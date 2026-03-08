"""
biomarker.py – Biomarker reading Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional


class BiomarkerCreate(BaseModel):
    patient_id: int
    biomarker_type: str = Field(..., example="blood_glucose")
    value: float = Field(..., example=95.5)
    timestamp: Optional[str] = None   # defaults to NOW in service


class BiomarkerOut(BiomarkerCreate):
    id: int
    timestamp: str

    class Config:
        from_attributes = True
