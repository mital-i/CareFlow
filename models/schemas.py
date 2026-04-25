"""
Pydantic models matching MongoDB collection schemas.
All four parts import from here — do not change field names without notifying teammates.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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

class NotificationPrefs(BaseModel):
    sensitivity: NotificationSensitivity = NotificationSensitivity.MEDIUM
    preferred_channel: NotificationChannel = NotificationChannel.PUSH
    do_not_disturb_hours: Optional[List[int]] = None  # e.g. [22, 23, 0, 1, 2, 3, 4, 5, 6]
    emergency_contact: Optional[str] = None


class Patient(BaseModel):
    patient_id: str
    name: str
    age: int
    conditions: List[str] = []
    medications: List[str] = []
    baseline_hr: float
    baseline_spo2: float
    baseline_hrv: float
    notification_prefs: NotificationPrefs = Field(default_factory=NotificationPrefs)


# ── MongoDB: vitals_history collection ────────────────────────────────────────

class VitalsHistory(BaseModel):
    patient_id: str
    timestamp: datetime
    heart_rate: float
    spo2: float
    hrv: float
    device_id: str
    anomaly_flagged: bool = False


# ── MongoDB: risk_assessments collection ──────────────────────────────────────

class RiskAssessmentDoc(BaseModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    patient_id: str
    risk_score: float
    severity_level: SeverityLevel
    reasoning_context: str
    anomaly_ref: Optional[UUID] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ── MongoDB: action_logs collection ───────────────────────────────────────────

class ActionLog(BaseModel):
    action_id: UUID = Field(default_factory=uuid4)
    patient_id: str
    assessment_ref: UUID
    action_tier: ActionTier
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    provider_message: Optional[str] = None
