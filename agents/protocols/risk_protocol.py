"""Chat Protocol handlers for Agent 2 — Risk Assessment Agent."""
from uagents import Context, Protocol

from agents.message_types import AnomalyEventMessage, RiskAssessmentMessage

risk_protocol = Protocol("RiskProtocol")


@risk_protocol.on_message(model=AnomalyEventMessage)
async def handle_anomaly_event(ctx: Context, sender: str, msg: AnomalyEventMessage):
    """Receive AnomalyEvent from Agent 1 and trigger the risk pipeline."""
    ctx.logger.info(f"AnomalyEvent received from {sender}: patient={msg.patient_id}, score={msg.deviation_score}")
    # Imported here to avoid circular imports at module level
    from risk.pipeline import invoke_pipeline
    from models.anomaly import AnomalyEvent
    from models.vitals import VitalsPayload
    from datetime import datetime, timezone

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
    result = await invoke_pipeline(anomaly)
    ctx.logger.info(f"Risk assessment complete: {result}")
