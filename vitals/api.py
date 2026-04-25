"""FastAPI router: SSE vitals stream + demo trigger endpoint."""
from __future__ import annotations
import asyncio
import json
import os
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from vitals.generator import generate_vitals, trigger_anomaly

router = APIRouter()

DEMO_PATIENTS = ["patient-001", "patient-002", "patient-003"]


class TriggerRequest(BaseModel):
    patient_id: str = "patient-001"
    duration_seconds: int = 30


@router.post("/trigger-anomaly")
async def trigger_anomaly_endpoint(req: TriggerRequest):
    trigger_anomaly(req.duration_seconds)
    return {"status": "anomaly triggered", "patient_id": req.patient_id, "duration_seconds": req.duration_seconds}


async def _vitals_event_generator(patient_id: str) -> AsyncGenerator[str, None]:
    while True:
        payload = generate_vitals(patient_id)
        data = payload.model_dump_json()
        yield f"data: {data}\n\n"
        await asyncio.sleep(1.0)


@router.get("/vitals/stream/{patient_id}")
async def vitals_stream(patient_id: str):
    return StreamingResponse(
        _vitals_event_generator(patient_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/vitals/latest/{patient_id}")
async def latest_vitals(patient_id: str):
    return generate_vitals(patient_id)
