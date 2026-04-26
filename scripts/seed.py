"""Seed all demo patients into MongoDB Atlas.

Run: python scripts/seed.py
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
import certifi
from pymongo import MongoClient

from db.db import DEMO_PATIENTS
from vitals.sources import SyntheticVitalsSource

load_dotenv()


def seed() -> None:
    client = MongoClient(os.environ["MONGODB_URI"], tlsCAFile=certifi.where())
    db = client[os.getenv("MONGODB_DB_NAME", "careflow")]

    source = SyntheticVitalsSource()

    for patient in DEMO_PATIENTS:
        pid = patient["patient_id"]

        db.patients.delete_many({"patient_id": pid})
        db.vitals_history.delete_many({"patient_id": pid})
        db.anomaly_events.delete_many({"patient_id": pid})

        db.patients.insert_one({**patient, "created_at": datetime.now(timezone.utc)})

        readings = []
        for _ in range(20):
            payload = source.next_vitals(pid)
            readings.append({**payload.model_dump(mode="python"), "saved_at": datetime.now(timezone.utc)})
            time.sleep(0.02)

        db.vitals_history.insert_many(readings)
        print(f"  Seeded {pid} ({patient['name']}) with {len(readings)} vitals readings.")

    db.vitals_history.create_index([("patient_id", 1), ("timestamp", -1)])
    db.anomaly_events.create_index([("patient_id", 1), ("detected_at", -1)])
    client.close()

    print(f"Done — seeded {len(DEMO_PATIENTS)} patients.")


if __name__ == "__main__":
    seed()
