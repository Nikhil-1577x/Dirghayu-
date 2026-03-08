"""
medication.py – Medication Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional


class MedicationCreate(BaseModel):
    patient_id: int
    name: str = Field(..., example="Metformin")
    dose: str = Field(..., example="500mg")
    schedule_time: str = Field(..., example="08:00")  # HH:MM


class MedicationOut(MedicationCreate):
    id: int

    class Config:
        from_attributes = True
