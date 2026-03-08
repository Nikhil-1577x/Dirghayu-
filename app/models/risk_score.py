"""
risk_score.py – Risk score Pydantic schemas.
"""
from pydantic import BaseModel
from app.utils.constants import RiskLevel


class RiskScoreOut(BaseModel):
    id: int
    patient_id: int
    score: float
    risk_level: RiskLevel
    timestamp: str

    class Config:
        from_attributes = True
