from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

import certifi
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.database import Database

from models.vitals import AnomalyEvent, VitalsPayload

load_dotenv()

DEMO_PATIENTS = [
    {
        "patient_id": "patient-001",
        "name": "Margaret Chen",
        "age": 67,
        "conditions": ["Atrial Fibrillation", "Hypertension"],
        "baseline_hr": 72,
        "baseline_spo2": 98.5,
        "baseline_hrv": 58,
        "device_id": "careflow_watch_001",
    },
    {
        "patient_id": "patient-002",
        "name": "Robert Okafor",
        "age": 54,
        "conditions": ["Type 2 Diabetes", "Coronary Artery Disease"],
        "baseline_hr": 68,
        "baseline_spo2": 97.8,
        "baseline_hrv": 62,
        "device_id": "careflow_watch_002",
    },
    {
        "patient_id": "patient-003",
        "name": "Sofia Ramirez",
        "age": 71,
        "conditions": ["COPD", "Post-op Cardiac Recovery"],
        "baseline_hr": 78,
        "baseline_spo2": 96.5,
        "baseline_hrv": 44,
        "device_id": "careflow_watch_003",
    },
]

DEMO_PATIENT = DEMO_PATIENTS[0]

_async_client: Optional[AsyncIOMotorClient] = None
_sync_client: Optional[MongoClient] = None


def get_async_db():
    global _async_client
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise RuntimeError("MONGODB_URI is not configured")

    if _async_client is None:
        _async_client = AsyncIOMotorClient(
            mongodb_uri,
            serverSelectionTimeoutMS=int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000")),
            tlsCAFile=certifi.where(),
        )
    return _async_client[os.getenv("MONGODB_DB_NAME", "careflow")]


def get_sync_db() -> Database:
    global _sync_client
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise RuntimeError("MONGODB_URI is not configured")

    if _sync_client is None:
        _sync_client = MongoClient(
            mongodb_uri,
            serverSelectionTimeoutMS=int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000")),
            tlsCAFile=certifi.where(),
        )
    return _sync_client[os.getenv("MONGODB_DB_NAME", "careflow")]


def get_db() -> Database:
    return get_sync_db()


def _dump_model(model) -> dict:
    return model.model_dump(mode="python")


def save_vitals(payload: VitalsPayload) -> None:
    db = get_db()
    doc = _dump_model(payload)
    doc["saved_at"] = datetime.now(timezone.utc)
    db.vitals_history.insert_one(doc)


def save_anomaly(event: AnomalyEvent) -> None:
    db = get_db()
    doc = _dump_model(event)
    doc["saved_at"] = datetime.now(timezone.utc)
    db.anomaly_events.insert_one(doc)


async def save_assessment(assessment: dict) -> None:
    db = get_async_db()
    await db.assessments.insert_one({**assessment, "saved_at": datetime.now(timezone.utc)})


def get_latest_vitals(patient_id: str) -> Optional[VitalsPayload]:
    db = get_db()
    doc = db.vitals_history.find_one(
        {"patient_id": patient_id},
        sort=[("timestamp", -1)],
    )
    if not doc:
        return None
    doc.pop("_id", None)
    return VitalsPayload.model_validate(doc)


def seed_demo_patient_if_missing() -> None:
    db = get_db()
    for patient in DEMO_PATIENTS:
        if not db.patients.find_one({"patient_id": patient["patient_id"]}):
            db.patients.insert_one({**patient, "created_at": datetime.now(timezone.utc)})


def get_patient(patient_id: str) -> Optional[dict]:
    db = get_db()
    doc = db.patients.find_one({"patient_id": patient_id}, {"_id": 0})
    return doc


def get_all_patients_sync() -> list[dict]:
    db = get_db()
    return list(db.patients.find({}, {"_id": 0}))


async def get_all_patients() -> list[dict]:
    return get_all_patients_sync()
