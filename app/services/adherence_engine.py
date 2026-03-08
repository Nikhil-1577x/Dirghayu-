"""
adherence_engine.py – Core adherence classification logic.

Rules:
  TAKEN  – dose taken within ±30 min of scheduled time
  LATE   – dose taken within 2 hours of scheduled time
  MISSED – no dose after 2 hours of scheduled time

Drug holiday – no activity for 18 hours → URGENT alert.
Weekly score  – (taken / total) * 100
"""
import logging
from datetime import timedelta
from typing import Optional

from app.utils.constants import (
    DoseStatus, DoseSource,
    TAKEN_WINDOW_MINUTES, LATE_WINDOW_MINUTES, DRUG_HOLIDAY_HOURS,
    WEEKLY_WINDOW_DAYS,
)
from app.utils.time_utils import (
    utcnow, utcnow_str, parse_iso,
    scheduled_datetime_today, week_start_utc,
)
from app.utils.db_utils import execute, fetchall, fetchone, rows_to_dicts

logger = logging.getLogger(__name__)


def classify_dose(medication_id: int, event_timestamp: str) -> DoseStatus:
    """
    Retrieve the scheduled time for medication_id and classify the dose event.
    """
    row = fetchone("SELECT schedule_time FROM medications WHERE id = ?", (medication_id,))
    if row is None:
        logger.warning("medication %d not found – classifying as LATE", medication_id)
        return DoseStatus.LATE

    scheduled_dt = scheduled_datetime_today(row["schedule_time"])
    event_dt = parse_iso(event_timestamp)

    delta_minutes = abs((event_dt - scheduled_dt).total_seconds()) / 60

    if delta_minutes <= TAKEN_WINDOW_MINUTES:
        return DoseStatus.TAKEN
    elif delta_minutes <= LATE_WINDOW_MINUTES:
        return DoseStatus.LATE
    else:
        return DoseStatus.MISSED


def record_dose_event(
    patient_id: int,
    medication_id: int,
    timestamp: str,
    status: DoseStatus,
    source: DoseSource = DoseSource.ESP32,
) -> int:
    """Insert a dose event into the DB and return its id."""
    row_id = execute(
        """INSERT INTO dose_events (patient_id, medication_id, timestamp, status, source)
           VALUES (?, ?, ?, ?, ?)""",
        (patient_id, medication_id, timestamp, status.value, source.value),
    )
    logger.info(
        "DoseEvent recorded: patient=%d med=%d status=%s source=%s id=%d",
        patient_id, medication_id, status.value, source.value, row_id,
    )
    return row_id


def check_drug_holiday(patient_id: int) -> bool:
    """
    Return True if the patient has had no dose activity in DRUG_HOLIDAY_HOURS.
    """
    cutoff = (utcnow() - timedelta(hours=DRUG_HOLIDAY_HOURS)).isoformat()
    row = fetchone(
        "SELECT id FROM dose_events WHERE patient_id = ? AND timestamp > ? LIMIT 1",
        (patient_id, cutoff),
    )
    return row is None


def get_weekly_adherence(patient_id: int) -> dict:
    """
    Compute adherence for the current 7-day window.
    Returns dict with taken, total, missed, score.
    """
    since = week_start_utc().isoformat()
    rows = fetchall(
        "SELECT status FROM dose_events WHERE patient_id = ? AND timestamp >= ?",
        (patient_id, since),
    )
    total = len(rows)
    taken = sum(1 for r in rows if r["status"] == DoseStatus.TAKEN.value)
    missed = sum(1 for r in rows if r["status"] == DoseStatus.MISSED.value)
    score = round((taken / total) * 100, 2) if total > 0 else 0.0
    return {"taken": taken, "missed": missed, "total": total, "weekly_score": score}


def get_daily_adherence(patient_id: int) -> dict:
    """Compute adherence for today."""
    from app.utils.time_utils import today_start_utc
    since = today_start_utc().isoformat()
    rows = fetchall(
        "SELECT status FROM dose_events WHERE patient_id = ? AND timestamp >= ?",
        (patient_id, since),
    )
    total = len(rows)
    taken = sum(1 for r in rows if r["status"] == DoseStatus.TAKEN.value)
    missed = sum(1 for r in rows if r["status"] == DoseStatus.MISSED.value)
    score = round((taken / total) * 100, 2) if total > 0 else 0.0
    return {"taken": taken, "missed": missed, "total": total, "daily_score": score}


def get_missed_doses(patient_id: int) -> list[dict]:
    """Return all MISSED dose events for this patient."""
    rows = fetchall(
        "SELECT * FROM dose_events WHERE patient_id = ? AND status = 'MISSED' ORDER BY timestamp DESC",
        (patient_id,),
    )
    return rows_to_dicts(rows)
