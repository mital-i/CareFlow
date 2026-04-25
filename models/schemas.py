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


class SafetyStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"


class SafetyReport(BaseModel):
    status: SafetyStatus
    is_hallucination: bool
    medical_alignment: bool
    concerns: Optional[str] = None


class RiskAssessment(BaseModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    patient_id: str
    risk_score: float
    severity_level: SeverityLevel
    reasoning_context: str
    doctor_note: str
    anomaly_ref: str
    safety_report: Optional[SafetyReport] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActionDecision(BaseModel):
    action_id: UUID = Field(default_factory=uuid4)
    patient_id: str
    action_tier: ActionTier
    provider_message: Optional[str] = None
    assessment_ref: str
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
