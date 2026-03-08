"""
alert_routes.py – Alert history endpoint.
"""
from fastapi import APIRouter
from app.services.alert_service import get_alert_history

router = APIRouter(prefix="/patient", tags=["Alerts"])


@router.get("/{id}/alerts")
def get_alerts(id: int):
    """Return full alert history for a patient."""
    return {"patient_id": id, "alerts": get_alert_history(id)}
