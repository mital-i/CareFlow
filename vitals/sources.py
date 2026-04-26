"""Configurable vitals sources for synthetic and replay-backed streams."""
from __future__ import annotations

import csv
import math
import os
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from models.vitals import VitalsPayload

DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", os.getenv("DEMO_PATIENT_ID", "patient-001"))
DEVICE_ID = os.getenv("DEVICE_ID", "careflow_watch_001")
ANOMALY_DURATION_SECONDS = 30
RECOVERY_SECONDS = 18
DEFAULT_REPLAY_PATH = "vitals/replays/bidmc_25_careflow.csv"

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class VitalsSource(ABC):
    """Common interface for anything that can provide live-ish vitals."""

    source_name: str

    @property
    def supports_anomaly_trigger(self) -> bool:
        return False

    @abstractmethod
    def next_vitals(self, patient_id: str) -> VitalsPayload:
        """Return the next reading for a patient."""

    def trigger_anomaly(
        self,
        patient_id: str = DEFAULT_PATIENT_ID,
        duration_seconds: int = ANOMALY_DURATION_SECONDS,
    ) -> dict:
        return {
            "status": "unsupported",
            "patient_id": patient_id,
            "source": self.source_name,
            "message": f"{self.source_name} does not support anomaly injection",
        }

    def is_anomaly_active(self, patient_id: str) -> bool:
        return False


@dataclass
class PatientVitalsState:
    heart_rate: float = 74.0
    spo2: float = 98.0
    hrv: float = 55.0
    anomaly_until: float = 0.0
    recovery_started_at: float = 0.0
    baseline_hr: float = 74.0
    baseline_spo2: float = 98.5
    baseline_hrv: float = 55.0


def _patient_baselines(patient_id: str) -> tuple[float, float, float]:
    from db.db import DEMO_PATIENTS
    for p in DEMO_PATIENTS:
        if p["patient_id"] == patient_id:
            return p["baseline_hr"], p["baseline_spo2"], p["baseline_hrv"]
    return 74.0, 98.5, 55.0


class SyntheticVitalsSource(VitalsSource):
    source_name = "synthetic"

    def __init__(self, device_id: str = DEVICE_ID) -> None:
        self.device_id = device_id
        self._states: dict[str, PatientVitalsState] = {}

    @property
    def supports_anomaly_trigger(self) -> bool:
        return True

    def _state_for(self, patient_id: str) -> PatientVitalsState:
        if patient_id not in self._states:
            bhr, bspo2, bhrv = _patient_baselines(patient_id)
            self._states[patient_id] = PatientVitalsState(
                heart_rate=bhr,
                spo2=bspo2,
                hrv=bhrv,
                baseline_hr=bhr,
                baseline_spo2=bspo2,
                baseline_hrv=bhrv,
            )
        return self._states[patient_id]

    @staticmethod
    def _organic_wave(now: float, period: float, amplitude: float) -> float:
        return amplitude * math.sin(2 * math.pi * now / period)

    @staticmethod
    def _bounded_int(value: float, low: int, high: int) -> int:
        return int(round(min(high, max(low, value))))

    def is_anomaly_active(self, patient_id: str) -> bool:
        return time.time() < self._state_for(patient_id).anomaly_until

    def trigger_anomaly(
        self,
        patient_id: str = DEFAULT_PATIENT_ID,
        duration_seconds: int = ANOMALY_DURATION_SECONDS,
    ) -> dict:
        if isinstance(patient_id, int):
            duration_seconds = patient_id
            patient_id = DEFAULT_PATIENT_ID

        state = self._state_for(patient_id)
        state.anomaly_until = time.time() + duration_seconds
        state.recovery_started_at = 0.0
        return {
            "status": "triggered",
            "patient_id": patient_id,
            "source": self.source_name,
            "message": f"Anomaly mode active for {duration_seconds} seconds",
        }

    def _target_values(self, patient_id: str, now: float) -> tuple[float, float, float, float]:
        state = self._state_for(patient_id)

        if now < state.anomaly_until:
            state.recovery_started_at = 0.0
            return (
                random.uniform(125, 155),
                random.uniform(91, 95),
                random.uniform(10, 24),
                1.0,
            )

        if state.anomaly_until > 0:
            if state.recovery_started_at == 0.0:
                state.recovery_started_at = now
            elapsed = now - state.recovery_started_at
            if elapsed < RECOVERY_SECONDS:
                recovery = elapsed / RECOVERY_SECONDS
                return (
                    140 - (64 * recovery) + random.uniform(-2, 2),
                    93 + (5 * recovery) + random.uniform(-0.3, 0.3),
                    18 + (37 * recovery) + random.uniform(-2, 2),
                    0.28,
                )
            state.anomaly_until = 0.0
            state.recovery_started_at = 0.0

        return (
            state.baseline_hr + self._organic_wave(now, 31, 4) + random.uniform(-3, 3),
            state.baseline_spo2 + self._organic_wave(now, 43, 0.5) + random.uniform(-0.4, 0.4),
            state.baseline_hrv + self._organic_wave(now, 37, 6) + random.uniform(-5, 5),
            0.35,
        )

    def next_vitals(self, patient_id: str) -> VitalsPayload:
        state = self._state_for(patient_id)
        now = time.time()
        target_hr, target_spo2, target_hrv, smoothing = self._target_values(patient_id, now)

        state.heart_rate += (target_hr - state.heart_rate) * smoothing
        state.spo2 += (target_spo2 - state.spo2) * smoothing
        state.hrv += (target_hrv - state.hrv) * smoothing

        return VitalsPayload(
            patient_id=patient_id,
            timestamp=datetime.now(timezone.utc),
            heart_rate=self._bounded_int(state.heart_rate, 45, 170),
            spo2=self._bounded_int(state.spo2, 85, 100),
            hrv=self._bounded_int(state.hrv, 5, 90),
            device_id=self.device_id,
        )


