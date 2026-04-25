"""
Agent 1 — Vital Monitoring Agent
Runs ZETIC Melange anomaly detection and publishes AnomalyEvents to Agent 2 via Agentverse.
Register on Agentverse, then update agents/addresses.py with the printed address.
"""
import asyncio
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from uagents import Agent, Context

load_dotenv()

from agents.addresses import AGENT2_ADDRESS
from agents.message_types import AnomalyEventMessage
from models.vitals import VitalsPayload
from vitals.generator import stream_vitals
from zetic.melange_agent import MelangeAgent
from db.db import save_vitals

SEED = os.getenv("AGENT1_SEED", "agent1_careflow_vital_monitor_seed_phrase_change_me")

agent = Agent(
    name="CareFlow-VitalMonitor",
    seed=SEED,
    port=8001,
    endpoint=["http://localhost:8001/submit"],
)

_melange = MelangeAgent(patient_id="ALL")  # one per patient in production


@agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"Agent 1 address: {agent.address}")
    ctx.logger.info("Vital Monitoring Agent started — streaming vitals for all patients")


@agent.on_interval(period=1.0)
async def monitor_vitals(ctx: Context):
    """Every second, generate vitals for all demo patients and run anomaly detection."""
    patient_ids = ["P001", "P002", "P003"]
    for patient_id in patient_ids:
        from vitals.generator import generate_one
        payload = generate_one(patient_id, 0)

        doc = payload.model_dump()
        doc["timestamp"] = doc["timestamp"].isoformat()
        save_vitals({**doc})

        melange = MelangeAgent(patient_id=patient_id)
        anomaly = melange.push_vitals(payload)

        if anomaly:
            ctx.logger.info(
                f"[ANOMALY] patient={patient_id} score={anomaly.deviation_score} type={anomaly.signal_type}"
            )
            msg = AnomalyEventMessage(
                anomaly_id=str(anomaly.anomaly_id),
                patient_id=anomaly.patient_id,
                signal_type=anomaly.signal_type,
                deviation_score=anomaly.deviation_score,
                heart_rate=anomaly.vitals_snapshot.heart_rate,
                spo2=anomaly.vitals_snapshot.spo2,
                hrv=anomaly.vitals_snapshot.hrv,
                detected_at=anomaly.detected_at.isoformat(),
            )
            await ctx.send(AGENT2_ADDRESS, msg)


if __name__ == "__main__":
    agent.run()
