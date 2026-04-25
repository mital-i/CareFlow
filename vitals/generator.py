"""Synthetic vitals generator — streams VitalsPayload at ~1 Hz.

Normal ranges:  HR 60-90 BPM,  SpO2 97-100%,  HRV 40-80 ms
Anomaly mode:   HR 120-160 BPM, SpO2 93-96%,   HRV 12-25 ms  (simulates AFib onset)
"""
from __future__ import annotations
import asyncio
import math
import os
import random
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from models.schemas import VitalsPayload

_anomaly_until: float = 0.0  # epoch seconds


def trigger_anomaly(duration_seconds: int = 30) -> None:
    global _anomaly_until
    _anomaly_until = time.time() + duration_seconds


def _is_anomaly() -> bool:
    return time.time() < _anomaly_until


def _circadian_offset(t: float) -> float:
    """Slow sinusoidal rhythm variation — looks organic on a chart."""
    return 4 * math.sin(2 * math.pi * t / 86400)


def generate_vitals(patient_id: str, device_id: str = "careflow-demo-device-001") -> VitalsPayload:
    t = time.time()
    circadian = _circadian_offset(t)

    if _is_anomaly():
        hr = random.gauss(140, 8) + circadian
        spo2 = random.gauss(94.5, 0.8)
        hrv = random.gauss(18, 4)
    else:
        hr = random.gauss(72 + circadian, 3)
        spo2 = random.gauss(98.5, 0.4)
        hrv = random.gauss(58, 7)

    return VitalsPayload(
        patient_id=patient_id,
        heart_rate=round(max(40.0, hr), 1),
        spo2=round(min(100.0, max(85.0, spo2)), 1),
        hrv=round(max(5.0, hrv), 1),
        timestamp=datetime.now(timezone.utc),
        device_id=device_id,
    )


async def stream_vitals(
    patient_id: str,
    callback: Callable[[VitalsPayload], None],
    interval: float = 1.0,
) -> None:
    """Indefinitely generate vitals and call callback at each tick."""
    while True:
        payload = generate_vitals(patient_id)
        callback(payload)
        await asyncio.sleep(interval)
