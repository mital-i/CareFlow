"""
Agent 3 — Care Coordination Agent (Core Orchestrator)
Receives RiskAssessment from Agent 2, queries Agents 4 & 5 for context,
applies routing logic, saves ActionDecision to MongoDB, and broadcasts to the dashboard.
"""
import os
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from uagents import Agent, Context

load_dotenv()

from agents.addresses import AGENT4_ADDRESS, AGENT5_ADDRESS
from agents.message_types import (
    RiskAssessmentMessage,
    ActionDecisionMessage,
    PatientPreferencesMessage,
    AvailabilitySlotMessage,
)
from agents.ws_broadcaster import broadcast_sync
from db.db import save_action_log

SEED = os.getenv("AGENT3_SEED", "agent3_careflow_coordinator_seed_phrase_change_me")

agent = Agent(
    name="CareFlow-Coordinator",
    seed=SEED,
    port=8003,
    endpoint=["http://localhost:8003/submit"],
)

# Routing thresholds
TIER_LOG_ONLY = 0.4
TIER_PATIENT_ALERT = 0.6
TIER_PROVIDER_NOTIFY = 0.8


@agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"Agent 3 address: {agent.address}")
    ctx.logger.info("Care Coordination Agent started — ready to orchestrate")


@agent.on_message(model=RiskAssessmentMessage)
async def handle_risk_assessment(ctx: Context, sender: str, msg: RiskAssessmentMessage):
    ctx.logger.info(
        f"RiskAssessment received: patient={msg.patient_id} score={msg.risk_score} severity={msg.severity_level}"
    )

    hour = datetime.now(timezone.utc).hour
    dnd = False  # TODO: query Agent 4 for DND status

    score = msg.risk_score
    if dnd:
        score = min(score + 0.2, 1.0)

    if score < TIER_LOG_ONLY:
        tier = "LOG_ONLY"
    elif score < TIER_PATIENT_ALERT:
        tier = "PATIENT_ALERT"
    elif score < TIER_PROVIDER_NOTIFY:
        tier = "PATIENT_ALERT"
        # Also notify provider
    else:
        tier = "PROVIDER_NOTIFY" if score < 0.8 else "ER_DISPATCH"

    provider_message = None
    if tier in ("PROVIDER_NOTIFY", "ER_DISPATCH"):
        provider_message = (
            f"[CareFlow Alert] Patient {msg.patient_id} — {msg.severity_level} risk detected. "
            f"Score: {msg.risk_score:.2f}. {msg.reasoning_context}"
        )

    action_id = str(uuid4())
    action = {
        "action_id": action_id,
        "patient_id": msg.patient_id,
        "assessment_ref": msg.assessment_id,
        "action_tier": tier,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "provider_message": provider_message,
    }
    save_action_log(action)

    broadcast_sync("action_decision", {
        **action,
        "risk_score": msg.risk_score,
        "severity_level": msg.severity_level,
        "reasoning_context": msg.reasoning_context,
    })

    ctx.logger.info(f"[ACTION] tier={tier} patient={msg.patient_id} action_id={action_id}")


if __name__ == "__main__":
    agent.run()
