from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator
from .vitals import VitalsPayload


class AnomalyEvent(BaseModel):
    """Emitted by Agent 1 when ZETIC Melange detects an anomaly."""
    anomaly_id: UUID = Field(default_factory=uuid4)
    patient_id: str
    signal_type: str  # e.g. "hr_hrv_combined", "spo2_drop"
    deviation_score: float  # 0.0–1.0; threshold default 0.65
    vitals_snapshot: VitalsPayload
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("detected_at")
    @classmethod
    def _detected_at_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
