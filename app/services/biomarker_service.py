"""
biomarker_service.py – Biomarker CRUD + OCR-based ingestion.
"""
import logging
from typing import Optional

from app.utils.time_utils import utcnow_str
from app.utils.db_utils import execute, fetchall, fetchone, rows_to_dicts
from ai_modules.ocr_pipeline import run_ocr
from ai_modules.narrative import generate_summary

logger = logging.getLogger(__name__)


def add_biomarker(
    patient_id: int,
    biomarker_type: str,
    value: float,
    timestamp: Optional[str] = None,
) -> dict:
    ts = timestamp or utcnow_str()
    row_id = execute(
        """INSERT INTO biomarker_readings (patient_id, biomarker_type, value, timestamp)
           VALUES (?, ?, ?, ?)""",
        (patient_id, biomarker_type, value, ts),
    )
    logger.info("Biomarker added: patient=%d type=%s value=%s", patient_id, biomarker_type, value)
    return {"id": row_id, "patient_id": patient_id, "biomarker_type": biomarker_type, "value": value, "timestamp": ts}


def get_biomarkers(patient_id: int) -> list[dict]:
    rows = fetchall(
        "SELECT * FROM biomarker_readings WHERE patient_id = ? ORDER BY timestamp DESC",
        (patient_id,),
    )
    return rows_to_dicts(rows)


def get_latest_biomarkers(patient_id: int) -> dict:
    """Return latest reading per biomarker type."""
    rows = fetchall(
        """SELECT biomarker_type, value, timestamp
           FROM biomarker_readings
           WHERE patient_id = ?
           ORDER BY timestamp DESC""",
        (patient_id,),
    )
    seen: set = set()
    result: dict = {}
    for row in rows:
        bt = row["biomarker_type"]
        if bt not in seen:
            result[bt] = {"value": row["value"], "timestamp": row["timestamp"]}
            seen.add(bt)
    return result


def ingest_from_image(patient_id: int, image_path: str) -> list[dict]:
    """
    Run OCR on an image, parse biomarker results, persist them.
    Expected return from run_ocr: list of {"type": ..., "value": ..., "timestamp": ...}
    """
    results = run_ocr(image_path)
    added = []
    for item in results:
        btype = item.get("type", "unknown")
        value = float(item.get("value", 0.0))
        ts = item.get("timestamp", utcnow_str())
        record = add_biomarker(patient_id, btype, value, ts)
        added.append(record)
    logger.info("OCR ingestion for patient %d: %d records added", patient_id, len(added))
    return added


def build_biomarker_dict(patient_id: int) -> dict:
    """Build a flat dict of latest biomarkers for narrative generation."""
    latest = get_latest_biomarkers(patient_id)
    return {btype: data["value"] for btype, data in latest.items()}


def get_narrative(patient_id: int) -> str:
    """Generate an AI narrative summary for the biomarkers."""
    bio_dict = build_biomarker_dict(patient_id)
    if not bio_dict:
        return "No biomarker data available."
    return generate_summary(bio_dict)
