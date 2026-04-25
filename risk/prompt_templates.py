"""Gemini prompt templates for clinical risk classification."""

RISK_CLASSIFICATION_TEMPLATE = """You are a clinical risk assessment AI assistant.
Analyze the following patient data and assign a risk assessment.

Patient context:
- Age: {age}
- Conditions: {conditions}
- Medications: {medications}
- Baseline vitals: HR={baseline_hr} bpm, SpO2={baseline_spo2}%, HRV={baseline_hrv}ms

Current anomaly:
- Signal type: {signal_type}
- Deviation score: {deviation_score}
- Current readings: HR={current_hr} bpm, SpO2={current_spo2}%, HRV={current_hrv}ms
- Detected at: {detected_at}

Recent history (last 30 events):
{history_summary}

Risk trend: {risk_trend}

Assign:
1. risk_score: float between 0.0 (no risk) and 1.0 (critical risk)
2. severity_level: one of LOW, MEDIUM, HIGH, CRITICAL
3. reasoning_context: 2-3 sentence clinical reasoning

Respond in valid JSON only, with exactly these keys:
{{"risk_score": <float>, "severity_level": "<string>", "reasoning_context": "<string>"}}"""


def build_risk_prompt(patient_history, anomaly) -> str:
    patient = patient_history.patient
    vitals = anomaly.vitals_snapshot

    history_lines = []
    for v in patient_history.recent_vitals[:10]:
        ts = v["timestamp"].strftime("%Y-%m-%d %H:%M") if hasattr(v["timestamp"], "strftime") else str(v["timestamp"])
        flagged = " [ANOMALY]" if v.get("anomaly_flagged") else ""
        history_lines.append(f"  {ts}: HR={v['heart_rate']}, SpO2={v['spo2']}, HRV={v['hrv']}{flagged}")

    history_summary = "\n".join(history_lines) if history_lines else "No recent history available."

    return RISK_CLASSIFICATION_TEMPLATE.format(
        age=patient.age,
        conditions=", ".join(patient.conditions) or "None documented",
        medications=", ".join(patient.medications) or "None documented",
        baseline_hr=patient.baseline_hr,
        baseline_spo2=patient.baseline_spo2,
        baseline_hrv=patient.baseline_hrv,
        signal_type=anomaly.signal_type,
        deviation_score=anomaly.deviation_score,
        current_hr=vitals.heart_rate,
        current_spo2=vitals.spo2,
        current_hrv=vitals.hrv,
        detected_at=anomaly.detected_at.isoformat(),
        history_summary=history_summary,
        risk_trend=patient_history.risk_trend,
    )
