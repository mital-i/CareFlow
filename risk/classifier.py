"""Gemini risk classifier — converts an AnomalyEvent into a RiskAssessment.

Uses Vertex AI (Gemini) with a single structured prompt. Falls back to a
rule-based assessment when Vertex AI is unavailable (dev/offline mode).
"""
from __future__ import annotations
import json
import os
from typing import Optional

from models.schemas import AnomalyEvent, RiskAssessment, SeverityLevel

_PROMPT_TEMPLATE = """You are a clinical AI assistant. Analyze the following patient vital signs anomaly and provide a structured risk assessment.

Patient vitals anomaly:
- Heart Rate: {heart_rate} BPM (normal: 60-90)
- SpO2: {spo2}% (normal: 97-100%)
- HRV: {hrv} ms (normal: 40-80 ms)
- Deviation Score: {deviation_score} (threshold: 0.65)
- Signal Type: {signal_type}

Respond ONLY with a valid JSON object in this exact format:
{{
  "risk_score": <float 0.0-1.0>,
  "severity_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "reasoning_context": "<2-3 sentence clinical explanation of what the vitals suggest>",
  "doctor_note": "<1 sentence recommended immediate action for the care provider>"
}}

Rules:
- risk_score < 0.4 → LOW, 0.4-0.6 → MEDIUM, 0.6-0.8 → HIGH, > 0.8 → CRITICAL
- Be specific about the likely cardiac event or condition suggested by these readings
- doctor_note must be actionable and concise
"""

_FALLBACK_RULES = [
    (lambda hr, spo2, hrv: hr > 140 or spo2 < 93 or hrv < 15, "CRITICAL", 0.92,
     "Severe tachycardia with suppressed HRV and low SpO2 — pattern consistent with acute AFib episode onset.",
     "Immediate physician review required; consider emergency cardiology consult."),
    (lambda hr, spo2, hrv: hr > 120 or spo2 < 95 or hrv < 25, "HIGH", 0.75,
     "Elevated heart rate with reduced HRV indicates significant cardiac stress; possible arrhythmia.",
     "Notify attending physician within 15 minutes and increase monitoring frequency."),
    (lambda hr, spo2, hrv: hr > 100 or spo2 < 97 or hrv < 35, "MEDIUM", 0.50,
     "Mildly elevated heart rate with decreased HRV — may indicate exertion, stress, or early warning sign.",
     "Alert patient to rest; schedule follow-up vitals check in 10 minutes."),
]


def _rule_based_fallback(event: AnomalyEvent) -> dict:
    v = event.vitals_snapshot
    for condition, severity, score, reasoning, note in _FALLBACK_RULES:
        if condition(v.heart_rate, v.spo2, v.hrv):
            return {
                "risk_score": score,
                "severity_level": severity,
                "reasoning_context": reasoning,
                "doctor_note": note,
            }
    return {
        "risk_score": 0.25,
        "severity_level": "LOW",
        "reasoning_context": "Vitals are within acceptable range; minor deviation detected.",
        "doctor_note": "No immediate action required; continue standard monitoring.",
    }


def _call_gemini(prompt: str) -> Optional[dict]:
    try:
        import vertexai  # type: ignore
        from vertexai.generative_models import GenerativeModel  # type: ignore

        project = os.environ["GCP_PROJECT_ID"]
        region = os.getenv("GCP_REGION", "us-central1")
        model_name = os.getenv("VERTEX_AI_MODEL", "gemini-pro")

        vertexai.init(project=project, location=region)
        model = GenerativeModel(model_name)
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as exc:
        print(f"[Gemini] API call failed ({exc}) — using rule-based fallback")
        return None


def classify_risk(event: AnomalyEvent) -> RiskAssessment:
    v = event.vitals_snapshot
    prompt = _PROMPT_TEMPLATE.format(
        heart_rate=v.heart_rate,
        spo2=v.spo2,
        hrv=v.hrv,
        deviation_score=event.deviation_score,
        signal_type=event.signal_type,
    )

    result = _call_gemini(prompt) or _rule_based_fallback(event)

    return RiskAssessment(
        patient_id=event.patient_id,
        risk_score=float(result["risk_score"]),
        severity_level=SeverityLevel(result["severity_level"]),
        reasoning_context=result["reasoning_context"],
        doctor_note=result["doctor_note"],
        anomaly_ref=event.anomaly_id,
    )
