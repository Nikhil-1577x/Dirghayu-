"""
risk_service_routes.py – Risk score endpoint.
We embed this in patient_routes but expose also as a standalone.
"""
from fastapi import APIRouter, HTTPException
from app.services.risk_service import compute_and_store_risk, get_latest_risk

router = APIRouter(prefix="/patient", tags=["Risk"])


@router.get("/{id}/risk")
def get_risk_score(id: int):
    """Return the latest risk prediction for a patient. Computes if none exists."""
    risk = get_latest_risk(id)
    if risk is None:
        # Compute on-demand for first call
        try:
            risk = compute_and_store_risk(id)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
    return {"patient_id": id, **risk}


@router.post("/{id}/risk/compute")
def trigger_risk_computation(id: int):
    """Force recompute risk score."""
    try:
        risk = compute_and_store_risk(id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"patient_id": id, **risk}
