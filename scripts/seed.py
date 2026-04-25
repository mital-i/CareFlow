"""
Run: python scripts/seed.py
Seeds 3 demo patients with 30 days of historical vitals including pre-seeded anomaly events.
Safe to re-run — drops and recreates collections each time.
"""
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from db.db import get_db

DEMO_PATIENTS = [
    {
        "patient_id": "P001",
        "name": "Margaret Chen",
        "age": 68,
        "conditions": ["atrial fibrillation", "hypertension"],
        "medications": ["metoprolol", "warfarin", "lisinopril"],
        "baseline_hr": 72.0,
        "baseline_spo2": 97.5,
        "baseline_hrv": 55.0,
        "notification_prefs": {
            "sensitivity": "HIGH",
            "preferred_channel": "push",
            "do_not_disturb_hours": [23, 0, 1, 2, 3, 4, 5],
            "emergency_contact": "+1-555-0101",
        },
    },
    {
        "patient_id": "P002",
        "name": "Robert Okafor",
        "age": 54,
        "conditions": ["type 2 diabetes", "coronary artery disease"],
        "medications": ["metformin", "atorvastatin", "aspirin"],
        "baseline_hr": 78.0,
        "baseline_spo2": 98.0,
        "baseline_hrv": 48.0,
        "notification_prefs": {
            "sensitivity": "MEDIUM",
            "preferred_channel": "push",
            "do_not_disturb_hours": [22, 23, 0, 1, 2, 3, 4, 5, 6],
            "emergency_contact": "+1-555-0202",
        },
    },
    {
        "patient_id": "P003",
        "name": "Amelia Torres",
        "age": 42,
        "conditions": ["post-operative recovery", "sleep apnea"],
        "medications": ["ibuprofen", "omeprazole"],
        "baseline_hr": 65.0,
        "baseline_spo2": 96.5,
        "baseline_hrv": 65.0,
        "notification_prefs": {
            "sensitivity": "LOW",
            "preferred_channel": "push",
            "do_not_disturb_hours": None,
            "emergency_contact": "+1-555-0303",
        },
    },
]


def _gaussian(mean: float, std: float, low: float, high: float) -> float:
    return max(low, min(high, random.gauss(mean, std)))


def generate_vitals_history(patient: dict, days: int = 30) -> list:
    records = []
    now = datetime.now(timezone.utc)
    interval_seconds = 300  # one reading every 5 min
    total_readings = days * 24 * (3600 // interval_seconds)

    anomaly_windows = set(random.sample(range(total_readings), k=5))

    for i in range(total_readings):
        ts = now - timedelta(seconds=i * interval_seconds)
        hour = ts.hour
        circadian_hr_offset = 5 * (1 - abs(hour - 14) / 14)

        in_anomaly = i in anomaly_windows
        hr = _gaussian(
            patient["baseline_hr"] + circadian_hr_offset + (25 if in_anomaly else 0),
            3.0, 40, 160
        )
        spo2 = _gaussian(
            patient["baseline_spo2"] - (3 if in_anomaly else 0),
            0.5, 88, 100
        )
        hrv = _gaussian(
            patient["baseline_hrv"] - (20 if in_anomaly else 0),
            5.0, 10, 120
        )

        records.append({
            "patient_id": patient["patient_id"],
            "timestamp": ts,
            "heart_rate": round(hr, 1),
            "spo2": round(spo2, 1),
            "hrv": round(hrv, 1),
            "device_id": f"zetic-{patient['patient_id'].lower()}-001",
            "anomaly_flagged": in_anomaly,
        })

    return records


def seed():
    db = get_db()

    print("Dropping existing collections...")
    db.patients.drop()
    db.vitals_history.drop()
    db.risk_assessments.drop()
    db.action_logs.drop()

    print("Inserting demo patients...")
    db.patients.insert_many(DEMO_PATIENTS)

    for patient in DEMO_PATIENTS:
        print(f"  Generating vitals for {patient['name']}...")
        records = generate_vitals_history(patient)
        db.vitals_history.insert_many(records)
        print(f"    Inserted {len(records)} readings")

    db.vitals_history.create_index([("patient_id", 1), ("timestamp", -1)])
    db.patients.create_index("patient_id", unique=True)
    db.risk_assessments.create_index([("patient_id", 1), ("generated_at", -1)])
    db.action_logs.create_index([("patient_id", 1), ("executed_at", -1)])

    print("\nSeed complete.")
    print(f"  Patients: {db.patients.count_documents({})}")
    print(f"  Vitals records: {db.vitals_history.count_documents({})}")


if __name__ == "__main__":
    seed()
