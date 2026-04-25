"""Seed Person 1 demo data into MongoDB Atlas.

Run: python scripts/seed.py
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from pymongo import MongoClient

from db.db import DEMO_PATIENT
from vitals.generator import generate_next_vitals

load_dotenv()


def seed() -> None:
    patient_id = os.getenv("DEFAULT_PATIENT_ID", "patient-001")
    client = MongoClient(os.environ["MONGODB_URI"])
    db = client[os.getenv("MONGODB_DB_NAME", "careflow")]

    db.patients.delete_many({"patient_id": patient_id})
    db.vitals_history.delete_many({"patient_id": patient_id})
    db.anomaly_events.delete_many({"patient_id": patient_id})

    db.patients.insert_one(
        {**DEMO_PATIENT, "patient_id": patient_id, "created_at": datetime.now(timezone.utc)}
    )

    readings = []
    for _ in range(20):
        payload = generate_next_vitals(patient_id)
        readings.append({**payload.model_dump(mode="python"), "saved_at": datetime.now(timezone.utc)})
        time.sleep(0.02)

    db.vitals_history.insert_many(readings)
    db.vitals_history.create_index([("patient_id", 1), ("timestamp", -1)])
    db.anomaly_events.create_index([("patient_id", 1), ("detected_at", -1)])
    client.close()

    print(f"Seeded CareFlow demo patient {patient_id} with {len(readings)} normal vitals readings.")


if __name__ == "__main__":
    seed()
