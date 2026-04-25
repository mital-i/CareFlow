"""
Shared MongoDB utility used by all parts.
Import get_db() to access the database; use the helper functions below
rather than accessing collections directly, to keep the schema contract stable.
"""
import os
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()

_client: Optional[MongoClient] = None


def get_db() -> Database:
    global _client
    if _client is None:
        uri = os.environ["MONGODB_URI"]
        _client = MongoClient(uri)
    db_name = os.getenv("MONGODB_DB_NAME", "careflow")
    return _client[db_name]


# ── patients ──────────────────────────────────────────────────────────────────

def get_patient(patient_id: str) -> Optional[dict]:
    db = get_db()
    return db.patients.find_one({"patient_id": patient_id}, {"_id": 0})


def list_patients() -> List[dict]:
    db = get_db()
    return list(db.patients.find({}, {"_id": 0}))


# ── vitals_history ────────────────────────────────────────────────────────────

def save_vitals(vitals: dict) -> None:
    db = get_db()
    db.vitals_history.insert_one(vitals)


def get_recent_vitals(patient_id: str, limit: int = 30) -> List[dict]:
    db = get_db()
    return list(
        db.vitals_history.find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
    )


def get_recent_anomalies(patient_id: str, limit: int = 5) -> List[dict]:
    db = get_db()
    return list(
        db.vitals_history.find(
            {"patient_id": patient_id, "anomaly_flagged": True},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
    )


# ── risk_assessments ──────────────────────────────────────────────────────────

def save_risk_assessment(assessment: dict) -> None:
    db = get_db()
    db.risk_assessments.insert_one(assessment)


def get_recent_risk_scores(patient_id: str, limit: int = 10) -> List[float]:
    db = get_db()
    docs = list(
        db.risk_assessments.find(
            {"patient_id": patient_id},
            {"risk_score": 1, "_id": 0}
        ).sort("generated_at", -1).limit(limit)
    )
    return [d["risk_score"] for d in docs]


def get_latest_risk_assessment(patient_id: str) -> Optional[dict]:
    db = get_db()
    return db.risk_assessments.find_one(
        {"patient_id": patient_id},
        {"_id": 0},
        sort=[("generated_at", -1)]
    )


# ── action_logs ───────────────────────────────────────────────────────────────

def save_action_log(action: dict) -> None:
    db = get_db()
    db.action_logs.insert_one(action)


def get_action_logs(patient_id: str, limit: int = 20) -> List[dict]:
    db = get_db()
    return list(
        db.action_logs.find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("executed_at", -1).limit(limit)
    )
