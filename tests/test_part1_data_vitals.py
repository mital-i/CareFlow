from datetime import datetime, timezone
from uuid import uuid4

from models.vitals import VitalsPayload


def test_vitals_payload_keeps_strict_public_schema():
    assert set(VitalsPayload.model_fields) == {
        "patient_id",
        "heart_rate",
        "spo2",
        "hrv",
        "timestamp",
        "device_id",
    }


def test_seed_generates_30_days_per_patient_with_multi_reading_anomalies():
    from scripts.seed import DEMO_PATIENTS, READINGS_PER_DAY, generate_vitals_history

    records = generate_vitals_history(DEMO_PATIENTS[0])
    assert len(records) == 30 * READINGS_PER_DAY
    assert sum(1 for record in records if record["anomaly_flagged"]) == 18
    assert all(record["timestamp"].tzinfo is not None for record in records)


def test_generator_normal_and_triggered_ranges():
    from vitals.generator import generate_one

    normal = generate_one("P001", in_anomaly=False)
    triggered = generate_one("P001", in_anomaly=True)

    assert 60 <= normal.heart_rate <= 90
    assert 97 <= normal.spo2 <= 100
    assert 40 <= normal.hrv <= 80
    assert triggered.heart_rate > normal.heart_rate
    assert triggered.hrv < normal.hrv


def test_melange_heuristic_emits_after_full_anomaly_buffer():
    from zetic.melange_agent import HeuristicBackend, MelangeAgent

    detector = MelangeAgent("P001", backend=HeuristicBackend(), cooldown_seconds=0)
    event = None
    for _ in range(10):
        event = detector.push_vitals(
            VitalsPayload(
                patient_id="P001",
                heart_rate=118,
                spo2=94.0,
                hrv=16,
                timestamp=datetime.now(timezone.utc),
                device_id="test-device",
            )
        )

    assert event is not None
    assert event.patient_id == "P001"
    assert event.deviation_score >= detector.threshold


def test_melange_cooldown_suppresses_duplicate_anomalies():
    from zetic.melange_agent import HeuristicBackend, MelangeAgent

    detector = MelangeAgent("P001", backend=HeuristicBackend(), cooldown_seconds=60)
    first = None
    second = None
    for _ in range(10):
        first = detector.push_vitals(
            VitalsPayload(patient_id="P001", heart_rate=118, spo2=94, hrv=16, device_id="test-device")
        )
    for _ in range(2):
        second = detector.push_vitals(
            VitalsPayload(patient_id="P001", heart_rate=120, spo2=94, hrv=15, device_id="test-device")
        )

    assert first is not None
    assert second is None


def test_db_normalize_doc_converts_uuid_and_iso_datetime():
    from db.db import normalize_doc

    doc = normalize_doc(
        {
            "assessment_id": uuid4(),
            "generated_at": "2026-04-24T12:00:00+00:00",
            "nested": {"action_id": uuid4()},
        }
    )

    assert isinstance(doc["assessment_id"], str)
    assert doc["generated_at"].tzinfo is not None
    assert isinstance(doc["nested"]["action_id"], str)


def test_flag_vitals_anomaly_updates_existing_reading(monkeypatch):
    import db.db as db_module

    calls = {}

    class FakeResult:
        modified_count = 1

    class FakeCollection:
        def update_one(self, query, update):
            calls["query"] = query
            calls["update"] = update
            return FakeResult()

    class FakeDB:
        vitals_history = FakeCollection()

    monkeypatch.setattr(db_module, "get_db", lambda: FakeDB())
    ts = datetime.now(timezone.utc)

    assert db_module.flag_vitals_anomaly("P001", ts, device_id="device-1") is True
    assert calls["query"]["patient_id"] == "P001"
    assert calls["query"]["device_id"] == "device-1"
    assert calls["update"] == {"$set": {"anomaly_flagged": True}}
