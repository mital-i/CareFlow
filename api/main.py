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

import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.ws_manager import manager
from db.db import get_db, seed_demo_patient_if_missing, DEMO_PATIENTS
from vitals.api import router as vitals_router

app = FastAPI(title="CareFlow API", version="1.0.0")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")
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


class TTSRequest(BaseModel):
    text: str


async def _request_elevenlabs_tts(client: httpx.AsyncClient, voice_id: str, text: str) -> httpx.Response:
    return await client.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": ELEVENLABS_MODEL_ID,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        },
        timeout=10.0,
    )


@app.post("/tts")
async def text_to_speech(req: TTSRequest):
    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        raise HTTPException(status_code=503, detail="ElevenLabs not configured")
    try:
        async with httpx.AsyncClient() as client:
            resp = await _request_elevenlabs_tts(client, ELEVENLABS_VOICE_ID, req.text)
    except httpx.RequestError as exc:
        print(f"[TTS] ElevenLabs request failed: {exc}")
        raise HTTPException(status_code=503, detail="Voice alert service unavailable") from exc

    if resp.status_code == 402:
        print("[TTS] ElevenLabs returned 402 Payment Required; voice alert skipped")
        raise HTTPException(
            status_code=402,
            detail="ElevenLabs quota or billing limit reached; voice alert skipped",
        )
    if resp.is_error:
        print(f"[TTS] ElevenLabs returned HTTP {resp.status_code}: {resp.text[:200]}")
        raise HTTPException(
            status_code=502,
            detail=f"Voice alert provider returned HTTP {resp.status_code}",
        )

    return StreamingResponse(iter([resp.content]), media_type="audio/mpeg")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(ws)
