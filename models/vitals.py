from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class VitalsPayload(BaseModel):
    """Live vitals reading emitted by the synthetic generator at 1 Hz."""
    patient_id: str
    heart_rate: float
    spo2: float
    hrv: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device_id: str

    @field_validator("timestamp")
    @classmethod
    def _timestamp_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
