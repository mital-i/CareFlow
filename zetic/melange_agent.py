"""
ZETIC Melange on-device anomaly detector.
Buffers the last 10s of vitals, runs model inference via the Melange SDK,
and emits an AnomalyEvent when the deviation score exceeds the threshold.
"""
import os
import statistics
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional, Protocol

from dotenv import load_dotenv

load_dotenv()

from models.vitals import VitalsPayload
from models.anomaly import AnomalyEvent

ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "0.65"))
BUFFER_SIZE = 10  # seconds
COOLDOWN_SECONDS = int(os.getenv("ANOMALY_COOLDOWN_SECONDS", "20"))

FALLBACK_BASELINES: Dict[str, dict] = {
    "P001": {"hr": 72.0, "spo2": 97.5, "hrv": 55.0},
    "P002": {"hr": 78.0, "spo2": 98.0, "hrv": 48.0},
    "P003": {"hr": 65.0, "spo2": 97.0, "hrv": 65.0},
}


class InferenceBackend(Protocol):
    name: str

    def infer(self, samples: List[VitalsPayload], baseline: dict) -> float:
        ...


def _load_patient_baseline(patient_id: str) -> dict:
    fallback = FALLBACK_BASELINES.get(patient_id, {"hr": 75.0, "spo2": 97.0, "hrv": 50.0})
    try:
        from db.db import get_patient

        patient = get_patient(patient_id)
    except Exception:
        patient = None
    if not patient:
        return fallback
    return {
        "hr": float(patient.get("baseline_hr", fallback["hr"])),
        "spo2": float(patient.get("baseline_spo2", fallback["spo2"])),
        "hrv": float(patient.get("baseline_hrv", fallback["hrv"])),
    }


def build_feature_matrix(samples: List[VitalsPayload], baseline: dict) -> List[List[float]]:
    """Normalize 10 seconds of HR, SpO2, HRV into the model input shape [10, 3]."""
    return [
        [
            (sample.heart_rate - baseline["hr"]) / 40.0,
            (sample.spo2 - baseline["spo2"]) / 10.0,
            (sample.hrv - baseline["hrv"]) / 40.0,
        ]
        for sample in samples
    ]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class HeuristicBackend:
    """Local fallback mirroring the anomaly model contract for dev and CI."""

    name = "heuristic"

    def infer(self, samples: List[VitalsPayload], baseline: dict) -> float:
        hrs = [v.heart_rate for v in samples]
        hrvs = [v.hrv for v in samples]
        spo2s = [v.spo2 for v in samples]

        hr_mean = statistics.mean(hrs)
        hrv_mean = statistics.mean(hrvs)
        spo2_mean = statistics.mean(spo2s)
        hr_std = statistics.stdev(hrs) if len(hrs) > 1 else 0.0

        hr_score = _clamp01((hr_mean - (baseline["hr"] + 18.0)) / 35.0)
        hrv_score = _clamp01((baseline["hrv"] - hrv_mean) / 35.0)
        spo2_score = _clamp01((baseline["spo2"] - spo2_mean) / 5.0)
        instability_score = _clamp01(hr_std / 15.0)

        return _clamp01(
            0.45 * hr_score
            + 0.40 * hrv_score
            + 0.15 * spo2_score
            + 0.10 * instability_score
        )


class MelangeBridgeBackend:
    """Calls a local mobile bridge that runs the compiled ZETIC Melange model."""

    name = "melange_bridge"

    def __init__(self, bridge_url: Optional[str] = None):
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError(
                "ZETIC_BACKEND=melange_bridge requires httpx. Install requirements with "
                "`python3 -m pip install -r requirements.txt`."
            ) from exc
        self.bridge_url = bridge_url or os.getenv("ZETIC_BRIDGE_URL", "http://localhost:8765/infer")
        self.model_key = os.getenv("ZETIC_MODEL_KEY", "")
        self.personal_key = os.getenv("ZETIC_PERSONAL_KEY", "")
        self._client = httpx.Client(timeout=float(os.getenv("ZETIC_BRIDGE_TIMEOUT_SECONDS", "2.0")))

    def infer(self, samples: List[VitalsPayload], baseline: dict) -> float:
        payload = {
            "model_key": self.model_key,
            "personal_key": self.personal_key,
            "input_shape": [len(samples), 3],
            "inputs": build_feature_matrix(samples, baseline),
        }
        response = self._client.post(self.bridge_url, json=payload)
        response.raise_for_status()
        result = response.json()
        return _clamp01(float(result.get("deviation_score", result.get("score", 0.0))))


def make_backend(name: Optional[str] = None) -> InferenceBackend:
    backend_name = (name or os.getenv("ZETIC_BACKEND", "heuristic")).strip().lower()
    if backend_name == "melange_bridge":
        return MelangeBridgeBackend()
    return HeuristicBackend()


class MelangeAgent:
    def __init__(
        self,
        patient_id: str,
        threshold: float = ANOMALY_THRESHOLD,
        backend: Optional[InferenceBackend] = None,
        cooldown_seconds: int = COOLDOWN_SECONDS,
    ):
        self.patient_id = patient_id
        self.threshold = threshold
        self.cooldown_seconds = cooldown_seconds
        self._buffer: Deque[VitalsPayload] = deque(maxlen=BUFFER_SIZE)
        self._baseline = _load_patient_baseline(patient_id)
        self._backend = backend or make_backend()
        self._last_anomaly_at: Optional[datetime] = None
        self.latest_score: Optional[float] = None

    def push_vitals(self, payload: VitalsPayload) -> Optional[AnomalyEvent]:
        """Feed one vitals reading; returns AnomalyEvent if anomaly detected."""
        self._buffer.append(payload)
        if len(self._buffer) < BUFFER_SIZE:
            return None

        score = self._run_inference()
        if score >= self.threshold and not self._in_cooldown():
            self._last_anomaly_at = datetime.now(timezone.utc)
            return AnomalyEvent(
                patient_id=self.patient_id,
                signal_type=self._classify_signal(),
                deviation_score=round(score, 4),
                vitals_snapshot=payload,
                detected_at=datetime.now(timezone.utc),
            )
        return None

    def _run_inference(self) -> float:
        samples = list(self._buffer)
        self.latest_score = self._backend.infer(samples, self._baseline)
        return self.latest_score

    def _in_cooldown(self) -> bool:
        if not self._last_anomaly_at:
            return False
        elapsed = (datetime.now(timezone.utc) - self._last_anomaly_at).total_seconds()
        return elapsed < self.cooldown_seconds

    def _classify_signal(self) -> str:
        hrs = [v.heart_rate for v in self._buffer]
        hrvs = [v.hrv for v in self._buffer]
        spo2s = [v.spo2 for v in self._buffer]
        if statistics.mean(hrs) > self._baseline["hr"] + 20 and statistics.mean(hrvs) < self._baseline["hrv"] - 20:
            return "hr_hrv_combined"
        if statistics.mean(hrs) > self._baseline["hr"] + 20:
            return "elevated_hr"
        if statistics.mean(hrvs) < self._baseline["hrv"] - 20:
            return "low_hrv"
        if statistics.mean(spo2s) < self._baseline["spo2"] - 2:
            return "spo2_drop"
        return "spo2_drop"
