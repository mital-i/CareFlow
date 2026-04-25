"""CareFlow FastAPI Gateway

Endpoints:
  GET  /patients                          — list demo patients
  GET  /vitals/stream/{patient_id}        — SSE live vitals (proxied from vitals.api)
  GET  /vitals/latest/{patient_id}        — single vitals reading
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

DEMO_PATIENTS = [
    {
        "patient_id": "patient-001",
        "name": "Margaret Chen",
        "age": 67,
        "conditions": ["Atrial Fibrillation", "Hypertension"],
        "baseline_hr": 72,
        "baseline_spo2": 98.5,
        "baseline_hrv": 58,
    },
    {
        "patient_id": "patient-002",
        "name": "Robert Okafor",
        "age": 54,
        "conditions": ["Type 2 Diabetes", "Coronary Artery Disease"],
        "baseline_hr": 68,
        "baseline_spo2": 97.8,
        "baseline_hrv": 62,
    },
    {
        "patient_id": "patient-003",
        "name": "Sofia Ramirez",
        "age": 71,
        "conditions": ["COPD", "Post-op Cardiac Recovery"],
        "baseline_hr": 78,
        "baseline_spo2": 96.5,
        "baseline_hrv": 44,
    },
]


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


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.get("/health")
async def health():
    return {"status": "ok"}
