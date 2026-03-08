"""
alert_log.py – Alert log Pydantic schemas.
"""
from pydantic import BaseModel
from app.utils.constants import AlertType


class AlertLogOut(BaseModel):
    id: int
    patient_id: int
    alert_type: AlertType
    message: str
    sent_to: str
    timestamp: str

    class Config:
        from_attributes = True
