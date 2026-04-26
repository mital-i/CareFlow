"""CareFlow FastAPI Gateway

Endpoints:
  GET  /patients                          — list demo patients
  GET  /vitals/stream/{patient_id}        — SSE live vitals (proxied from vitals.api)
  GET  /vitals/current/{patient_id}       — latest vitals reading
  POST /trigger-anomaly                   — inject demo anomaly
  GET  /agents/status                     — heartbeat for both agents
  POST /internal/broadcast               — called by Coordinator agent to push WS events
  WS   /ws                               — WebSocket hub for React dashboard
"""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.ws_manager import manager
from db.db import get_db, seed_demo_patient_if_missing, DEMO_PATIENTS
from vitals.api import router as vitals_router

app = FastAPI(title="CareFlow API", version="1.0.0")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vitals_router)



@app.on_event("startup")
async def startup() -> None:
    try:
        get_db().command("ping")
        print("[CareFlow] Mongo connected")
        seed_demo_patient_if_missing()
        print("[CareFlow] Demo patient ready")
    except Exception as exc:
        print(f"[CareFlow] Mongo startup skipped: {exc}")

    print("[CareFlow] Vitals stream ready: GET /vitals/stream/patient-001")
    print("[CareFlow] Trigger endpoint ready: POST /trigger-anomaly")


@app.get("/patients")
async def list_patients():
    return DEMO_PATIENTS


@app.get("/agents/status")
async def agents_status():
    return {
        "monitor_agent": {"name": "CareFlow-VitalMonitor", "status": "running", "port": 8001},
        "coordinator_agent": {"name": "CareFlow-Coordinator", "status": "running", "port": 8002},
    }


class BroadcastRequest(BaseModel):
    event_type: str
    data: dict


@app.post("/internal/broadcast")
async def internal_broadcast(req: BroadcastRequest):
    """Called by Coordinator agent to push events to WebSocket clients."""
    await manager.broadcast(req.event_type, req.data)
    return {"broadcasted": True, "connections": len(manager.active)}


@app.post("/acknowledge/{assessment_id}")
async def acknowledge_assessment(assessment_id: str):
    await manager.broadcast("acknowledged", {"assessment_id": assessment_id})
    return {"ok": True}


@app.get("/anomalies/{patient_id}")
async def get_anomaly_history(patient_id: str, limit: int = 20):
    try:
        db = get_db()
        docs = list(
            db.anomaly_events.find(
                {"patient_id": patient_id},
                {"_id": 0},
            ).sort("detected_at", -1).limit(limit)
        )
        return docs
    except Exception as exc:
        return []


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(ws)
