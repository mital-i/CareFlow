"""
LangGraph node functions for the risk assessment pipeline.
Each node receives and returns the RiskPipelineState dict.
"""
from typing import Any, Dict

from db.db import save_risk_assessment
from risk.cache import cache_assessment
from risk.classifier import classify_risk
from risk.history import build_patient_history


def fetch_patient_history(state: Dict[str, Any]) -> Dict[str, Any]:
    anomaly = state["anomaly"]
    try:
        history = build_patient_history(anomaly.patient_id)
        return {**state, "patient_history": history, "error": None}
    except Exception as exc:
        return {**state, "error": str(exc)}


def run_classify_risk(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("error"):
        return state
    anomaly = state["anomaly"]
    history = state["patient_history"]
    try:
        assessment = classify_risk(anomaly, history)
        return {**state, "risk_assessment": assessment, "error": None}
    except Exception as exc:
        return {**state, "error": str(exc)}


def emergency_flag(state: Dict[str, Any]) -> Dict[str, Any]:
    """Set a critical flag if risk_score > 0.9."""
    assessment = state.get("risk_assessment")
    if assessment:
        from models.schemas import SeverityLevel
        assessment.severity_level = SeverityLevel.CRITICAL
    return {**state, "emergency": True}


def save_assessment_node(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("error") or not state.get("risk_assessment"):
        return state
    assessment = state["risk_assessment"]
    doc = assessment.model_dump()
    doc["assessment_id"] = str(doc["assessment_id"])
    doc["anomaly_ref"] = str(doc["anomaly_ref"]) if doc.get("anomaly_ref") else None
    doc["generated_at"] = doc["generated_at"].isoformat()
    doc["severity_level"] = doc["severity_level"].value if hasattr(doc["severity_level"], "value") else doc["severity_level"]
    save_risk_assessment(doc)
    cache_assessment(assessment)
    return state


def publish_result(state: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder — Agent 2's message handler sends to Agent 3 after pipeline completes."""
    assessment = state.get("risk_assessment")
    if assessment:
        print(f"[PIPELINE] Published: patient={assessment.patient_id} score={assessment.risk_score} severity={assessment.severity_level}")
    return state
