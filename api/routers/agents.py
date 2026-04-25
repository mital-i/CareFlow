"""Agent status and trigger endpoints."""
from fastapi import APIRouter

from agents.addresses import (
    AGENT1_ADDRESS, AGENT2_ADDRESS, AGENT3_ADDRESS, AGENT4_ADDRESS, AGENT5_ADDRESS,
)
from vitals.generator import trigger_anomaly

router = APIRouter(prefix="/agents", tags=["agents"])

AGENT_REGISTRY = [
    {"id": "agent1", "name": "Vital Monitoring Agent", "address": AGENT1_ADDRESS, "tech": "ZETIC Melange"},
    {"id": "agent2", "name": "Risk Assessment Agent", "address": AGENT2_ADDRESS, "tech": "Vertex AI + LangGraph"},
    {"id": "agent3", "name": "Care Coordination Agent", "address": AGENT3_ADDRESS, "tech": "Fetch.ai Orchestrator"},
    {"id": "agent4", "name": "Patient Agent", "address": AGENT4_ADDRESS, "tech": "Fetch.ai uAgent"},
    {"id": "agent5", "name": "Provider Agent", "address": AGENT5_ADDRESS, "tech": "Fetch.ai uAgent"},
]


@router.get("/status")
async def get_agent_status():
    # TODO: implement real heartbeat checks against each agent's endpoint
    return [
        {**agent, "status": "online", "heartbeat": True}
        for agent in AGENT_REGISTRY
    ]


@router.post("/trigger-anomaly")
async def trigger_anomaly_endpoint(patient_id: str = "P001"):
    trigger_anomaly(patient_id)
    return {"status": "triggered", "patient_id": patient_id}
