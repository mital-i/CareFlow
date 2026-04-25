from __future__ import annotations

import csv
import tempfile
import unittest
from collections import deque
from pathlib import Path

from scripts.prepare_bidmc_replay import (
    calculate_demo_deviation_score,
    calculate_hrv_proxy,
    convert_bidmc_numerics,
    should_flag_anomaly,
)


class PrepareBidmcReplayTest(unittest.TestCase):
    def test_converts_bidmc_csv_and_skips_nan_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "bidmc_99_Numerics.csv"
            output = Path(tmp) / "careflow.csv"
            self._write_bidmc_csv(source)

            rows_written = convert_bidmc_numerics(
                input_path_or_url=str(source),
                output_path=output,
                patient_id="patient-001",
                device_id="device-001",
            )

            rows = self._read_output(output)
            self.assertEqual(rows_written, 32)
            self.assertEqual(len(rows), 32)
            self.assertEqual(rows[0]["patient_id"], "patient-001")
            self.assertEqual(rows[0]["device_id"], "device-001")
            self.assertEqual(rows[0]["source_record"], "bidmc_99")
            self.assertEqual(rows[0]["heart_rate"], "70")
            self.assertEqual(rows[0]["spo2"], "98")
            self.assertEqual(rows[0]["hrv"], "55")
            self.assertEqual(rows[-1]["anomaly_flagged"], "true")

    def test_hrv_proxy_is_bounded(self) -> None:
        steady = deque([70.0] * 30, maxlen=30)
        volatile = deque([60.0, 100.0] * 15, maxlen=30)

        self.assertEqual(calculate_hrv_proxy(deque([70.0] * 10, maxlen=30)), 55)
        self.assertEqual(calculate_hrv_proxy(steady), 80)
        self.assertGreaterEqual(calculate_hrv_proxy(volatile), 10)
        self.assertLessEqual(calculate_hrv_proxy(volatile), 80)

    def test_anomaly_flag_rules_match_demo_thresholds(self) -> None:
        self.assertEqual(calculate_demo_deviation_score(130, 94, 25, [80, 81, 82]), 1.0)
        self.assertTrue(should_flag_anomaly(130, 94, 25, [80, 81, 82]))
        self.assertTrue(should_flag_anomaly(130, 98, 25, [80, 81, 82]))
        self.assertTrue(should_flag_anomaly(130, 94, 55, [80, 81, 82]))
        self.assertFalse(should_flag_anomaly(121, 98, 55, [80, 81, 82]))
        self.assertFalse(should_flag_anomaly(90, 94, 55, [80, 81, 82]))
        self.assertFalse(should_flag_anomaly(90, 98, 29, [80, 81, 82]))
        self.assertFalse(should_flag_anomaly(90, 98, 55, [88, 89, 90]))

    @staticmethod
    def _write_bidmc_csv(path: Path) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["Time [s]", "HR", "PULSE", "RESP", "SpO2"])
            writer.writeheader()
            for second in range(30):
                writer.writerow(
                    {
                        "Time [s]": str(second),
                        "HR": str(70 + (second % 2)),
                        "PULSE": str(70 + (second % 2)),
                        "RESP": "20",
                        "SpO2": "98",
                    }
                )
            writer.writerow({"Time [s]": "30", "HR": "NaN", "PULSE": "NaN", "RESP": "20", "SpO2": "98"})
            writer.writerow({"Time [s]": "31", "HR": "130", "PULSE": "130", "RESP": "20", "SpO2": "94"})
            writer.writerow({"Time [s]": "32", "HR": "131", "PULSE": "131", "RESP": "20", "SpO2": "94"})

    @staticmethod
    def _read_output(path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
