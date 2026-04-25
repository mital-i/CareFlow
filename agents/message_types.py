"""
Fetch.ai Chat Protocol message models.
Every inter-agent message must use one of these types — no raw HTTP calls.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from uagents import Model


class AnomalyEventMessage(Model):
    anomaly_id: str
    patient_id: str
    signal_type: str
    deviation_score: float
    heart_rate: float
    spo2: float
    hrv: float
    detected_at: str  # ISO 8601


class VitalsQueryMessage(Model):
    patient_id: str


class VitalsResponseMessage(Model):
    patient_id: str
    heart_rate: float
    spo2: float
    hrv: float
    timestamp: str
    device_id: str
    anomaly_flagged: bool = False


class DetectAnomalyRequestMessage(Model):
    patient_id: str
    heart_rate: float
    spo2: float
    hrv: float
    timestamp: str
    device_id: str


class DetectAnomalyResponseMessage(Model):
    patient_id: str
    anomaly_detected: bool
    deviation_score: float
    signal_type: Optional[str] = None
    anomaly_id: Optional[str] = None
    detected_at: Optional[str] = None


class RiskAssessmentMessage(Model):
    assessment_id: str
    patient_id: str
    risk_score: float
    severity_level: str  # LOW | MEDIUM | HIGH | CRITICAL
    reasoning_context: str
    anomaly_ref: str
    generated_at: str  # ISO 8601


class ActionDecisionMessage(Model):
    action_id: str
    patient_id: str
    action_tier: str  # LOG_ONLY | PATIENT_ALERT | PROVIDER_NOTIFY | ER_DISPATCH
    assessment_ref: str
    provider_message: Optional[str] = None
    executed_at: str  # ISO 8601


class PatientPreferencesMessage(Model):
    patient_id: str
    notification_sensitivity: str
    preferred_channel: str
    can_receive_alert: bool


class AvailabilitySlotMessage(Model):
    available: bool
    slot_time: str  # ISO 8601
    callback_type: str  # immediate | scheduled | oncall


class AcknowledgeAlertMessage(Model):
    alert_id: str
    acknowledged_at: str  # ISO 8601


class StatusOKMessage(Model):
    status: str = "ok"
