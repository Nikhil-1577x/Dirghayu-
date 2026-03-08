"""
dose_event.py – Dose event Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from app.utils.constants import DoseStatus, DoseSource


class DoseEventCreate(BaseModel):
    patient_id: int
    medication_id: int
    timestamp: str = Field(..., example="2026-03-08T08:05:00Z")
    status: DoseStatus
    source: DoseSource = DoseSource.ESP32


class DoseEventOut(DoseEventCreate):
    id: int

    class Config:
        from_attributes = True


class MQTTDosePayload(BaseModel):
    """Payload received from ESP32 over MQTT."""
    patient_id: int
    medication_id: int
    timestamp: str
    event: str = Field(..., example="taken")
