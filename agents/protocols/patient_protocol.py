"""Chat Protocol handlers for Agent 4 — Patient Agent."""
from uagents import Context, Protocol

from agents.message_types import PatientPreferencesMessage, StatusOKMessage

patient_protocol = Protocol("PatientProtocol")


@patient_protocol.on_message(model=PatientPreferencesMessage)
async def handle_preference_query(ctx: Context, sender: str, msg: PatientPreferencesMessage):
    """Return patient preferences when queried by Agent 3."""
    ctx.logger.info(f"Preference query from {sender} for patient {msg.patient_id}")
    # TODO: load from MongoDB and reply
