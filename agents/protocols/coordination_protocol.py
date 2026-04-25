"""Chat Protocol handlers for Agent 3 — Care Coordination Agent."""
from uagents import Context, Protocol

from agents.message_types import RiskAssessmentMessage, ActionDecisionMessage

coordination_protocol = Protocol("CoordinationProtocol")


@coordination_protocol.on_message(model=RiskAssessmentMessage)
async def handle_risk_assessment(ctx: Context, sender: str, msg: RiskAssessmentMessage):
    """Main handler — receives RiskAssessment from Agent 2, routes action."""
    ctx.logger.info(
        f"RiskAssessment received: patient={msg.patient_id}, score={msg.risk_score}, severity={msg.severity_level}"
    )
    # TODO: import and call the coordination logic from agent3_coordinator
