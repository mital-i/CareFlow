"""Convert BIDMC numerics CSV data into CareFlow replay vitals.

Example:
    python scripts/prepare_bidmc_replay.py \
      --input https://physionet.org/files/bidmc/1.0.0/bidmc_csv/bidmc_25_Numerics.csv \
      --output vitals/replays/bidmc_25_careflow.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import math
import statistics
import urllib.request
from collections import deque
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_INPUT_URL = "https://physionet.org/files/bidmc/1.0.0/bidmc_csv/bidmc_25_Numerics.csv"
DEFAULT_OUTPUT_PATH = "vitals/replays/bidmc_25_careflow.csv"
DEFAULT_PATIENT_ID = "patient-001"
DEFAULT_DEVICE_ID = "bidmc_monitor_001"
HRV_WINDOW_SECONDS = 30
ANOMALY_THRESHOLD = 0.65

OUTPUT_FIELDS = [
    "patient_id",
    "heart_rate",
    "spo2",
    "hrv",
    "device_id",
    "source_record",
    "time_offset_seconds",
    "anomaly_flagged",
]


def convert_bidmc_numerics(
    input_path_or_url: str,
    output_path: str | Path,
    patient_id: str = DEFAULT_PATIENT_ID,
    device_id: str = DEFAULT_DEVICE_ID,
    source_record: str | None = None,
) -> int:
    """Convert one BIDMC numerics CSV into normalized CareFlow replay rows."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    source_record = source_record or _source_record_name(input_path_or_url)

    recent_hr: deque[float] = deque(maxlen=HRV_WINDOW_SECONDS)
    rows_written = 0

    with _open_text(input_path_or_url) as handle, output.open("w", newline="", encoding="utf-8") as out:
        reader = csv.DictReader(handle, skipinitialspace=True)
        writer = csv.DictWriter(out, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()

        for row in reader:
            heart_rate = _parse_float(row.get("HR"))
            spo2 = _parse_float(row.get("SpO2"))
            if heart_rate is None or spo2 is None:
                continue

            previous_hr = list(recent_hr)
            recent_hr.append(heart_rate)
            hrv = calculate_hrv_proxy(recent_hr)
            anomaly_flagged = should_flag_anomaly(heart_rate, spo2, hrv, previous_hr)

            writer.writerow(
                {
                    "patient_id": patient_id,
                    "heart_rate": int(round(heart_rate)),
                    "spo2": int(round(spo2)),
                    "hrv": hrv,
                    "device_id": device_id,
                    "source_record": source_record,
                    "time_offset_seconds": _clean_time(row.get("Time [s]")),
                    "anomaly_flagged": str(anomaly_flagged).lower(),
                }
            )
            rows_written += 1

    if rows_written == 0:
        raise ValueError(f"No usable HR/SpO2 rows found in {input_path_or_url}")
    return rows_written


def calculate_hrv_proxy(recent_hr: deque[float] | list[float]) -> int:
    """Map rolling HR variability to a bounded demo HRV value.

    This is intentionally a replay/demo proxy, not a clinical HRV measure.
    """
    if len(recent_hr) < HRV_WINDOW_SECONDS:
        return 55

    stddev = statistics.pstdev(recent_hr)
    return _bounded_int(80 - (stddev * 10), 10, 80)


def should_flag_anomaly(
    heart_rate: float,
    spo2: float,
    hrv: int,
    previous_hr: list[float],
) -> bool:
    return calculate_demo_deviation_score(heart_rate, spo2, hrv, previous_hr) >= ANOMALY_THRESHOLD


def calculate_demo_deviation_score(
    heart_rate: float,
    spo2: float,
    hrv: int,
    previous_hr: list[float],
) -> float:
    """Mirror the deterministic fallback score used by zetic.melange_agent."""
    score = 0.0
    if heart_rate > 120:
        score += 0.45
    if spo2 < 95:
        score += 0.25
    if hrv < 30:
        score += 0.25
    if previous_hr:
        avg_hr = sum(previous_hr) / len(previous_hr)
        if heart_rate - avg_hr > 25:
            score += 0.15
    return round(min(score, 1.0), 4)


def _open_text(path_or_url: str):
    parsed = urlparse(path_or_url)
    if parsed.scheme in {"http", "https"}:
        response = urllib.request.urlopen(path_or_url)
        return io.TextIOWrapper(response, encoding="utf-8", newline="")
    return Path(path_or_url).open(newline="", encoding="utf-8")


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if math.isnan(parsed):
        return None
    return parsed


def _clean_time(value: str | None) -> str:
    parsed = _parse_float(value)
    if parsed is None:
        return ""
    if parsed.is_integer():
        return str(int(parsed))
    return str(parsed)


def _source_record_name(path_or_url: str) -> str:
    parsed = urlparse(path_or_url)
    name = Path(parsed.path or path_or_url).name
    return name.replace("_Numerics.csv", "").replace(".csv", "") or "bidmc"


def _bounded_int(value: float, low: int, high: int) -> int:
    return int(round(min(high, max(low, value))))


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a BIDMC numerics CSV for CareFlow replay mode.")
    parser.add_argument("--input", default=DEFAULT_INPUT_URL, help="Local BIDMC numerics CSV path or URL.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH, help="Output CareFlow replay CSV path.")
    parser.add_argument("--patient-id", default=DEFAULT_PATIENT_ID)
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID)
    parser.add_argument("--source-record", default=None)
    args = parser.parse_args()

    rows = convert_bidmc_numerics(
        input_path_or_url=args.input,
        output_path=args.output,
        patient_id=args.patient_id,
        device_id=args.device_id,
        source_record=args.source_record,
    )
    print(f"Wrote {rows} replay rows to {args.output}")


if __name__ == "__main__":
    main()
