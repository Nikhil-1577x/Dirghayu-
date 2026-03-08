"""
predict.py – Stub for ML risk prediction model.

In production, replace with a trained scikit-learn/XGBoost/TensorFlow model.

Input:  dict of patient features
Output: float risk score in range [0, 100]
"""
import logging
import math

logger = logging.getLogger(__name__)


def predict_risk(patient_features: dict) -> float:
    """
    Predict the risk score for a patient.

    Args:
        patient_features: dict containing:
            - patient_id (int)
            - age (int)
            - gender (str)
            - weekly_adherence (float): percentage 0-100
            - total_missed (int)
            - avg_blood_glucose (float, optional)
            - avg_blood_pressure (float, optional)
            - ... other biomarker averages

    Returns:
        float: risk score in range 0.0 – 100.0
    """
    logger.debug("predict_risk called for patient %s", patient_features.get("patient_id"))

    # ── STUB heuristic model ────────────────────────────────────────────────
    # Replace with: joblib.load("model.pkl").predict([feature_vector])[0]

    adherence = patient_features.get("weekly_adherence", 100.0)
    missed = patient_features.get("total_missed", 0)
    age = patient_features.get("age", 50)
    glucose = patient_features.get("avg_blood_glucose", 100.0)

    # Base risk from missed doses and adherence
    base_risk = max(0.0, 100.0 - adherence)

    # Age factor contribution
    age_factor = max(0.0, (age - 40) * 0.3) if age > 40 else 0.0

    # Glucose anomaly (normal < 100 mg/dL fasting)
    glucose_penalty = max(0.0, (glucose - 100) * 0.2) if glucose > 100 else 0.0

    # Missed dose penalty
    missed_penalty = missed * 2.5

    raw_score = base_risk + age_factor + glucose_penalty + missed_penalty
    score = round(min(100.0, raw_score), 2)

    logger.info("Risk score computed: %.1f for patient %s", score, patient_features.get("patient_id"))
    return score
