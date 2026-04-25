"""
SSE endpoint for live vitals streaming.
Mounted at /vitals/stream/{patient_id} by the FastAPI gateway (api/main.py).
Also exposes POST /trigger-anomaly for the demo harness.
"""
import json

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from db.db import save_vitals
from vitals.generator import stream_vitals, trigger_anomaly

router = APIRouter(prefix="/vitals", tags=["vitals"])


@router.get("/stream/{patient_id}")
async def vitals_stream(patient_id: str):
    async def event_generator():
        async for payload in stream_vitals(patient_id):
            doc = payload.model_dump()
            doc["timestamp"] = doc["timestamp"].isoformat()
            save_vitals({**doc})
            yield {"data": json.dumps(doc)}

    return EventSourceResponse(event_generator())


@router.post("/trigger-anomaly/{patient_id}")
async def trigger_anomaly_endpoint(patient_id: str):
    trigger_anomaly(patient_id)
    return {"status": "anomaly_triggered", "patient_id": patient_id, "duration_seconds": 30}
