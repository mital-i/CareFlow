"""Agent 1: Vital Monitoring Agent

Runs the heuristic anomaly detector every second over configured vitals.
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

import httpx
from uagents import Agent, Context, Protocol

from agents.addresses import COORDINATOR_AGENT_ADDRESS
from agents.message_types import AnomalyMessage, VitalsMessage
from models.schemas import VitalsPayload
from vitals.anomaly import process_vitals
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

AGENT_MONITOR_SEED_PHRASE = os.getenv("AGENT_MONITOR_SEED_PHRASE", "your-agent-seed-phrase-here")
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

ALL_PATIENT_IDS = ["patient-001", "patient-002", "patient-003"]

monitor_agent = Agent(
    name="CareFlow-VitalMonitor",
    seed=AGENT_MONITOR_SEED_PHRASE,
    port=8001,
    mailbox=True,
    endpoint=["http://localhost:8001/submit"],
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)

@monitor_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"[Monitor] Agent address: {monitor_agent.address}")
    ctx.logger.info("[Monitor] Vital monitoring started — streaming vitals at 1 Hz")


@monitor_agent.on_interval(period=1.0)
async def tick(ctx: Context):
    async with httpx.AsyncClient() as client:
        for patient_id in ALL_PATIENT_IDS:
            try:
                resp = await client.get(f"{API_BASE}/vitals/current/{patient_id}", timeout=3.0)
                resp.raise_for_status()
                payload = VitalsPayload(**resp.json())
            except Exception as exc:
                ctx.logger.warning(f"[Monitor] Failed to fetch vitals for {patient_id}: {exc}")
                continue

            anomaly = process_vitals(payload)
            if anomaly:
                ctx.logger.warning(
                    f"[Monitor] ANOMALY {patient_id} score={anomaly.deviation_score:.3f} — forwarding to Coordinator"
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
