"""FastAPI router for live vitals, local edge detection, and demo triggers."""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from db.db import save_vitals
from vitals.sources import get_vitals_source
from zetic.melange_agent import ZeticAnomalyDetector

router = APIRouter()
detector = ZeticAnomalyDetector()


class TriggerRequest(BaseModel):
    patient_id: str = "patient-001"
    duration_seconds: int = 30


def _json_event(event_type: str, data) -> str:
    return json.dumps(
        {
            "type": event_type,
            "data": data.model_dump(mode="json"),
        }
    )


@router.get("/health")
async def data_edge_health():
    return {"status": "ok", "service": "careflow-data-edge"}


@router.post("/trigger-anomaly")
async def trigger_anomaly_endpoint(req: TriggerRequest):
    return get_vitals_source().trigger_anomaly(req.patient_id, req.duration_seconds)


@router.get("/vitals/current/{patient_id}")
async def current_vitals(patient_id: str):
    return get_vitals_source().next_vitals(patient_id)


@router.get("/vitals/latest/{patient_id}")
async def latest_vitals(patient_id: str):
    return await current_vitals(patient_id)


async def _vitals_event_generator(patient_id: str) -> AsyncGenerator[dict, None]:
    while True:
        payload = get_vitals_source().next_vitals(patient_id)
        anomaly = detector.add_vitals(payload)

        try:
            save_vitals(payload)
        except Exception as exc:
            print(f"[Mongo] vitals save skipped: {exc}")

        yield {"data": _json_event("vitals", payload)}

        if anomaly:
            yield {"event": "anomaly", "data": _json_event("anomaly", anomaly)}

        await asyncio.sleep(1.0)


@router.get("/vitals/stream/{patient_id}")
async def vitals_stream(patient_id: str):
    return EventSourceResponse(
        _vitals_event_generator(patient_id),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
