"""
SSE endpoint for live vitals streaming.
Mounted at /vitals/stream/{patient_id} by the FastAPI gateway (api/main.py).
Also exposes POST /trigger-anomaly for the demo harness.
"""
import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter

try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:
    from starlette.responses import StreamingResponse

    class EventSourceResponse(StreamingResponse):
        def __init__(self, content):
            async def encoded():
                async for event in content:
                    data = event.get("data", event)
                    yield f"data: {data}\n\n"

            super().__init__(encoded(), media_type="text/event-stream")

from db.db import get_latest_vitals, save_vitals
from vitals.generator import generate_one, trigger_anomaly

router = APIRouter(tags=["vitals"])


def _json_ready(doc: dict) -> dict:
    out = {key: value for key, value in doc.items() if key != "_id"}
    timestamp = out.get("timestamp")
    if isinstance(timestamp, datetime):
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        out["timestamp"] = timestamp.isoformat()
    return out


def _is_stale(doc: dict | None, max_age_seconds: int = 3) -> bool:
    if not doc:
        return True
    timestamp = doc.get("timestamp")
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if not isinstance(timestamp, datetime):
        return True
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)).total_seconds() > max_age_seconds


@router.get("/vitals/stream/{patient_id}")
async def vitals_stream(patient_id: str):
    async def event_generator():
        while True:
            doc = get_latest_vitals(patient_id)
            if _is_stale(doc):
                # Dev fallback: keeps the dashboard alive when Agent 1 is not running.
                payload = generate_one(patient_id)
                fallback_doc = payload.model_dump()
                fallback_doc["anomaly_flagged"] = False
                save_vitals(fallback_doc)
                doc = fallback_doc
            yield {"data": json.dumps(_json_ready(doc))}
            await asyncio.sleep(1.0)

    return EventSourceResponse(event_generator())


@router.post("/vitals/trigger-anomaly/{patient_id}")
async def trigger_anomaly_endpoint(patient_id: str):
    trigger = trigger_anomaly(patient_id)
    return {
        "status": "anomaly_triggered",
        "patient_id": patient_id,
        "duration_seconds": trigger["duration_seconds"],
        "triggered_until": _json_ready(trigger)["triggered_until"],
    }


@router.post("/trigger-anomaly")
async def trigger_anomaly_alias(patient_id: str = "P001"):
    return await trigger_anomaly_endpoint(patient_id)
