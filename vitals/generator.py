"""
Synthetic vitals generator — streams VitalsPayload at 1 Hz per patient.
Supports demo_trigger mode: injects an AFib-pattern anomaly for 30s.
"""
import asyncio
import math
import os
import random
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict

from dotenv import load_dotenv

load_dotenv()

from models.vitals import VitalsPayload

DEVICE_ID = os.getenv("ZETIC_DEVICE_ID", "careflow-demo-device-001")
ANOMALY_DURATION_SECONDS = int(os.getenv("ANOMALY_DURATION_SECONDS", "30"))

# Fallback per-patient normal ranges. MongoDB patient baselines win when present.
PATIENT_BASELINES: Dict[str, dict] = {
    "P001": {"hr": 72.0, "spo2": 97.5, "hrv": 55.0},
    "P002": {"hr": 78.0, "spo2": 98.0, "hrv": 48.0},
    "P003": {"hr": 65.0, "spo2": 97.0, "hrv": 65.0},
}

_baseline_cache: Dict[str, dict] = {}
_memory_triggers: Dict[str, datetime] = {}


def trigger_anomaly(patient_id: str, duration_seconds: int = ANOMALY_DURATION_SECONDS) -> dict:
    """Called by POST /trigger-anomaly to start an anomaly injection."""
    try:
        from db.db import set_demo_trigger

        return set_demo_trigger(patient_id, duration_seconds=duration_seconds)
    except Exception:
        triggered_until = datetime.now(timezone.utc).timestamp() + duration_seconds
        until_dt = datetime.fromtimestamp(triggered_until, tz=timezone.utc)
        _memory_triggers[patient_id] = until_dt
        return {
            "patient_id": patient_id,
            "triggered_until": until_dt,
            "duration_seconds": duration_seconds,
        }


def is_anomaly_triggered(patient_id: str) -> bool:
    try:
        from db.db import is_demo_trigger_active

        return is_demo_trigger_active(patient_id)
    except Exception:
        until = _memory_triggers.get(patient_id)
        if not until:
            return False
        active = until > datetime.now(timezone.utc)
        if not active:
            _memory_triggers.pop(patient_id, None)
        return active


def _gaussian(mean: float, std: float, low: float, high: float) -> float:
    return max(low, min(high, random.gauss(mean, std)))


def _circadian_offset(hour: int) -> float:
    """Small HR variation mimicking natural circadian rhythm."""
    return 4.0 * math.sin(math.pi * (hour - 6) / 12)


def _load_baseline(patient_id: str) -> dict:
    if patient_id in _baseline_cache:
        return _baseline_cache[patient_id]
    fallback = PATIENT_BASELINES.get(patient_id, {"hr": 75.0, "spo2": 97.0, "hrv": 50.0})
    try:
        from db.db import get_patient

        patient = get_patient(patient_id)
    except Exception:
        patient = None
    if patient:
        baseline = {
            "hr": float(patient.get("baseline_hr", fallback["hr"])),
            "spo2": float(patient.get("baseline_spo2", fallback["spo2"])),
            "hrv": float(patient.get("baseline_hrv", fallback["hrv"])),
        }
    else:
        baseline = fallback
    _baseline_cache[patient_id] = baseline
    return baseline


def generate_one(patient_id: str, tick: int = 0, in_anomaly: bool | None = None) -> VitalsPayload:
    baseline = _load_baseline(patient_id)
    now = datetime.now(timezone.utc)
    hour = now.hour
    anomaly_active = is_anomaly_triggered(patient_id) if in_anomaly is None else in_anomaly

    hr = _gaussian(
        baseline["hr"] + _circadian_offset(hour) + (32 if anomaly_active else 0),
        2.5 if not anomaly_active else 5.5,
        40 if anomaly_active else 60,
        160 if anomaly_active else 90,
    )
    spo2 = _gaussian(
        baseline["spo2"] - (2.5 if anomaly_active else 0),
        0.4,
        88 if anomaly_active else 97,
        100,
    )
    hrv = _gaussian(
        baseline["hrv"] - (35 if anomaly_active else 0),
        4.0 if not anomaly_active else 6.0,
        10 if anomaly_active else 40,
        120 if anomaly_active else 80,
    )

    return VitalsPayload(
        patient_id=patient_id,
        heart_rate=round(hr, 1),
        spo2=round(spo2, 1),
        hrv=round(hrv, 1),
        timestamp=now,
        device_id=f"{DEVICE_ID}-{patient_id.lower()}",
    )


async def stream_vitals(patient_id: str) -> AsyncGenerator[VitalsPayload, None]:
    """Yields one VitalsPayload per second indefinitely."""
    tick = 0
    while True:
        yield generate_one(patient_id, tick)
        tick += 1
        await asyncio.sleep(1.0)
