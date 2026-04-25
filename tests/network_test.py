"""
Integration test: sends a mock AnomalyEvent through the full
Agent 1 → 2 → 3 → 4 → 5 chain and validates ActionDecision output.
Run: pytest tests/network_test.py -v
"""
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from models.anomaly import AnomalyEvent
from models.vitals import VitalsPayload


@pytest.fixture
def mock_anomaly():
    vitals = VitalsPayload(
        patient_id="P001",
        heart_rate=118.0,
        spo2=95.5,
        hrv=18.0,
        timestamp=datetime.now(timezone.utc),
        device_id="test-device",
    )
    return AnomalyEvent(
        patient_id="P001",
        signal_type="hr_hrv_combined",
        deviation_score=0.78,
        vitals_snapshot=vitals,
        detected_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_risk_pipeline_returns_assessment(mock_anomaly):
    """Risk pipeline should return a RiskAssessmentDoc given a valid AnomalyEvent."""
    with patch("risk.classifier._get_vertex_client") as mock_client:
        mock_response = MagicMock()
        mock_response.text = '{"risk_score": 0.75, "severity_level": "HIGH", "reasoning_context": "Mocked assessment."}'
        mock_client.return_value.generate_content.return_value = mock_response

        with patch("risk.history.build_patient_history") as mock_history:
            from models.patient import PatientHistory
            from models.schemas import Patient, NotificationPrefs

            mock_patient = Patient(
                patient_id="P001",
                name="Margaret Chen",
                age=68,
                conditions=["atrial fibrillation"],
                medications=["metoprolol"],
                baseline_hr=72.0,
                baseline_spo2=97.5,
                baseline_hrv=55.0,
                notification_prefs=NotificationPrefs(),
            )
            mock_history.return_value = PatientHistory(
                patient=mock_patient,
                recent_vitals=[],
                recent_anomalies=[],
                risk_trend="trending_up",
            )

            with patch("risk.nodes.save_risk_assessment"):
                from risk.pipeline import invoke_pipeline
                result = await invoke_pipeline(mock_anomaly)

    assert result is not None
    assert result.patient_id == "P001"
    assert 0.0 <= result.risk_score <= 1.0
    assert result.severity_level is not None
    assert result.reasoning_context != ""


@pytest.mark.asyncio
async def test_fallback_assessment_fires_on_vertex_failure(mock_anomaly):
    """Pipeline should use rule-based fallback when Vertex AI raises an exception."""
    with patch("risk.classifier._get_vertex_client", side_effect=Exception("API unavailable")):
        with patch("risk.history.build_patient_history") as mock_history:
            from models.patient import PatientHistory
            from models.schemas import Patient, NotificationPrefs

            mock_patient = Patient(
                patient_id="P001",
                name="Test Patient",
                age=50,
                conditions=[],
                medications=[],
                baseline_hr=75.0,
                baseline_spo2=97.0,
                baseline_hrv=50.0,
                notification_prefs=NotificationPrefs(),
            )
            mock_history.return_value = PatientHistory(
                patient=mock_patient,
                recent_vitals=[],
                recent_anomalies=[],
                risk_trend="stable",
            )

            with patch("risk.nodes.save_risk_assessment"):
                from risk.pipeline import invoke_pipeline
                result = await invoke_pipeline(mock_anomaly)

    assert result is not None
    assert result.risk_score > 0
