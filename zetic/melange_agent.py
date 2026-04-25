"""ZETIC Melange-compatible local anomaly detector.

The demo contract is intentionally small: raw vitals are processed locally,
and only compact AnomalyEvent objects are saved/sent upstream.
"""
from __future__ import annotations

import os
from collections import defaultdict, deque
from typing import Deque, Optional

from db.db import save_anomaly
from models.vitals import AnomalyEvent, VitalsPayload


class ZeticAnomalyDetector:
    buffer_size = 10
    threshold = float(os.getenv("ANOMALY_THRESHOLD", "0.65"))

    def __init__(self) -> None:
        self._buffers: dict[str, Deque[VitalsPayload]] = defaultdict(
            lambda: deque(maxlen=self.buffer_size)
        )
        self._zetic_model = None
        self._zetic_available = self._try_init_zetic()

    def _try_init_zetic(self) -> bool:
        if os.getenv("ZETIC_MODE", "mock").lower() == "mock":
            return False

        try:
            # TODO: Replace this import and constructor with the confirmed
            # ZETIC Melange SDK package from the LA Hacks starter pack.
            from zetic_melange import ZeticMelange  # type: ignore

            self._zetic_model = ZeticMelange(
                model_key=os.environ["ZETIC_MODEL_KEY"],
                personal_key=os.environ["ZETIC_PERSONAL_KEY"],
            )
            print("[ZETIC] Melange SDK initialized")
            return True
        except Exception as exc:
            print(f"[ZETIC] SDK unavailable ({exc}); using deterministic mock scorer")
            return False

    def add_vitals(self, payload: VitalsPayload) -> Optional[AnomalyEvent]:
        recent_buffer = self._buffers[payload.patient_id]
        score = self.calculate_deviation_score(payload, recent_buffer)
        recent_buffer.append(payload)

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

    def calculate_deviation_score(
        self,
        payload: VitalsPayload,
        recent_buffer: Deque[VitalsPayload],
    ) -> float:
        if self._zetic_available:
            # TODO: Replace this adapter with real ZETIC Melange on-device
            # inference once the SDK/model artifact is available.
            return self._calculate_zetic_score(payload, recent_buffer)

        score = 0.0
        if payload.heart_rate > 120:
            score += 0.45
        if payload.spo2 < 95:
            score += 0.25
        if payload.hrv < 30:
            score += 0.25
        if recent_buffer:
            avg_hr = sum(v.heart_rate for v in recent_buffer) / len(recent_buffer)
            if payload.heart_rate - avg_hr > 25:
                score += 0.15
        return round(min(score, 1.0), 4)

    def _calculate_zetic_score(
        self,
        payload: VitalsPayload,
        recent_buffer: Deque[VitalsPayload],
    ) -> float:
        sequence = [
            [v.heart_rate, v.spo2, v.hrv]
            for v in [*recent_buffer, payload][-self.buffer_size :]
        ]
        # TODO: Confirm exact SDK input/output names. The fallback scorer keeps
        # the same public interface for the rest of the demo pipeline.
        result = self._zetic_model.infer({"vitals": sequence})
        return float(result.get("deviation_score", 0.0))


_detector = ZeticAnomalyDetector()


def process_vitals(payload: VitalsPayload) -> Optional[AnomalyEvent]:
    return _detector.add_vitals(payload)
