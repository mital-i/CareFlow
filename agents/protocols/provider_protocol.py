"""Chat Protocol handlers for Agent 5 — Provider Agent."""
from uagents import Context, Protocol

from agents.message_types import AvailabilitySlotMessage, AcknowledgeAlertMessage, StatusOKMessage

provider_protocol = Protocol("ProviderProtocol")


@provider_protocol.on_message(model=AcknowledgeAlertMessage)
async def handle_acknowledge(ctx: Context, sender: str, msg: AcknowledgeAlertMessage):
    ctx.logger.info(f"Alert {msg.alert_id} acknowledged by provider via {sender}")
    await ctx.send(sender, StatusOKMessage())
