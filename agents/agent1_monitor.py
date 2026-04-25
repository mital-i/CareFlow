"""Agent 1: Vital Monitoring Agent (ZETIC Edge Agent)

Runs the ZETIC on-device anomaly detector every second over synthetic vitals.
When an anomaly is detected, publishes an AnomalyMessage to the Coordinator Agent
via Fetch.ai Chat Protocol.

Start:  python agents/agent1_monitor.py
"""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from uagents import Agent, Context, Protocol 

from agents.addresses import COORDINATOR_AGENT_ADDRESS
from agents.message_types import AnomalyMessage, VitalsMessage
from models.schemas import VitalsPayload
from vitals.generator import generate_vitals
from zetic.melange_agent import process_vitals
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

AGENT_SEED = os.getenv("AGENT_MONITOR_SEED", "careflow-monitor-agent-seed-phrase-001")
DEMO_PATIENT_ID = os.getenv("DEMO_PATIENT_ID", "patient-001")
AGENTVERSE_KEY = os.getenv("AGENTVERSE_KEY", "your-agentverse-key-here")
AGENT_MONITOR_SEED_PHRASE = os.getenv("AGENT_MONITOR_SEED_PHRASE", "your-agent-seed-phrase-here")

monitor_agent = Agent(
    name="CareFlow-VitalMonitor",
    seed=AGENT_MONITOR_SEED_PHRASE,
    mailbox=True,
    port=8001, 
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)

@monitor_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"[Monitor] Agent address: {monitor_agent.address}")
    ctx.logger.info("[Monitor] Vital monitoring started — streaming vitals at 1 Hz")


@monitor_agent.on_interval(period=1.0)
async def tick(ctx: Context):
    payload: VitalsPayload = generate_vitals(DEMO_PATIENT_ID)

    ctx.logger.debug(
        f"[Monitor] HR={payload.heart_rate} SpO2={payload.spo2} HRV={payload.hrv}"
    )

    anomaly = process_vitals(payload)
    if anomaly:
        ctx.logger.warning(
            f"[Monitor] ANOMALY detected! score={anomaly.deviation_score:.3f} — forwarding to Coordinator"
        )
        msg = AnomalyMessage(
            anomaly_id=str(anomaly.anomaly_id),
            patient_id=anomaly.patient_id,
            signal_type=anomaly.signal_type,
            deviation_score=anomaly.deviation_score,
            heart_rate=payload.heart_rate,
            spo2=payload.spo2,
            hrv=payload.hrv,
            detected_at=anomaly.detected_at.isoformat(),
        )
        await ctx.send(COORDINATOR_AGENT_ADDRESS, msg)


if __name__ == "__main__":
    monitor_agent.run()
