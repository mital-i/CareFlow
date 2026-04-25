"""
Builds PatientHistory from MongoDB for use in the Gemini risk prompt.
Unit tests should mock the db calls so this module can be tested offline.
"""
import statistics
from typing import List

from db.db import get_patient, get_recent_vitals, get_recent_anomalies, get_recent_risk_scores
from models.patient import PatientHistory
from models.schemas import Patient, NotificationPrefs


def _doc_to_patient(doc: dict) -> Patient:
    prefs_raw = doc.get("notification_prefs", {})
    prefs = NotificationPrefs(**prefs_raw) if prefs_raw else NotificationPrefs()
    return Patient(
        patient_id=doc["patient_id"],
        name=doc["name"],
        age=doc["age"],
        conditions=doc.get("conditions", []),
        medications=doc.get("medications", []),
        baseline_hr=doc["baseline_hr"],
        baseline_spo2=doc["baseline_spo2"],
        baseline_hrv=doc["baseline_hrv"],
        notification_prefs=prefs,
    )


def get_risk_trend(patient_id: str) -> str:
    scores = get_recent_risk_scores(patient_id, limit=10)
    if len(scores) < 3:
        return "stable"
    recent = scores[:3]
    older = scores[3:6] if len(scores) >= 6 else scores[3:]
    if not older:
        return "stable"
    recent_mean = statistics.mean(recent)
    older_mean = statistics.mean(older)
    delta = recent_mean - older_mean
    if delta > 0.1:
        return "trending_up"
    if delta < -0.1:
        return "trending_down"
    return "stable"


def build_patient_history(patient_id: str) -> PatientHistory:
    patient_doc = get_patient(patient_id)
    if not patient_doc:
        raise ValueError(f"Patient {patient_id} not found in database")

    patient = _doc_to_patient(patient_doc)
    recent_vitals = get_recent_vitals(patient_id, limit=30)
    recent_anomalies = get_recent_anomalies(patient_id, limit=5)
    trend = get_risk_trend(patient_id)

    return PatientHistory(
        patient=patient,
        recent_vitals=recent_vitals,
        recent_anomalies=recent_anomalies,
        risk_trend=trend,
    )
