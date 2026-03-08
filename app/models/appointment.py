"""
appointment.py – Appointment Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional


class AppointmentCreate(BaseModel):
    patient_id: int
    appointment_time: str = Field(..., example="2026-03-15T10:00:00")
    doctor_name: str = Field(..., example="Dr. Smith")
    notes: Optional[str] = None


class AppointmentOut(AppointmentCreate):
    id: int

    class Config:
        from_attributes = True
