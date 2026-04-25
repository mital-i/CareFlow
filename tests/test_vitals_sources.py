from __future__ import annotations

import csv
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from vitals.sources import ReplayVitalsSource, SyntheticVitalsSource, create_vitals_source


class SyntheticVitalsSourceTest(unittest.TestCase):
    def test_normal_vitals_stay_within_existing_bounds(self) -> None:
        source = SyntheticVitalsSource(device_id="test-device")

        readings = [source.next_vitals("patient-001") for _ in range(5)]

        for reading in readings:
            self.assertGreaterEqual(reading.heart_rate, 45)
            self.assertLessEqual(reading.heart_rate, 170)
            self.assertGreaterEqual(reading.spo2, 85)
            self.assertLessEqual(reading.spo2, 100)
            self.assertGreaterEqual(reading.hrv, 5)
            self.assertLessEqual(reading.hrv, 90)
            self.assertEqual(reading.device_id, "test-device")

    def test_trigger_anomaly_produces_stressed_vitals(self) -> None:
        source = SyntheticVitalsSource()

        result = source.trigger_anomaly("patient-001", duration_seconds=10)
        reading = source.next_vitals("patient-001")

        self.assertEqual(result["status"], "triggered")
        self.assertTrue(source.is_anomaly_active("patient-001"))
        self.assertGreaterEqual(reading.heart_rate, 120)
        self.assertLessEqual(reading.spo2, 95)
        self.assertLessEqual(reading.hrv, 30)


class ReplayVitalsSourceTest(unittest.TestCase):
    def test_replay_loads_rows_and_uses_live_timestamps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_replay_csv(Path(tmp) / "replay.csv")
            source = ReplayVitalsSource(path, loop=True)

            before = datetime.now(timezone.utc)
            reading = source.next_vitals("patient-001")
            after = datetime.now(timezone.utc)

            self.assertEqual(reading.heart_rate, 70)
            self.assertEqual(reading.spo2, 98)
            self.assertEqual(reading.hrv, 55)
            self.assertEqual(reading.device_id, "device-a")
            self.assertGreaterEqual(reading.timestamp, before)
            self.assertLessEqual(reading.timestamp, after)

    def test_replay_loops_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_replay_csv(Path(tmp) / "replay.csv")
            source = ReplayVitalsSource(path, loop=True)

            self.assertEqual(source.next_vitals("patient-001").heart_rate, 70)
            self.assertEqual(source.next_vitals("patient-001").heart_rate, 130)
            self.assertEqual(source.next_vitals("patient-001").heart_rate, 70)

    def test_replay_maintains_separate_patient_cursors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_replay_csv(Path(tmp) / "replay.csv")
            source = ReplayVitalsSource(path, loop=True)

            self.assertEqual(source.next_vitals("patient-001").heart_rate, 70)
            self.assertEqual(source.next_vitals("patient-002").heart_rate, 80)
            self.assertEqual(source.next_vitals("patient-001").heart_rate, 130)

    def test_trigger_anomaly_jumps_to_first_flagged_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_replay_csv(Path(tmp) / "replay.csv")
            source = ReplayVitalsSource(path, loop=True)

            result = source.trigger_anomaly("patient-001")
            reading = source.next_vitals("patient-001")

            self.assertEqual(result["status"], "triggered")
            self.assertTrue(reading.anomaly_flagged)
            self.assertEqual(reading.heart_rate, 130)

    def test_factory_defaults_to_synthetic(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsInstance(create_vitals_source(), SyntheticVitalsSource)

    def test_factory_selects_replay_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_replay_csv(Path(tmp) / "replay.csv")
            with patch.dict(os.environ, {"VITALS_SOURCE": "replay", "VITALS_REPLAY_PATH": str(path)}):
                self.assertIsInstance(create_vitals_source(), ReplayVitalsSource)

    def test_factory_rejects_unknown_source(self) -> None:
        with patch.dict(os.environ, {"VITALS_SOURCE": "banana"}):
            with self.assertRaises(ValueError):
                create_vitals_source()

    @staticmethod
    def _write_replay_csv(path: Path) -> Path:
        rows = [
            {
                "patient_id": "patient-001",
                "heart_rate": "70",
                "spo2": "98",
                "hrv": "55",
                "device_id": "device-a",
                "source_record": "unit",
                "time_offset_seconds": "0",
                "anomaly_flagged": "false",
            },
            {
                "patient_id": "patient-001",
                "heart_rate": "130",
                "spo2": "94",
                "hrv": "25",
                "device_id": "device-a",
                "source_record": "unit",
                "time_offset_seconds": "1",
                "anomaly_flagged": "true",
            },
            {
                "patient_id": "patient-002",
                "heart_rate": "80",
                "spo2": "97",
                "hrv": "50",
                "device_id": "device-b",
                "source_record": "unit",
                "time_offset_seconds": "0",
                "anomaly_flagged": "false",
            },
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return path


if __name__ == "__main__":
    unittest.main()
