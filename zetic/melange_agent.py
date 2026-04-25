"""
ZETIC Melange on-device anomaly detector.
Buffers the last 10s of vitals, runs model inference via the Melange SDK,
and emits an AnomalyEvent when the deviation score exceeds the threshold.

TODO: Replace the stub inference with the real ZETIC Melange SDK calls
      once the SDK is installed (follow https://zetic.ai/la-hacks starter pack).
"""
import os
import statistics
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Optional

from dotenv import load_dotenv

load_dotenv()

from models.vitals import VitalsPayload
from models.anomaly import AnomalyEvent

ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "0.65"))
BUFFER_SIZE = 10  # seconds


class MelangeAgent:
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self._buffer: Deque[VitalsPayload] = deque(maxlen=BUFFER_SIZE)
        self._model = self._load_model()

    def _load_model(self):
        """
        TODO: Load the quantized LSTM/CNN model via ZETIC Melange SDK.
        Example (replace with real SDK calls):
            from zetic_mlange import MelangeModel
            return MelangeModel.load("careflow_anomaly_v1", backend="npu")
        """
        return None  # stub

    def push_vitals(self, payload: VitalsPayload) -> Optional[AnomalyEvent]:
        """Feed one vitals reading; returns AnomalyEvent if anomaly detected."""
        self._buffer.append(payload)
        if len(self._buffer) < BUFFER_SIZE:
            return None

        score = self._run_inference()
        if score >= ANOMALY_THRESHOLD:
            return AnomalyEvent(
                patient_id=self.patient_id,
                signal_type=self._classify_signal(),
                deviation_score=round(score, 4),
                vitals_snapshot=payload,
                detected_at=datetime.now(timezone.utc),
            )
        return None

    def _run_inference(self) -> float:
        """
        TODO: Replace stub with real Melange SDK inference.
        The real call should look like:
            features = self._build_feature_vector()
            result = self._model.infer(features)
            return result["deviation_score"]
        """
        hrs = [v.heart_rate for v in self._buffer]
        hrvs = [v.hrv for v in self._buffer]
        spo2s = [v.spo2 for v in self._buffer]

        hr_mean = statistics.mean(hrs)
        hrv_mean = statistics.mean(hrvs)
        spo2_mean = statistics.mean(spo2s)

        # Heuristic fallback (replace with real model output)
        score = 0.0
        if hr_mean > 100:
            score += 0.3
        if hrv_mean < 25:
            score += 0.3
        if spo2_mean < 94:
            score += 0.25
        hr_std = statistics.stdev(hrs) if len(hrs) > 1 else 0
        if hr_std > 10:
            score += 0.15

        return min(score, 1.0)

    def _classify_signal(self) -> str:
        hrs = [v.heart_rate for v in self._buffer]
        hrvs = [v.hrv for v in self._buffer]
        if statistics.mean(hrs) > 100 and statistics.mean(hrvs) < 25:
            return "hr_hrv_combined"
        if statistics.mean(hrs) > 100:
            return "elevated_hr"
        if statistics.mean(hrvs) < 25:
            return "low_hrv"
        return "spo2_drop"
