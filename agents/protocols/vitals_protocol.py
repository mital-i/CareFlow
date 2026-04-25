"""Chat Protocol handlers for Agent 1 — Vital Monitoring Agent."""
from uagents import Context, Protocol

from agents.message_types import AnomalyEventMessage

vitals_protocol = Protocol("VitalsProtocol")


@vitals_protocol.on_message(model=AnomalyEventMessage)
async def handle_anomaly_query(ctx: Context, sender: str, msg: AnomalyEventMessage):
    """Agent 3 can query Agent 1 for the latest anomaly state."""
    ctx.logger.info(f"Received anomaly query from {sender}")
    # TODO: respond with current anomaly state if needed
