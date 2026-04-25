"""
Agent 2 — Risk Assessment Agent
Receives AnomalyEvents from Agent 1, runs the LangGraph risk pipeline,
and sends RiskAssessmentMessage to Agent 3.
Registered on Agentverse as a discoverable healthcare risk intelligence service.
"""
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from uagents import Agent, Context

load_dotenv()

from agents.addresses import AGENT3_ADDRESS
from agents.message_types import AnomalyEventMessage, RiskAssessmentMessage
from agents.protocols.risk_protocol import risk_protocol

SEED = os.getenv("AGENT2_SEED", "agent2_careflow_risk_assessment_seed_phrase_change_me")

agent = Agent(
    name="CareFlow-RiskAssessment",
    seed=SEED,
    port=8002,
    endpoint=["http://localhost:8002/submit"],
)

agent.include(risk_protocol)


@agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"Agent 2 address: {agent.address}")
    ctx.logger.info("Risk Assessment Agent started — listening for AnomalyEvents")


@agent.on_message(model=AnomalyEventMessage)
async def handle_anomaly(ctx: Context, sender: str, msg: AnomalyEventMessage):
    ctx.logger.info(f"AnomalyEvent from {sender}: patient={msg.patient_id} score={msg.deviation_score}")

    from risk.pipeline import invoke_pipeline
    from models.anomaly import AnomalyEvent
    from models.vitals import VitalsPayload

    vitals = VitalsPayload(
        patient_id=msg.patient_id,
        heart_rate=msg.heart_rate,
        spo2=msg.spo2,
        hrv=msg.hrv,
        timestamp=datetime.fromisoformat(msg.detected_at),
        device_id="zetic-device",
    )
    anomaly = AnomalyEvent(
        anomaly_id=msg.anomaly_id,
        patient_id=msg.patient_id,
        signal_type=msg.signal_type,
        deviation_score=msg.deviation_score,
        vitals_snapshot=vitals,
        detected_at=datetime.fromisoformat(msg.detected_at),
    )

    # Payment Protocol scaffold — log a payment_request event
    ctx.logger.info(f"[PAYMENT] payment_request for assess_risk: patient={msg.patient_id}")

    assessment = await invoke_pipeline(anomaly)
    if assessment:
        out = RiskAssessmentMessage(
            assessment_id=str(assessment.assessment_id),
            patient_id=assessment.patient_id,
            risk_score=assessment.risk_score,
            severity_level=assessment.severity_level.value,
            reasoning_context=assessment.reasoning_context,
            anomaly_ref=str(assessment.anomaly_ref),
            generated_at=assessment.generated_at.isoformat(),
        )
        await ctx.send(AGENT3_ADDRESS, out)
        ctx.logger.info(f"RiskAssessment sent to Agent 3: score={assessment.risk_score}")


if __name__ == "__main__":
    agent.run()
