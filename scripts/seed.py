"""Seed CareFlow demo data.

Run: python3 scripts/seed.py

Safe to re-run: drops and recreates demo collections each time.
"""
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from db.db import ensure_indexes, get_db
from models.schemas import Patient, VitalsHistory

RANDOM_SEED = 20260424
INTERVAL_SECONDS = 300
READINGS_PER_DAY = 24 * (3600 // INTERVAL_SECONDS)

DEMO_PATIENTS_RAW = [
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
        "baseline_spo2": 97.0,
        "baseline_hrv": 65.0,
        "notification_prefs": {
            "sensitivity": "LOW",
            "preferred_channel": "push",
            "do_not_disturb_hours": None,
            "emergency_contact": "+1-555-0303",
        },
    },
]

DEMO_PATIENTS = [patient.model_dump(mode="json") for patient in [Patient(**p) for p in DEMO_PATIENTS_RAW]]


def _gaussian(mean: float, std: float, low: float, high: float) -> float:
    return max(low, min(high, random.gauss(mean, std)))


def _circadian_hr_offset(hour: int) -> float:
    # Peak in the afternoon, lower overnight.
    return 4.0 * (1 - abs(hour - 14) / 14)


def _anomaly_indices(total_readings: int) -> set[int]:
    """Return deterministic multi-reading anomaly windows across the 30-day span."""
    episode_starts = [
        READINGS_PER_DAY * 4 + 72,
        READINGS_PER_DAY * 13 + 144,
        READINGS_PER_DAY * 24 + 210,
    ]
    indices: set[int] = set()
    for start in episode_starts:
        for offset in range(6):  # 30 minutes at 5-minute intervals
            if start + offset < total_readings:
                indices.add(start + offset)
    return indices


def generate_vitals_history(patient: dict, days: int = 30) -> list:
    records = []
    now = datetime.now(timezone.utc)
    total_readings = days * READINGS_PER_DAY
    anomaly_windows = _anomaly_indices(total_readings)

    for i in range(total_readings):
        ts = now - timedelta(seconds=(total_readings - i) * INTERVAL_SECONDS)
        hour = ts.hour

        in_anomaly = i in anomaly_windows
        hr = _gaussian(
            patient["baseline_hr"] + _circadian_hr_offset(hour) + (30 if in_anomaly else 0),
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

        record = {
            "patient_id": patient["patient_id"],
            "timestamp": ts,
            "heart_rate": round(hr, 1),
            "spo2": round(spo2, 1),
            "hrv": round(hrv, 1),
            "device_id": f"zetic-{patient['patient_id'].lower()}-001",
            "anomaly_flagged": in_anomaly,
        }
        records.append(VitalsHistory(**record).model_dump())

    return records


def seed():
    random.seed(RANDOM_SEED)
    db = get_db()

    print("Dropping existing collections...")
    db.patients.drop()
    db.vitals_history.drop()
    db.risk_assessments.drop()
    db.action_logs.drop()
    db.demo_triggers.drop()

    print("Inserting demo patients...")
    db.patients.insert_many(DEMO_PATIENTS)

    for patient in DEMO_PATIENTS:
        print(f"  Generating vitals for {patient['name']}...")
        records = generate_vitals_history(patient)
        db.vitals_history.insert_many(records)
        print(f"    Inserted {len(records)} readings")

    ensure_indexes(force=True)

    print("\nSeed complete.")
    print(f"  Patients: {db.patients.count_documents({})}")
    print(f"  Vitals records: {db.vitals_history.count_documents({})}")
    print(f"  Anomaly records: {db.vitals_history.count_documents({'anomaly_flagged': True})}")


if __name__ == "__main__":
    seed()
