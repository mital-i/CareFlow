"""Protocol handlers for Agent 1 — Vital Monitoring Agent."""
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Context, Protocol

from agents.message_types import (
    DetectAnomalyRequestMessage,
    DetectAnomalyResponseMessage,
    VitalsQueryMessage,
    VitalsResponseMessage,
)
from db.db import get_latest_vitals
from models.vitals import VitalsPayload
from zetic.melange_agent import MelangeAgent

vitals_protocol = Protocol("VitalsProtocol")
_query_agents: dict[str, MelangeAgent] = {}


def _iso(value) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _get_query_agent(patient_id: str) -> MelangeAgent:
    if patient_id not in _query_agents:
        _query_agents[patient_id] = MelangeAgent(patient_id=patient_id)
    return _query_agents[patient_id]


@vitals_protocol.on_message(model=VitalsQueryMessage)
async def get_latest_vitals_handler(ctx: Context, sender: str, msg: VitalsQueryMessage):
    """Return the latest MongoDB-backed vitals snapshot for a patient."""
    latest = get_latest_vitals(msg.patient_id)
    if not latest:
        ctx.logger.warning(f"No latest vitals found for patient {msg.patient_id}")
        return
    await ctx.send(
        sender,
        VitalsResponseMessage(
            patient_id=latest["patient_id"],
            heart_rate=latest["heart_rate"],
            spo2=latest["spo2"],
            hrv=latest["hrv"],
            timestamp=_iso(latest["timestamp"]),
            device_id=latest["device_id"],
            anomaly_flagged=latest.get("anomaly_flagged", False),
        ),
    )


@vitals_protocol.on_message(model=DetectAnomalyRequestMessage)
async def detect_anomaly_handler(ctx: Context, sender: str, msg: DetectAnomalyRequestMessage):
    """Run the patient's Melange detector on an on-demand vitals reading."""
    payload = VitalsPayload(
        patient_id=msg.patient_id,
        heart_rate=msg.heart_rate,
        spo2=msg.spo2,
        hrv=msg.hrv,
        timestamp=datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00")),
        device_id=msg.device_id,
    )
    detector = _get_query_agent(msg.patient_id)
    anomaly = detector.push_vitals(payload)
    await ctx.send(
        sender,
        DetectAnomalyResponseMessage(
            patient_id=msg.patient_id,
            anomaly_detected=anomaly is not None,
            deviation_score=detector.latest_score or 0.0,
            signal_type=anomaly.signal_type if anomaly else None,
            anomaly_id=str(anomaly.anomaly_id) if anomaly else None,
            detected_at=anomaly.detected_at.isoformat() if anomaly else None,
        ),
    )


chat_protocol = None

try:
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement,
        ChatMessage,
        EndSessionContent,
        TextContent,
        chat_protocol_spec,
    )

    chat_protocol = Protocol(spec=chat_protocol_spec)

    def _chat_response(text: str, end_session: bool = False) -> ChatMessage:
        content = [TextContent(type="text", text=text)]
        if end_session:
            content.append(EndSessionContent(type="end-session"))
        return ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=content)

    @chat_protocol.on_message(ChatMessage)
    async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
        await ctx.send(
            sender,
            ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id),
        )
        text = (msg.text() or "").upper()
        patient_id = next((token for token in text.replace("?", " ").split() if token.startswith("P00")), "P001")
        latest = get_latest_vitals(patient_id)
        if not latest:
            await ctx.send(sender, _chat_response(f"No latest vitals found for {patient_id}.", end_session=True))
            return
        response = (
            f"Latest vitals for {patient_id}: HR {latest['heart_rate']} bpm, "
            f"SpO2 {latest['spo2']}%, HRV {latest['hrv']} ms at {_iso(latest['timestamp'])}. "
            f"Anomaly flagged: {latest.get('anomaly_flagged', False)}."
        )
        await ctx.send(sender, _chat_response(response, end_session=True))

    @chat_protocol.on_message(ChatAcknowledgement)
    async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
        return
except Exception:
    chat_protocol = None
