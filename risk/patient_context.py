"""Formats patient context for inclusion in risk prompts."""
from models.patient import PatientHistory


def format_patient_context(history: PatientHistory) -> str:
    p = history.patient
    lines = [
        f"Name: {p.name}, Age: {p.age}",
        f"Conditions: {', '.join(p.conditions) or 'None'}",
        f"Medications: {', '.join(p.medications) or 'None'}",
        f"Baseline — HR: {p.baseline_hr} bpm, SpO2: {p.baseline_spo2}%, HRV: {p.baseline_hrv}ms",
        f"Recent anomaly events: {len(history.recent_anomalies)}",
        f"Risk trend: {history.risk_trend}",
    ]
    return "\n".join(lines)
