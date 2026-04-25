"""Fetch.ai Chat Protocol message models for CareFlow agents."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID

from uagents import Model  # type: ignore


class VitalsMessage(Model):
    patient_id: str
    heart_rate: float
    spo2: float
    hrv: float
    timestamp: str
    device_id: str


class AnomalyMessage(Model):
    anomaly_id: str
    patient_id: str
    signal_type: str
    deviation_score: float
    heart_rate: float
    spo2: float
    hrv: float
    detected_at: str


class RiskMessage(Model):
    assessment_id: str
    patient_id: str
    risk_score: float
    severity_level: str
    reasoning_context: str
    doctor_note: str
    anomaly_ref: str
    generated_at: str


class ActionMessage(Model):
    action_id: str
    patient_id: str
    action_tier: str
    provider_message: Optional[str]
    assessment_ref: str
    executed_at: str
