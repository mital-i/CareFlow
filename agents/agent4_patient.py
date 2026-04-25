"""
Agent 4 — Patient Agent
Lightweight Fetch.ai uAgent representing the patient.
Stores notification preferences in MongoDB and responds to queries from Agent 3.
"""
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from uagents import Agent, Context

load_dotenv()

from agents.message_types import PatientPreferencesMessage, StatusOKMessage
from agents.protocols.patient_protocol import patient_protocol
from db.db import get_patient

SEED = os.getenv("AGENT4_SEED", "agent4_careflow_patient_seed_phrase_change_me")

agent = Agent(
    name="CareFlow-Patient",
    seed=SEED,
    port=8004,
    endpoint=["http://localhost:8004/submit"],
)

agent.include(patient_protocol)


@agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"Agent 4 address: {agent.address}")
    ctx.logger.info("Patient Agent started")


@agent.on_message(model=PatientPreferencesMessage)
async def handle_preferences_request(ctx: Context, sender: str, msg: PatientPreferencesMessage):
    """Return patient preferences for a given patient_id."""
    patient_doc = get_patient(msg.patient_id)
    if not patient_doc:
        ctx.logger.warning(f"Patient {msg.patient_id} not found")
        return

    prefs = patient_doc.get("notification_prefs", {})
    hour = datetime.now(timezone.utc).hour
    dnd_hours = prefs.get("do_not_disturb_hours") or []
    can_alert = hour not in dnd_hours

    response = PatientPreferencesMessage(
        patient_id=msg.patient_id,
        notification_sensitivity=prefs.get("sensitivity", "MEDIUM"),
        preferred_channel=prefs.get("preferred_channel", "push"),
        can_receive_alert=can_alert,
    )
    await ctx.send(sender, response)
    ctx.logger.info(f"Preferences sent for {msg.patient_id}: can_receive={can_alert}")


if __name__ == "__main__":
    agent.run()
