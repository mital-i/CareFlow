"""
Shared MongoDB utility used by all parts.
Import get_db() to access the database; use the helper functions below
rather than accessing collections directly, to keep the schema contract stable.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()

_client: Optional[MongoClient] = None
_indexes_ready = False


def _coerce_datetime(value: Any) -> Any:
    if not isinstance(value, (datetime, str)):
        return value
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _mongo_safe(value: Any) -> Any:
    """Convert Pydantic/UUID/nested values into Mongo-safe primitives."""
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return _coerce_datetime(value)
    if isinstance(value, dict):
        return {key: _mongo_safe(item) for key, item in value.items() if key != "_id"}
    if isinstance(value, list):
        return [_mongo_safe(item) for item in value]
    return value


_DATETIME_FIELDS = {
    "timestamp",
    "generated_at",
    "executed_at",
    "detected_at",
    "triggered_until",
    "created_at",
}


def _coerce_known_datetimes(doc: Any) -> Any:
    if isinstance(doc, dict):
        return {
            key: _coerce_datetime(value) if key in _DATETIME_FIELDS else _coerce_known_datetimes(value)
            for key, value in doc.items()
        }
    if isinstance(doc, list):
        return [_coerce_known_datetimes(item) for item in doc]
    return doc


def normalize_doc(doc: Any) -> Dict[str, Any]:
    return _coerce_known_datetimes(_mongo_safe(doc))


def get_db() -> Database:
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError(
                "MONGODB_URI is not set. Create /Users/student/CareFlow/.env from "
                ".env.example and set MONGODB_URI to your MongoDB Atlas connection string."
            )
        timeout_ms = int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000"))
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=timeout_ms,
            connectTimeoutMS=timeout_ms,
            tz_aware=True,
        )
    db_name = os.getenv("MONGODB_DB_NAME", "careflow")
    return _client[db_name]


def ping() -> bool:
    db = get_db()
    db.command("ping")
    return True


def ensure_indexes(force: bool = False) -> None:
    global _indexes_ready
    if _indexes_ready and not force:
        return
    db = get_db()
    db.patients.create_index("patient_id", unique=True)
    db.vitals_history.create_index([("patient_id", 1), ("timestamp", -1)])
    db.vitals_history.create_index([("patient_id", 1), ("anomaly_flagged", 1), ("timestamp", -1)])
    db.risk_assessments.create_index([("patient_id", 1), ("generated_at", -1)])
    db.action_logs.create_index([("patient_id", 1), ("executed_at", -1)])
    db.demo_triggers.create_index("patient_id", unique=True)
    db.demo_triggers.create_index("triggered_until", expireAfterSeconds=0)
    _indexes_ready = True


def setup_database() -> None:
    ping()
    ensure_indexes()


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
    doc = normalize_doc(vitals)
    doc["timestamp"] = _coerce_datetime(doc["timestamp"])
    doc.setdefault("anomaly_flagged", False)
    db.vitals_history.insert_one(doc)


def get_recent_vitals(patient_id: str, limit: int = 30) -> List[dict]:
    db = get_db()
    return list(
        db.vitals_history.find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
    )


def get_latest_vitals(patient_id: str) -> Optional[dict]:
    db = get_db()
    return db.vitals_history.find_one(
        {"patient_id": patient_id},
        {"_id": 0},
        sort=[("timestamp", -1)],
    )


def flag_vitals_anomaly(patient_id: str, timestamp: datetime | str, device_id: Optional[str] = None) -> bool:
    db = get_db()
    query: Dict[str, Any] = {
        "patient_id": patient_id,
        "timestamp": _coerce_datetime(timestamp),
    }
    if device_id:
        query["device_id"] = device_id
    result = db.vitals_history.update_one(query, {"$set": {"anomaly_flagged": True}})
    return result.modified_count > 0


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
    doc = normalize_doc(assessment)
    if "generated_at" in doc:
        doc["generated_at"] = _coerce_datetime(doc["generated_at"])
    db.risk_assessments.insert_one(doc)


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
    doc = normalize_doc(action)
    if "executed_at" in doc:
        doc["executed_at"] = _coerce_datetime(doc["executed_at"])
    db.action_logs.insert_one(doc)


def get_action_logs(patient_id: str, limit: int = 20) -> List[dict]:
    db = get_db()
    return list(
        db.action_logs.find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("executed_at", -1).limit(limit)
    )


# ── demo_triggers: internal cross-process anomaly controls ───────────────────

def set_demo_trigger(patient_id: str, duration_seconds: int = 30) -> dict:
    db = get_db()
    triggered_until = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)
    doc = {
        "patient_id": patient_id,
        "triggered_until": triggered_until,
        "duration_seconds": duration_seconds,
        "created_at": datetime.now(timezone.utc),
    }
    db.demo_triggers.update_one(
        {"patient_id": patient_id},
        {"$set": doc},
        upsert=True,
    )
    return doc


def get_demo_trigger(patient_id: str) -> Optional[dict]:
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = db.demo_triggers.find_one(
        {"patient_id": patient_id, "triggered_until": {"$gt": now}},
        {"_id": 0},
    )
    return doc


def is_demo_trigger_active(patient_id: str) -> bool:
    return get_demo_trigger(patient_id) is not None


def clear_expired_demo_triggers() -> None:
    db = get_db()
    db.demo_triggers.delete_many({"triggered_until": {"$lte": datetime.now(timezone.utc)}})
