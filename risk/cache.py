"""In-memory cache for the last 5 risk assessments per patient."""
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from models.schemas import RiskAssessmentDoc

_cache: Dict[str, Deque[RiskAssessmentDoc]] = defaultdict(lambda: deque(maxlen=5))


def cache_assessment(assessment: RiskAssessmentDoc) -> None:
    _cache[assessment.patient_id].appendleft(assessment)


def get_cached(patient_id: str) -> Optional[RiskAssessmentDoc]:
    q = _cache.get(patient_id)
    if q:
        return q[0]
    return None


def get_all_cached(patient_id: str) -> list:
    return list(_cache.get(patient_id, []))
