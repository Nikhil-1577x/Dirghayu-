"""
adherence_routes.py – Adherence endpoints.
"""
from fastapi import APIRouter

from app.services.adherence_engine import (
    get_daily_adherence,
    get_weekly_adherence,
    get_missed_doses,
)

router = APIRouter(prefix="/patient", tags=["Adherence"])


@router.get("/{id}/adherence")
def get_adherence(id: int):
    """
    Returns daily adherence, weekly score, and missed doses list.
    """
    daily = get_daily_adherence(id)
    weekly = get_weekly_adherence(id)
    missed = get_missed_doses(id)
    return {
        "patient_id": id,
        "daily_adherence": daily,
        "weekly_score": weekly["weekly_score"],
        "weekly_adherence": weekly,
        "missed_doses": missed,
    }
