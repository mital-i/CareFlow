"""Agent 2: Care Coordinator Agent (Doctor's Assistant)

Receives AnomalyMessage from the Monitor Agent, calls Gemini for risk
classification, decides the action tier, and broadcasts the result to the
React dashboard via the FastAPI WebSocket hub.

Start:  python agents/agent2_coordinator.py
"""
from __future__ import annotations
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)
from uagents import Agent, Context, Protocol 

import httpx
from dotenv import load_dotenv
load_dotenv()

from agents.message_types import AnomalyMessage, RiskMessage, ActionMessage
from models.schemas import (
    AnomalyEvent, VitalsPayload, ActionTier, SeverityLevel
)
from risk.classifier import classify_risk

AGENT_COORDINATOR_SEED_PHRASE = os.getenv("AGENT_COORDINATOR_SEED_PHRASE", "your-agent-seed-phrase-here")
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

coordinator_agent = Agent(
    name="CareFlow-Coordinator",
    seed=AGENT_COORDINATOR_SEED_PHRASE,
    port=8002,
    endpoint=["http://localhost:8002/submit"],
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)

def _severity_to_tier(severity: SeverityLevel) -> ActionTier:
    mapping = {
        SeverityLevel.LOW: ActionTier.LOG_ONLY,
        SeverityLevel.MEDIUM: ActionTier.PATIENT_ALERT,
        SeverityLevel.HIGH: ActionTier.PROVIDER_NOTIFY,
        SeverityLevel.CRITICAL: ActionTier.ER_DISPATCH,
    }
    return mapping[severity]


def _build_provider_message(assessment) -> str | None:
    if assessment.severity_level in (SeverityLevel.HIGH, SeverityLevel.CRITICAL):
        return (
            f"[CareFlow Alert] Patient {assessment.patient_id} — "
            f"{assessment.severity_level.value} risk (score {assessment.risk_score:.2f}). "
            f"{assessment.doctor_note}"
        )
    return None


async def _broadcast_to_dashboard(event_type: str, data: dict) -> None:
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{API_BASE}/internal/broadcast",
                json={"event_type": event_type, "data": data},
                timeout=3.0,
            )
    except Exception as exc:
        print(f"[Coordinator] Dashboard broadcast failed: {exc}")


@coordinator_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"[Coordinator] Agent address: {coordinator_agent.address}")
    ctx.logger.info("[Coordinator] Ready to receive anomaly events")


@coordinator_agent.on_message(model=AnomalyMessage)
async def handle_anomaly(ctx: Context, sender: str, msg: AnomalyMessage):
    ctx.logger.info(
        f"[Coordinator] Received anomaly from {sender} — patient={msg.patient_id} score={msg.deviation_score:.3f}"
    )

    vitals = VitalsPayload(
        patient_id=msg.patient_id,
        heart_rate=msg.heart_rate,
        spo2=msg.spo2,
        hrv=msg.hrv,
        device_id=os.getenv("DEVICE_ID", "careflow_watch_001"),
    )
    anomaly_event = AnomalyEvent(
        anomaly_id=msg.anomaly_id,
        patient_id=msg.patient_id,
        signal_type=msg.signal_type,
        deviation_score=msg.deviation_score,
        vitals_snapshot=vitals,
    )

    assessment = classify_risk(anomaly_event)
    tier = _severity_to_tier(assessment.severity_level)
    provider_msg = _build_provider_message(assessment)

    ctx.logger.info(
        f"[Coordinator] Assessment: score={assessment.risk_score:.2f} "
        f"severity={assessment.severity_level.value} action={tier.value}"
    )

    await _broadcast_to_dashboard("risk_assessment", {
        "assessment_id": str(assessment.assessment_id),
        "patient_id": assessment.patient_id,
        "risk_score": assessment.risk_score,
        "severity_level": assessment.severity_level.value,
        "reasoning_context": assessment.reasoning_context,
        "doctor_note": assessment.doctor_note,
        "action_tier": tier.value,
        "provider_message": provider_msg,
        "safety_report": assessment.safety_report.model_dump() if assessment.safety_report else None,
        "generated_at": assessment.generated_at.isoformat(),
    })


if __name__ == "__main__":
    coordinator_agent.run()
