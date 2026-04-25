"""
Agent 5 — Provider Agent
Simulates a doctor's availability schedule and handles alert acknowledgments.
Agent 3 queries this agent before routing PROVIDER_NOTIFY or ER_DISPATCH actions.
"""
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from uagents import Agent, Context

load_dotenv()

from agents.message_types import AvailabilitySlotMessage, AcknowledgeAlertMessage, StatusOKMessage
from agents.protocols.provider_protocol import provider_protocol

SEED = os.getenv("AGENT5_SEED", "agent5_careflow_provider_seed_phrase_change_me")

agent = Agent(
    name="CareFlow-Provider",
    seed=SEED,
    port=8005,
    endpoint=["http://localhost:8005/submit"],
)

agent.include(provider_protocol)

# Simulated state
_current_load: int = 3
_on_call: bool = False


def _check_availability(urgency: str) -> AvailabilitySlotMessage:
    now = datetime.now(timezone.utc)
    # Convert to PT (UTC-7 for PDT, UTC-8 for PST)
    pt_offset = -7
    pt_hour = (now.hour + pt_offset) % 24
    is_business_hours = 9 <= pt_hour < 17 and now.weekday() < 5

    if is_business_hours:
        return AvailabilitySlotMessage(
            available=True,
            slot_time=now.isoformat(),
            callback_type="immediate",
        )
    elif urgency == "CRITICAL":
        next_slot = now + timedelta(minutes=15)
        return AvailabilitySlotMessage(
            available=True,
            slot_time=next_slot.isoformat(),
            callback_type="oncall",
        )
    else:
        # Next business day 9am PT
        next_day = now + timedelta(days=1)
        next_slot = next_day.replace(hour=16, minute=0, second=0, microsecond=0)  # 9am PT = 16:00 UTC
        return AvailabilitySlotMessage(
            available=False,
            slot_time=next_slot.isoformat(),
            callback_type="scheduled",
        )


@agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"Agent 5 address: {agent.address}")
    ctx.logger.info("Provider Agent started — Dr. Shah availability simulation active")


@agent.on_message(model=AcknowledgeAlertMessage)
async def handle_acknowledge(ctx: Context, sender: str, msg: AcknowledgeAlertMessage):
    ctx.logger.info(f"Alert {msg.alert_id} acknowledged at {msg.acknowledged_at}")
    await ctx.send(sender, StatusOKMessage())


if __name__ == "__main__":
    agent.run()
