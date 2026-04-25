"""Compatibility wrappers for the configured CareFlow vitals source."""
from __future__ import annotations

from models.vitals import VitalsPayload
from vitals.sources import (
    ANOMALY_DURATION_SECONDS,
    DEFAULT_PATIENT_ID,
    DEVICE_ID,
    get_vitals_source,
)


def is_anomaly_active(patient_id: str) -> bool:
    return get_vitals_source().is_anomaly_active(patient_id)


def trigger_anomaly(
    patient_id: str = DEFAULT_PATIENT_ID,
    duration_seconds: int = ANOMALY_DURATION_SECONDS,
) -> dict:
    return get_vitals_source().trigger_anomaly(patient_id, duration_seconds)


def generate_next_vitals(patient_id: str) -> VitalsPayload:
    return get_vitals_source().next_vitals(patient_id)


def generate_vitals(patient_id: str, device_id: str | None = None) -> VitalsPayload:
    payload = generate_next_vitals(patient_id)
    if device_id:
        payload.device_id = device_id
    return payload
