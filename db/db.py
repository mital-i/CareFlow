from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

_async_client: Optional[AsyncIOMotorClient] = None
_sync_client: Optional[MongoClient] = None


def get_async_db():
    global _async_client
    if _async_client is None:
        _async_client = AsyncIOMotorClient(
            os.environ["MONGODB_URI"],
            serverSelectionTimeoutMS=int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000")),
        )
    return _async_client[os.getenv("MONGODB_DB_NAME", "careflow")]


def get_sync_db():
    global _sync_client
    if _sync_client is None:
        _sync_client = MongoClient(
            os.environ["MONGODB_URI"],
            serverSelectionTimeoutMS=int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000")),
        )
    return _sync_client[os.getenv("MONGODB_DB_NAME", "careflow")]


async def save_vitals(payload: dict) -> None:
    db = get_async_db()
    await db.vitals.insert_one({**payload, "saved_at": datetime.now(timezone.utc)})


async def save_anomaly(event: dict) -> None:
    db = get_async_db()
    await db.vitals.update_one(
        {"patient_id": event["patient_id"]},
        {"$set": {"latest_anomaly": event, "anomaly_flagged": True}},
        upsert=True,
    )


async def save_assessment(assessment: dict) -> None:
    db = get_async_db()
    await db.assessments.insert_one({**assessment, "saved_at": datetime.now(timezone.utc)})


async def get_patient(patient_id: str) -> Optional[dict]:
    db = get_async_db()
    return await db.patients.find_one({"patient_id": patient_id}, {"_id": 0})


async def get_all_patients() -> list[dict]:
    db = get_async_db()
    cursor = db.patients.find({}, {"_id": 0})
    return await cursor.to_list(length=100)


def get_all_patients_sync() -> list[dict]:
    db = get_sync_db()
    return list(db.patients.find({}, {"_id": 0}))
