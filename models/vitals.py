from datetime import datetime
from pydantic import BaseModel, Field
from datetime import timezone


class VitalsPayload(BaseModel):
    """Live vitals reading emitted by the synthetic generator at 1 Hz."""
    patient_id: str
    heart_rate: float
    spo2: float
    hrv: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device_id: str