@dataclass(frozen=True)
class ReplayVitalsRow:
    patient_id: str
    heart_rate: int
    spo2: int
    hrv: int
    device_id: str
    anomaly_flagged: bool = False


class ReplayVitalsSource(VitalsSource):
    source_name = "replay"

    def __init__(self, path: str | Path, loop: bool = True) -> None:
        self.path = _resolve_path(path)
        self.loop = loop
        self._rows_by_patient = self._load_rows(self.path)
        self._cursors: dict[str, int] = {patient_id: 0 for patient_id in self._rows_by_patient}

    @property
    def supports_anomaly_trigger(self) -> bool:
        return any(row.anomaly_flagged for rows in self._rows_by_patient.values() for row in rows)

    def _load_rows(self, path: Path) -> dict[str, list[ReplayVitalsRow]]:
        if not path.exists():
            raise FileNotFoundError(
                f"Replay vitals file not found: {path}. "
                "Prepare one with scripts/prepare_bidmc_replay.py or set VITALS_REPLAY_PATH."
            )

        rows_by_patient: dict[str, list[ReplayVitalsRow]] = {}
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, skipinitialspace=True)
            for line_number, row in enumerate(reader, start=2):
                replay_row = self._parse_row(row, line_number)
                rows_by_patient.setdefault(replay_row.patient_id, []).append(replay_row)

        if not rows_by_patient:
            raise ValueError(f"Replay vitals file has no usable rows: {path}")
        return rows_by_patient

    @staticmethod
    def _parse_row(row: dict[str, str], line_number: int) -> ReplayVitalsRow:
        required_columns = ["patient_id", "heart_rate", "spo2", "hrv"]
        for column in required_columns:
            if column not in row:
                raise ValueError(f"Missing required replay CSV column: {column}")

        try:
            patient_id = (row["patient_id"] or "").strip()
            heart_rate = int(round(float(row["heart_rate"])))
            spo2 = int(round(float(row["spo2"])))
            hrv = int(round(float(row["hrv"])))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid numeric value in replay CSV line {line_number}") from exc

        if not patient_id:
            raise ValueError(f"Missing patient_id in replay CSV line {line_number}")

        return ReplayVitalsRow(
            patient_id=patient_id,
            heart_rate=_bounded_int(heart_rate, 30, 220),
            spo2=_bounded_int(spo2, 50, 100),
            hrv=_bounded_int(hrv, 1, 200),
            device_id=(row.get("device_id") or DEVICE_ID).strip() or DEVICE_ID,
            anomaly_flagged=_parse_bool(row.get("anomaly_flagged", "false")),
        )

    def _rows_for(self, patient_id: str) -> list[ReplayVitalsRow]:
        if patient_id not in self._rows_by_patient:
            available = ", ".join(sorted(self._rows_by_patient))
            raise KeyError(f"Patient {patient_id} is not present in replay file. Available: {available}")
        return self._rows_by_patient[patient_id]

    def next_vitals(self, patient_id: str) -> VitalsPayload:
        rows = self._rows_for(patient_id)
        cursor = self._cursors.get(patient_id, 0)

        if cursor >= len(rows):
            cursor = 0 if self.loop else len(rows) - 1

        row = rows[cursor]
        next_cursor = cursor + 1
        self._cursors[patient_id] = 0 if self.loop and next_cursor >= len(rows) else next_cursor

        return VitalsPayload(
            patient_id=patient_id,
            timestamp=datetime.now(timezone.utc),
            heart_rate=row.heart_rate,
            spo2=row.spo2,
            hrv=row.hrv,
            device_id=row.device_id,
            anomaly_flagged=row.anomaly_flagged,
        )

    def trigger_anomaly(
        self,
        patient_id: str = DEFAULT_PATIENT_ID,
        duration_seconds: int = ANOMALY_DURATION_SECONDS,
    ) -> dict:
        rows = self._rows_for(patient_id)
        for index, row in enumerate(rows):
            if row.anomaly_flagged:
                self._cursors[patient_id] = index
                return {
                    "status": "triggered",
                    "patient_id": patient_id,
                    "source": self.source_name,
                    "message": "Replay cursor moved to first flagged anomaly row",
                }

        return {
            "status": "unsupported",
            "patient_id": patient_id,
            "source": self.source_name,
            "message": "Replay file has no rows with anomaly_flagged=true",
        }


_source: VitalsSource | None = None


def create_vitals_source(source_name: str | None = None) -> VitalsSource:
    configured = (source_name or os.getenv("VITALS_SOURCE", "synthetic")).strip().lower()

    if configured == "synthetic":
        return SyntheticVitalsSource(device_id=os.getenv("DEVICE_ID", DEVICE_ID))

    if configured == "replay":
        path = os.getenv("VITALS_REPLAY_PATH", DEFAULT_REPLAY_PATH)
        loop = _parse_bool(os.getenv("VITALS_REPLAY_LOOP", "true"))
        return ReplayVitalsSource(path=path, loop=loop)

    raise ValueError(
        f"Unsupported VITALS_SOURCE={configured!r}. Expected 'synthetic' or 'replay'."
    )


def get_vitals_source(refresh: bool = False) -> VitalsSource:
    global _source
    if refresh or _source is None:
        _source = create_vitals_source()
    return _source


def reset_vitals_source() -> None:
    global _source
    _source = None


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def _parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _bounded_int(value: float, low: int, high: int) -> int:
    return int(round(min(high, max(low, value))))
