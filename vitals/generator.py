"""Synthetic vitals generator for the CareFlow edge-device demo."""
from __future__ import annotations

import math
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from models.vitals import VitalsPayload

DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", os.getenv("DEMO_PATIENT_ID", "patient-001"))
DEVICE_ID = os.getenv("DEVICE_ID", "careflow_watch_001")
ANOMALY_DURATION_SECONDS = 30
RECOVERY_SECONDS = 18


@dataclass
class PatientVitalsState:
    heart_rate: float = 74.0
    spo2: float = 98.0
    hrv: float = 55.0
    anomaly_until: float = 0.0
    recovery_started_at: float = 0.0


_states: dict[str, PatientVitalsState] = {}


def _state_for(patient_id: str) -> PatientVitalsState:
    if patient_id not in _states:
        _states[patient_id] = PatientVitalsState()
    return _states[patient_id]


def _organic_wave(now: float, period: float, amplitude: float) -> float:
    return amplitude * math.sin(2 * math.pi * now / period)


def _bounded_int(value: float, low: int, high: int) -> int:
    return int(round(min(high, max(low, value))))


def is_anomaly_active(patient_id: str) -> bool:
    return time.time() < _state_for(patient_id).anomaly_until


def trigger_anomaly(patient_id: str = DEFAULT_PATIENT_ID, duration_seconds: int = ANOMALY_DURATION_SECONDS) -> dict:
    if isinstance(patient_id, int):
        duration_seconds = patient_id
        patient_id = DEFAULT_PATIENT_ID

    state = _state_for(patient_id)
    state.anomaly_until = time.time() + duration_seconds
    state.recovery_started_at = 0.0
    return {
        "status": "triggered",
        "patient_id": patient_id,
        "message": f"Anomaly mode active for {duration_seconds} seconds",
    }


def _target_values(patient_id: str, now: float) -> tuple[float, float, float, float]:
    state = _state_for(patient_id)

    if now < state.anomaly_until:
        state.recovery_started_at = 0.0
        return (
            random.uniform(125, 155),
            random.uniform(91, 95),
            random.uniform(10, 24),
            1.0,
        )

    if state.anomaly_until > 0:
        if state.recovery_started_at == 0.0:
            state.recovery_started_at = now
        elapsed = now - state.recovery_started_at
        if elapsed < RECOVERY_SECONDS:
            recovery = elapsed / RECOVERY_SECONDS
            return (
                140 - (64 * recovery) + random.uniform(-2, 2),
                93 + (5 * recovery) + random.uniform(-0.3, 0.3),
                18 + (37 * recovery) + random.uniform(-2, 2),
                0.28,
            )
        state.anomaly_until = 0.0
        state.recovery_started_at = 0.0

    return (
        74 + _organic_wave(now, 31, 4) + random.uniform(-3, 3),
        98.5 + _organic_wave(now, 43, 0.5) + random.uniform(-0.4, 0.4),
        58 + _organic_wave(now, 37, 6) + random.uniform(-5, 5),
        0.35,
    )


def generate_next_vitals(patient_id: str) -> VitalsPayload:
    state = _state_for(patient_id)
    now = time.time()
    target_hr, target_spo2, target_hrv, smoothing = _target_values(patient_id, now)

    state.heart_rate += (target_hr - state.heart_rate) * smoothing
    state.spo2 += (target_spo2 - state.spo2) * smoothing
    state.hrv += (target_hrv - state.hrv) * smoothing

    return VitalsPayload(
        patient_id=patient_id,
        timestamp=datetime.now(timezone.utc),
        heart_rate=_bounded_int(state.heart_rate, 45, 170),
        spo2=_bounded_int(state.spo2, 85, 100),
        hrv=_bounded_int(state.hrv, 5, 90),
        device_id=DEVICE_ID,
    )


def generate_vitals(patient_id: str, device_id: str | None = None) -> VitalsPayload:
    payload = generate_next_vitals(patient_id)
    if device_id:
        payload.device_id = device_id
    return payload
