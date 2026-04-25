"""Patient REST endpoints consumed by the React dashboard."""
from fastapi import APIRouter, HTTPException

from db.db import get_patient, list_patients, get_recent_vitals, get_action_logs, get_latest_risk_assessment

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
async def get_all_patients():
    patients = list_patients()
    result = []
    for p in patients:
        pid = p["patient_id"]
        latest_risk = get_latest_risk_assessment(pid)
        latest_vitals = get_recent_vitals(pid, limit=1)
        result.append({
            **p,
            "current_risk_score": latest_risk["risk_score"] if latest_risk else None,
            "current_severity": latest_risk["severity_level"] if latest_risk else None,
            "latest_vitals": latest_vitals[0] if latest_vitals else None,
        })
    return result


@router.get("/{patient_id}/history")
async def get_patient_history(patient_id: str, limit: int = 50):
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return get_recent_vitals(patient_id, limit=limit)


@router.get("/{patient_id}/actions")
async def get_patient_actions(patient_id: str, limit: int = 20):
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return get_action_logs(patient_id, limit=limit)
