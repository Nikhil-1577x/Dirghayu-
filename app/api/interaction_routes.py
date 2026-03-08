"""
interaction_routes.py – Drug interaction checker API (GAP 3).

POST /patient/{id}/medications/check-interactions
  Body: {"medications": ["Metformin", "Amlodipine", "Alcohol"]}
  Response: list of interaction objects with severity + clinical note
  Side effect: SEVERE interactions trigger a doctor WhatsApp alert
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.db_utils import fetchone
from app.services.drug_interaction_service import check_interactions, trigger_severe_alerts

router = APIRouter()


class InteractionCheckRequest(BaseModel):
    medications: list[str]


@router.post("/patient/{patient_id}/medications/check-interactions")
def check_drug_interactions(patient_id: int, body: InteractionCheckRequest):
    """
    Check the provided medication list against the drug_interactions table.
    SEVERE interactions will also trigger a doctor WhatsApp alert.
    """
    # Validate patient exists
    patient = fetchone("SELECT id, name FROM patients WHERE id = ?", (patient_id,))
    if patient is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    if not body.medications:
        return {"patient_id": patient_id, "interactions": [], "total": 0}

    interactions = check_interactions(body.medications)

    # Trigger doctor alert for any SEVERE findings
    if interactions:
        trigger_severe_alerts(patient_id, interactions)

    severe_count   = sum(1 for i in interactions if i["severity"] == "SEVERE")
    moderate_count = sum(1 for i in interactions if i["severity"] == "MODERATE")

    return {
        "patient_id":     patient_id,
        "patient_name":   patient["name"],
        "medications_checked": body.medications,
        "total":          len(interactions),
        "severe_count":   severe_count,
        "moderate_count": moderate_count,
        "interactions":   interactions,
        "alert_sent":     severe_count > 0,
    }


@router.get("/patient/{patient_id}/environment")
def get_environment_readings(patient_id: int, limit: int = 50):
    """Return recent DHT22 temperature/humidity readings for a patient."""
    patient = fetchone("SELECT id FROM patients WHERE id = ?", (patient_id,))
    if patient is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    from app.services.environment_service import get_environment_readings
    readings = get_environment_readings(patient_id, limit)
    return {"patient_id": patient_id, "readings": readings, "total": len(readings)}


@router.get("/drug-interactions")
def list_drug_interactions():
    """Return all seeded drug interactions from the CDSCO database."""
    from app.utils.db_utils import fetchall, rows_to_dicts
    rows = fetchall("SELECT * FROM drug_interactions ORDER BY severity, drug_a")
    return {"interactions": rows_to_dicts(rows), "total": len(rows)}
