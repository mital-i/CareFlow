import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.schemas import AnomalyEvent, VitalsPayload, RiskAssessment, SeverityLevel, SafetyStatus
from risk.safety import evaluate_safety
from risk.classifier import classify_risk

class TestAISafety(unittest.TestCase):

    def setUp(self):
        self.vitals = VitalsPayload(
            patient_id="patient-001",
            heart_rate=150,
            spo2=92,
            hrv=15,
            device_id="test_watch_001"
        )
        self.anomaly_event = AnomalyEvent(
            anomaly_id="a1",
            patient_id="patient-001",
            signal_type="tachycardia",
            deviation_score=0.85,
            vitals_snapshot=self.vitals
        )
        self.assessment = RiskAssessment(
            patient_id="patient-001",
            risk_score=0.82,
            severity_level=SeverityLevel.HIGH,
            reasoning_context="Elevated heart rate and low HRV.",
            doctor_note="Immediate review.",
            anomaly_ref="a1"
        )

    @patch('httpx.post')
    def test_evaluate_safety_pass(self, mock_post):
        # Mock a successful safety pass from Gemma
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": json.dumps({
                "status": "PASS",
                "is_hallucination": False,
                "medical_alignment": True,
                "concerns": None
            })
        }
        mock_post.return_value = mock_response

        report = evaluate_safety(self.anomaly_event, self.assessment)
        
        self.assertEqual(report.status, SafetyStatus.PASS)
        self.assertFalse(report.is_hallucination)
        self.assertTrue(report.medical_alignment)
        self.assertIsNone(report.concerns)

    @patch('httpx.post')
    def test_evaluate_safety_fail_hallucination(self, mock_post):
        # Mock a failure due to hallucination
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": json.dumps({
                "status": "FAIL",
                "is_hallucination": True,
                "medical_alignment": True,
                "concerns": "Mentioned blood pressure which was not in the vitals."
            })
        }
        mock_post.return_value = mock_response

        report = evaluate_safety(self.anomaly_event, self.assessment)
        
        self.assertEqual(report.status, SafetyStatus.FAIL)
        self.assertTrue(report.is_hallucination)
        self.assertEqual(report.concerns, "Mentioned blood pressure which was not in the vitals.")

    @patch('httpx.post')
    def test_evaluate_safety_network_error(self, mock_post):
        # Mock a network error
        mock_post.side_effect = Exception("Connection refused")

        report = evaluate_safety(self.anomaly_event, self.assessment)
        
        self.assertEqual(report.status, SafetyStatus.UNCERTAIN)
        self.assertIn("Connection refused", report.concerns)

    @patch('risk.classifier._call_gemma')
    @patch('risk.classifier.evaluate_safety')
    def test_classify_risk_integration(self, mock_evaluate, mock_call_gemma):
        # Mock primary classification
        mock_call_gemma.return_value = {
            "risk_score": 0.5,
            "severity_level": "MEDIUM",
            "reasoning_context": "Mildly elevated.",
            "doctor_note": "Monitor closely."
        }
        # Mock safety evaluation
        mock_evaluate.return_value = MagicMock(status=SafetyStatus.PASS)

        final_assessment = classify_risk(self.anomaly_event)
        
        self.assertIsNotNone(final_assessment.safety_report)
        self.assertEqual(final_assessment.safety_report.status, SafetyStatus.PASS)
        mock_evaluate.assert_called_once()

if __name__ == "__main__":
    unittest.main()
