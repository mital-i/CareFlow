"""ZETIC Melange on-device anomaly detector.

Buffers the last 10s of vitals. On each tick, runs inference and emits
AnomalyEvent when deviation_score exceeds ANOMALY_THRESHOLD.

If the ZETIC SDK is unavailable (dev/CI), falls back to a heuristic scorer
that produces equivalent outputs for testing the rest of the pipeline.
"""
from __future__ import annotations
import os
import time
from collections import deque
from typing import Callable, Optional
from uuid import uuid4

from models.schemas import AnomalyEvent, VitalsPayload

ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "0.65"))
BUFFER_SIZE = 10  # seconds of vitals to buffer


class MelangeDetector:
    def __init__(self) -> None:
        self._buffer: deque[VitalsPayload] = deque(maxlen=BUFFER_SIZE)
        self._zetic_available = self._try_init_zetic()

    def _try_init_zetic(self) -> bool:
        try:
            from zetic_mlange import ZeticMLange  # type: ignore
            model_key = os.environ["ZETIC_MODEL_KEY"]
            personal_key = os.environ["ZETIC_PERSONAL_KEY"]
            backend = os.getenv("ZETIC_BACKEND", "heuristic")
            self._model = ZeticMLange(model_key, personal_key, backend=backend)
            print("[ZETIC] Melange SDK initialised successfully")
            return True
        except Exception as exc:
            print(f"[ZETIC] SDK not available ({exc}) — using heuristic fallback")
            return False

    def _heuristic_score(self) -> float:
        """Simple z-score based deviation across HR, SpO2, HRV."""
        if len(self._buffer) < 3:
            return 0.0
        hrs = [v.heart_rate for v in self._buffer]
        spo2s = [v.spo2 for v in self._buffer]
        hrvs = [v.hrv for v in self._buffer]

        def z(vals: list[float]) -> float:
            mean = sum(vals) / len(vals)
            std = (sum((x - mean) ** 2 for x in vals) / len(vals)) ** 0.5
            return abs(vals[-1] - mean) / (std + 1e-6)

        # Normalise to [0, 1] — a z-score of 3+ maps to ~1.0
        score = min(1.0, (z(hrs) * 0.5 + z(spo2s) * 0.3 + z(hrvs) * 0.2) / 3.0)
        return round(score, 4)

    def _zetic_score(self) -> float:
        if len(self._buffer) < BUFFER_SIZE:
            return 0.0
        sequence = [
            [v.heart_rate, v.spo2, v.hrv]
            for v in self._buffer
        ]
        result = self._model.infer({"input": sequence})
        return float(result.get("deviation_score", 0.0))

    def ingest(self, payload: VitalsPayload) -> Optional[AnomalyEvent]:
        self._buffer.append(payload)
        score = self._zetic_score() if self._zetic_available else self._heuristic_score()

        if score >= ANOMALY_THRESHOLD:
            return AnomalyEvent(
                patient_id=payload.patient_id,
                deviation_score=score,
                vitals_snapshot=payload,
            )
        return None


_detector = MelangeDetector()


def process_vitals(payload: VitalsPayload) -> Optional[AnomalyEvent]:
    """Public interface used by Agent 1."""
    return _detector.ingest(payload)
