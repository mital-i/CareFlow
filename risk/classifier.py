"""
Vertex AI Gemini risk classifier.
Accepts AnomalyEvent + PatientHistory, calls Gemini via Vertex AI,
returns a RiskAssessmentDoc.
"""
import json
import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from models.anomaly import AnomalyEvent
from models.patient import PatientHistory
from models.schemas import RiskAssessmentDoc, SeverityLevel
from risk.prompt_templates import build_risk_prompt

_vertex_client = None


def _get_vertex_client():
    global _vertex_client
    if _vertex_client is None:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        vertexai.init(
            project=os.environ["GCP_PROJECT_ID"],
            location=os.getenv("GCP_REGION", "us-central1"),
        )
        _vertex_client = GenerativeModel(os.getenv("VERTEX_AI_MODEL", "gemini-pro"))
    return _vertex_client


def _fallback_assessment(anomaly: AnomalyEvent, patient_history: PatientHistory) -> dict:
    """Rule-based fallback when Vertex AI is unavailable."""
    hr = anomaly.vitals_snapshot.heart_rate
    hrv = anomaly.vitals_snapshot.hrv
    spo2 = anomaly.vitals_snapshot.spo2

    if hr > 120 and hrv < 20:
        score, severity = 0.85, "HIGH"
        reason = f"Elevated HR ({hr:.0f} bpm) with critically low HRV ({hrv:.0f}ms) indicates possible arrhythmia event."
    elif spo2 < 92:
        score, severity = 0.80, "HIGH"
        reason = f"SpO2 critically low at {spo2:.1f}%. Immediate intervention may be required."
    elif hr > 100 or hrv < 30:
        score, severity = 0.55, "MEDIUM"
        reason = f"Elevated heart rate ({hr:.0f} bpm) or reduced HRV warrants patient monitoring."
    else:
        score, severity = 0.25, "LOW"
        reason = f"Vitals deviation detected but within manageable range. Continued monitoring recommended."

    return {"risk_score": score, "severity_level": severity, "reasoning_context": reason}


def classify_risk(anomaly: AnomalyEvent, patient_history: PatientHistory) -> RiskAssessmentDoc:
    prompt = build_risk_prompt(patient_history, anomaly)
    result = None
    max_retries = 3
    backoff = 1.0

    for attempt in range(max_retries):
        try:
            model = _get_vertex_client()
            response = model.generate_content(prompt)
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw)
            break
        except Exception as exc:
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
            else:
                print(f"[WARN] Vertex AI failed after {max_retries} attempts: {exc}. Using fallback.")
                result = _fallback_assessment(anomaly, patient_history)

    risk_score = float(result.get("risk_score", 0.5))
    severity_raw = result.get("severity_level", "MEDIUM").upper()
    try:
        severity = SeverityLevel(severity_raw)
    except ValueError:
        severity = SeverityLevel.MEDIUM

    return RiskAssessmentDoc(
        patient_id=anomaly.patient_id,
        risk_score=round(risk_score, 4),
        severity_level=severity,
        reasoning_context=result.get("reasoning_context", ""),
        anomaly_ref=anomaly.anomaly_id,
        generated_at=datetime.now(timezone.utc),
    )
