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

# Per-patient normal ranges
PATIENT_BASELINES: Dict[str, dict] = {
    "P001": {"hr": 72.0, "spo2": 97.5, "hrv": 55.0},
    "P002": {"hr": 78.0, "spo2": 98.0, "hrv": 48.0},
    "P003": {"hr": 65.0, "spo2": 96.5, "hrv": 65.0},
}

# Tracks which patients currently have an active anomaly injection
_anomaly_active: Dict[str, bool] = {}
_anomaly_ticks: Dict[str, int] = {}
ANOMALY_DURATION_TICKS = 30


def trigger_anomaly(patient_id: str) -> None:
    """Called by POST /trigger-anomaly to start an anomaly injection."""
    _anomaly_active[patient_id] = True
    _anomaly_ticks[patient_id] = ANOMALY_DURATION_TICKS


def _gaussian(mean: float, std: float, low: float, high: float) -> float:
    return max(low, min(high, random.gauss(mean, std)))


def _circadian_offset(hour: int) -> float:
    """Small HR variation mimicking natural circadian rhythm."""
    return 4.0 * math.sin(math.pi * (hour - 6) / 12)


def generate_one(patient_id: str, tick: int) -> VitalsPayload:
    baseline = PATIENT_BASELINES.get(patient_id, {"hr": 75.0, "spo2": 97.0, "hrv": 50.0})
    hour = datetime.now(timezone.utc).hour

    in_anomaly = _anomaly_active.get(patient_id, False)
    if in_anomaly:
        remaining = _anomaly_ticks.get(patient_id, 0) - 1
        _anomaly_ticks[patient_id] = remaining
        if remaining <= 0:
            _anomaly_active[patient_id] = False

    hr = _gaussian(
        baseline["hr"] + _circadian_offset(hour) + (28 if in_anomaly else 0),
        2.5, 40, 160,
    )
    spo2 = _gaussian(
        baseline["spo2"] - (2.5 if in_anomaly else 0),
        0.4, 88, 100,
    )
    hrv = _gaussian(
        baseline["hrv"] - (22 if in_anomaly else 0),
        4.0, 10, 120,
    )

    return VitalsPayload(
        patient_id=patient_id,
        heart_rate=round(hr, 1),
        spo2=round(spo2, 1),
        hrv=round(hrv, 1),
        timestamp=datetime.now(timezone.utc),
        device_id=DEVICE_ID,
    )


async def stream_vitals(patient_id: str) -> AsyncGenerator[VitalsPayload, None]:
    """Yields one VitalsPayload per second indefinitely."""
    tick = 0
    while True:
        yield generate_one(patient_id, tick)
        tick += 1
        await asyncio.sleep(1.0)
