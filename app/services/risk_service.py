"""
risk_service.py – Compute and persist patient risk scores.
"""
import logging
from typing import Optional

from app.utils.constants import RiskLevel
from app.utils.time_utils import utcnow_str
from app.utils.db_utils import execute, fetchone, fetchall, rows_to_dicts

from ai_modules.predict import predict_risk

logger = logging.getLogger(__name__)


def _score_to_level(score: float) -> RiskLevel:
    if score >= 85:
        return RiskLevel.CRITICAL
    elif score >= 70:
        return RiskLevel.HIGH
    elif score >= 40:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.LOW


def _build_patient_features(patient_id: int) -> dict:
    """
    Gather features from DB to pass to the ML model.
    """
    from app.services.adherence_engine import get_weekly_adherence
    adherence = get_weekly_adherence(patient_id)

    # Latest biomarkers (last 7 days)
    biomarkers = fetchall(
        """SELECT biomarker_type, value FROM biomarker_readings
           WHERE patient_id = ?
           ORDER BY timestamp DESC LIMIT 20""",
        (patient_id,),
    )
    bio_dict: dict = {}
    for row in biomarkers:
        bio_dict.setdefault(row["biomarker_type"], []).append(row["value"])

    patient = fetchone("SELECT age, gender FROM patients WHERE id = ?", (patient_id,))
    age = patient["age"] if patient else 50
    gender = patient["gender"] if patient else "unknown"

    return {
        "patient_id": patient_id,
        "age": age,
        "gender": gender,
        "weekly_adherence": adherence["weekly_score"],
        "total_missed": adherence["missed"],
        **{f"avg_{k}": (sum(v) / len(v)) for k, v in bio_dict.items()},
    }


def compute_and_store_risk(patient_id: int) -> dict:
    """
    Run ML prediction, persist result, return the risk dict.
    """
    features = _build_patient_features(patient_id)
    score: float = predict_risk(features)
    level = _score_to_level(score)
    ts = utcnow_str()

    row_id = execute(
        "INSERT INTO risk_scores (patient_id, score, risk_level, timestamp) VALUES (?, ?, ?, ?)",
        (patient_id, score, level.value, ts),
    )
    logger.info("Risk computed for patient %d: score=%.1f level=%s", patient_id, score, level.value)
    return {"id": row_id, "patient_id": patient_id, "score": score, "risk_level": level.value, "timestamp": ts}


def get_latest_risk(patient_id: int) -> Optional[dict]:
    """Return the most recent risk score for a patient."""
    row = fetchone(
        "SELECT * FROM risk_scores WHERE patient_id = ? ORDER BY timestamp DESC LIMIT 1",
        (patient_id,),
    )
    if row is None:
        return None
    return dict(row)
