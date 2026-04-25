from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VitalsPayload(BaseModel):
    patient_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    heart_rate: int
    spo2: int
    hrv: int
    device_id: str
    anomaly_flagged: bool = False


class AnomalyEvent(BaseModel):
    anomaly_id: str = Field(default_factory=lambda: str(uuid4()))
    patient_id: str
    signal_type: str
    deviation_score: float
    vitals_snapshot: VitalsPayload
    detected_at: datetime = Field(default_factory=utc_now)
    source: str = "zetic_on_device"
