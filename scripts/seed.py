"""Seed demo patients into MongoDB Atlas.

Run:  python scripts/seed.py
"""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient

PATIENTS = [
    {
        "patient_id": "patient-001",
        "name": "Margaret Chen",
        "age": 67,
        "conditions": ["Atrial Fibrillation", "Hypertension"],
        "medications": ["Metoprolol 25mg", "Lisinopril 10mg", "Warfarin 5mg"],
        "baseline_hr": 72,
        "baseline_spo2": 98.5,
        "baseline_hrv": 58,
        "notification_prefs": {"channel": "push", "sensitivity": "HIGH"},
    },
    {
        "patient_id": "patient-002",
        "name": "Robert Okafor",
        "age": 54,
        "conditions": ["Type 2 Diabetes", "Coronary Artery Disease"],
        "medications": ["Metformin 500mg", "Atorvastatin 40mg", "Aspirin 81mg"],
        "baseline_hr": 68,
        "baseline_spo2": 97.8,
        "baseline_hrv": 62,
        "notification_prefs": {"channel": "push", "sensitivity": "MEDIUM"},
    },
    {
        "patient_id": "patient-003",
        "name": "Sofia Ramirez",
        "age": 71,
        "conditions": ["COPD", "Post-op Cardiac Recovery"],
        "medications": ["Tiotropium 18mcg", "Prednisone 5mg", "Furosemide 20mg"],
        "baseline_hr": 78,
        "baseline_spo2": 96.5,
        "baseline_hrv": 44,
        "notification_prefs": {"channel": "voice", "sensitivity": "HIGH"},
    },
]


def seed():
    client = MongoClient(os.environ["MONGODB_URI"])
    db = client[os.getenv("MONGODB_DB_NAME", "careflow")]

    db.patients.drop()
    result = db.patients.insert_many(PATIENTS)
    print(f"Seeded {len(result.inserted_ids)} patients")

    db.vitals.create_index([("patient_id", 1), ("saved_at", -1)])
    db.assessments.create_index([("patient_id", 1), ("generated_at", -1)])
    print("Indexes created")
    client.close()


if __name__ == "__main__":
    seed()
