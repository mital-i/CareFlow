"""
Pydantic models matching MongoDB collection schemas.
All four parts import from here — do not change field names without notifying teammates.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class CareFlowModel(BaseModel):
    """Base model with JSON-safe UUID/datetime serialization."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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


class NotificationChannel(str, Enum):
    PUSH = "push"
    VOICE = "voice"
    SMS = "sms"


class NotificationSensitivity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ── MongoDB: patients collection ──────────────────────────────────────────────

class NotificationPrefs(CareFlowModel):
    sensitivity: NotificationSensitivity = NotificationSensitivity.MEDIUM
    preferred_channel: NotificationChannel = NotificationChannel.PUSH
    do_not_disturb_hours: Optional[List[int]] = None  # e.g. [22, 23, 0, 1, 2, 3, 4, 5, 6]
    emergency_contact: Optional[str] = None


class Patient(CareFlowModel):
    patient_id: str
    name: str
    age: int
    conditions: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    baseline_hr: float
    baseline_spo2: float
    baseline_hrv: float
    notification_prefs: NotificationPrefs = Field(default_factory=NotificationPrefs)


# ── MongoDB: vitals_history collection ────────────────────────────────────────

class VitalsHistory(CareFlowModel):
    patient_id: str
    timestamp: datetime
    heart_rate: float
    spo2: float
    hrv: float
    device_id: str
    anomaly_flagged: bool = False

    @field_validator("timestamp")
    @classmethod
    def _timestamp_aware(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value)


# ── MongoDB: risk_assessments collection ──────────────────────────────────────

class RiskAssessmentDoc(CareFlowModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    patient_id: str
    risk_score: float
    severity_level: SeverityLevel
    reasoning_context: str
    anomaly_ref: Optional[UUID] = None
    generated_at: datetime = Field(default_factory=utc_now)

    @field_validator("generated_at")
    @classmethod
    def _generated_at_aware(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value)


# ── MongoDB: action_logs collection ───────────────────────────────────────────

class ActionLog(CareFlowModel):
    action_id: UUID = Field(default_factory=uuid4)
    patient_id: str
    assessment_ref: UUID
    action_tier: ActionTier
    executed_at: datetime = Field(default_factory=utc_now)
    provider_message: Optional[str] = None

    @field_validator("executed_at")
    @classmethod
    def _executed_at_aware(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value)
