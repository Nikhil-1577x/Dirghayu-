"""
patient.py – Patient Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional


class PatientCreate(BaseModel):
    name: str = Field(..., example="John Doe")
    age: int = Field(..., ge=0, le=120)
    gender: str = Field(..., example="male")
    phone: str = Field(..., example="+1234567890")
    family_phone: Optional[str] = Field(None, example="+0987654321")
    doctor_phone: Optional[str] = Field(None, example="+1122334455")


class PatientOut(PatientCreate):
    id: int
    created_at: str

    class Config:
        from_attributes = True
