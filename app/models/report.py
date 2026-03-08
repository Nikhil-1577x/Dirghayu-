"""
report.py – Report Pydantic schemas.
"""
from pydantic import BaseModel


class ReportOut(BaseModel):
    id: int
    patient_id: int
    file_path: str
    created_at: str

    class Config:
        from_attributes = True
