from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from models.vitals import AnomalyEvent, VitalsPayload


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionTier(str, Enum):
    LOG_ONLY = "LOG_ONLY"
    PATIENT_ALERT = "PATIENT_ALERT"
    PROVIDER_NOTIFY = "PROVIDER_NOTIFY"
    ER_DISPATCH = "ER_DISPATCH"


class RiskAssessment(BaseModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    patient_id: str
    risk_score: float
    severity_level: SeverityLevel
    reasoning_context: str
    doctor_note: str
    anomaly_ref: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActionDecision(BaseModel):
    action_id: UUID = Field(default_factory=uuid4)
    patient_id: str
    action_tier: ActionTier
    provider_message: Optional[str] = None
    assessment_ref: str
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
