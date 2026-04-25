"""
Agent 1 — Vital Monitoring Agent
Runs ZETIC Melange anomaly detection and publishes AnomalyEvents to Agent 2 via Agentverse.
Register on Agentverse, then update agents/addresses.py with the printed address.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from uagents import Agent, Context

sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from agents.addresses import AGENT2_ADDRESS
from agents.message_types import AnomalyEventMessage
from agents.protocols.vitals_protocol import chat_protocol, vitals_protocol
from vitals.generator import generate_one
from zetic.melange_agent import MelangeAgent
from db.db import flag_vitals_anomaly, save_vitals, setup_database

SEED = os.getenv("AGENT1_SEED", "agent1_careflow_vital_monitor_seed_phrase_change_me")
PATIENT_IDS = [p.strip() for p in os.getenv("DEMO_PATIENT_IDS", "P001,P002,P003").split(",") if p.strip()]
AGENT1_ENDPOINT = os.getenv("AGENT1_ENDPOINT", "http://localhost:8001/submit")
# TODO: Replace AGENT1_PUBLIC_ENDPOINT with a real public tunnel URL before Agentverse judging.
AGENT1_PUBLIC_ENDPOINT = os.getenv("AGENT1_PUBLIC_ENDPOINT")
ENDPOINTS = [AGENT1_PUBLIC_ENDPOINT or AGENT1_ENDPOINT]

agent = Agent(
    name="CareFlow-VitalMonitor",
    seed=SEED,
    port=8001,
    endpoint=ENDPOINTS,
)

agent.include(vitals_protocol)
if chat_protocol is not None:
    agent.include(chat_protocol, publish_manifest=True)

_melange_by_patient = {patient_id: MelangeAgent(patient_id=patient_id) for patient_id in PATIENT_IDS}


@agent.on_event("startup")
async def on_startup(ctx: Context):
    setup_database()
    ctx.logger.info(f"Agent 1 address: {agent.address}")
    ctx.logger.info(f"Agent 1 endpoint(s): {ENDPOINTS}")
    ctx.logger.info("Vital Monitoring Agent started — streaming vitals for all patients")


@agent.on_interval(period=1.0)
async def monitor_vitals(ctx: Context):
    """Every second, generate vitals for all demo patients and run anomaly detection."""
    for patient_id in PATIENT_IDS:
        payload = generate_one(patient_id)

        doc = payload.model_dump()
        doc["anomaly_flagged"] = False
        save_vitals(doc)

        melange = _melange_by_patient[patient_id]
        anomaly = melange.push_vitals(payload)

        if anomaly:
            flag_vitals_anomaly(patient_id, payload.timestamp, device_id=payload.device_id)
            ctx.logger.info(
                f"[ANOMALY] detected_at={anomaly.detected_at.isoformat()} "
                f"patient={patient_id} score={anomaly.deviation_score} type={anomaly.signal_type}"
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
            if AGENT2_ADDRESS and not AGENT2_ADDRESS.endswith("..."):
                await ctx.send(AGENT2_ADDRESS, msg)
            else:
                ctx.logger.warning("AGENT2_ADDRESS is not configured; anomaly was logged but not sent")


if __name__ == "__main__":
    agent.run()
