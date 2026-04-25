"""Heuristic anomaly detector — scores vitals against clinical thresholds."""
from __future__ import annotations
import os
from collections import defaultdict, deque
from typing import Deque, Optional

from db.db import save_anomaly
from models.vitals import AnomalyEvent, VitalsPayload


class AnomalyDetector:
    buffer_size = 10
    threshold = float(os.getenv("ANOMALY_THRESHOLD", "0.65"))

    def __init__(self) -> None:
        self._buffers: dict[str, Deque[VitalsPayload]] = defaultdict(
            lambda: deque(maxlen=self.buffer_size)
        )

    def add_vitals(self, payload: VitalsPayload) -> Optional[AnomalyEvent]:
        buf = self._buffers[payload.patient_id]
        score = self._score(payload, buf)
        buf.append(payload)

        if score < self.threshold:
            return None

        payload.anomaly_flagged = True
        event = AnomalyEvent(
            patient_id=payload.patient_id,
            signal_type="HR+SpO2+HRV",
            deviation_score=score,
            vitals_snapshot=payload,
        )

        try:
            save_anomaly(event)
        except Exception as exc:
            print(f"[Mongo] anomaly save skipped: {exc}")

        return event

    def _score(self, payload: VitalsPayload, buf: Deque[VitalsPayload]) -> float:
        score = 0.0
        if payload.heart_rate > 120:
            score += 0.45
        if payload.spo2 < 95:
            score += 0.25
        if payload.hrv < 30:
            score += 0.25
        if buf:
            avg_hr = sum(v.heart_rate for v in buf) / len(buf)
            if payload.heart_rate - avg_hr > 25:
                score += 0.15
        return round(min(score, 1.0), 4)


_detector = AnomalyDetector()


def process_vitals(payload: VitalsPayload) -> Optional[AnomalyEvent]:
    return _detector.add_vitals(payload)
