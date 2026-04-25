from dataclasses import dataclass, field
from typing import List, Optional
from .schemas import Patient, VitalsHistory, NotificationPrefs


@dataclass
class PatientHistory:
    """Assembled context passed to the Gemini risk prompt."""
    patient: Patient
    recent_vitals: List[VitalsHistory] = field(default_factory=list)   # last 30
    recent_anomalies: List[VitalsHistory] = field(default_factory=list)  # last 5 flagged
    risk_trend: str = "stable"  # "trending_up" | "stable" | "trending_down"


@dataclass
class PatientPreferences:
    patient_id: str
    notification_sensitivity: str = "MEDIUM"
    preferred_channel: str = "push"
    do_not_disturb_hours: Optional[List[int]] = None
    emergency_contact: Optional[str] = None

    def can_receive_alert(self, current_hour: int) -> bool:
        if self.do_not_disturb_hours and current_hour in self.do_not_disturb_hours:
            return False
        return True
