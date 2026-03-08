"""
report_service.py – Generate PDF doctor report with ReportLab.

Report contents:
  - Patient info
  - Adherence statistics (daily + weekly)
  - Biomarker trend summary
  - Risk score + level
  - AI narrative explanation
  - Behavioral notes
"""
import logging
import os
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.config import settings
from app.utils.time_utils import utcnow_str
from app.utils.db_utils import execute, fetchone, fetchall, rows_to_dicts

logger = logging.getLogger(__name__)


def _ensure_reports_dir() -> Path:
    p = Path(settings.REPORTS_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def generate_report(patient_id: int) -> str:
    """
    Build a comprehensive PDF report and return the file path.
    """
    from app.services.adherence_engine import get_daily_adherence, get_weekly_adherence
    from app.services.biomarker_service import get_latest_biomarkers, get_narrative
    from app.services.risk_service import get_latest_risk

    patient = fetchone("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if patient is None:
        raise ValueError(f"Patient {patient_id} not found")

    patient = dict(patient)
    daily = get_daily_adherence(patient_id)
    weekly = get_weekly_adherence(patient_id)
    biomarkers = get_latest_biomarkers(patient_id)
    risk = get_latest_risk(patient_id) or {"score": 0, "risk_level": "N/A", "timestamp": "N/A"}
    narrative = get_narrative(patient_id)
    medications = rows_to_dicts(fetchall("SELECT * FROM medications WHERE patient_id = ?", (patient_id,)))
    appointments = rows_to_dicts(fetchall(
        "SELECT * FROM appointments WHERE patient_id = ? ORDER BY appointment_time ASC",
        (patient_id,),
    ))

    # ── File path ───────────────────────────────────────────────────────────
    reports_dir = _ensure_reports_dir()
    ts_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{patient_id}_{ts_str}.pdf"
    filepath = reports_dir / filename

    # ── Build PDF ───────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=18, spaceAfter=6, alignment=TA_CENTER)
    h2_style = ParagraphStyle("H2Style", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=4, textColor=colors.HexColor("#1E3A5F"))
    body_style = styles["BodyText"]
    risk_color = {
        "LOW": colors.green,
        "MODERATE": colors.orange,
        "HIGH": colors.red,
        "CRITICAL": colors.darkred,
    }.get(risk["risk_level"], colors.black)

    story = []

    # Title
    story.append(Paragraph("Smart Medication Adherence System", title_style))
    story.append(Paragraph("Doctor Report", ParagraphStyle("sub", parent=styles["Normal"], fontSize=11, alignment=TA_CENTER, textColor=colors.grey)))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1E3A5F")))
    story.append(Spacer(1, 0.3 * cm))

    # Patient Info
    story.append(Paragraph("Patient Information", h2_style))
    patient_data = [
        ["Name", patient["name"]],
        ["Age", str(patient["age"])],
        ["Gender", patient["gender"]],
        ["Phone", patient["phone"]],
        ["Family Phone", patient.get("family_phone") or "—"],
    ]
    story.append(_build_table(patient_data))
    story.append(Spacer(1, 0.4 * cm))

    # Adherence Stats
    story.append(Paragraph("Adherence Statistics", h2_style))
    adh_data = [
        ["Metric", "Value"],
        ["Today – Taken", f"{daily['taken']} / {daily['total']}"],
        ["Today – Missed", str(daily["missed"])],
        ["Daily Score", f"{daily['daily_score']:.1f}%"],
        ["Weekly Taken", f"{weekly['taken']} / {weekly['total']}"],
        ["Weekly Missed", str(weekly["missed"])],
        ["Weekly Score", f"{weekly['weekly_score']:.1f}%"],
    ]
    story.append(_build_table(adh_data, has_header=True))
    story.append(Spacer(1, 0.4 * cm))

    # Risk Score
    story.append(Paragraph("Risk Assessment", h2_style))
    risk_data = [
        ["Risk Score", f"{risk['score']:.1f}"],
        ["Risk Level", risk["risk_level"]],
        ["Computed At", risk["timestamp"]],
    ]
    story.append(_build_table(risk_data))
    story.append(Spacer(1, 0.4 * cm))

    # Biomarkers
    if biomarkers:
        story.append(Paragraph("Latest Biomarkers", h2_style))
        bio_data = [["Biomarker", "Value", "Timestamp"]]
        for btype, data in biomarkers.items():
            bio_data.append([btype, str(data["value"]), data["timestamp"]])
        story.append(_build_table(bio_data, has_header=True))
        story.append(Spacer(1, 0.4 * cm))

    # AI Narrative
    story.append(Paragraph("AI Clinical Narrative", h2_style))
    story.append(Paragraph(narrative, body_style))
    story.append(Spacer(1, 0.4 * cm))

    # Medications
    if medications:
        story.append(Paragraph("Prescribed Medications", h2_style))
        med_data = [["Medication", "Dose", "Scheduled"]]
        for m in medications:
            med_data.append([m["name"], m["dose"], m["schedule_time"]])
        story.append(_build_table(med_data, has_header=True))
        story.append(Spacer(1, 0.4 * cm))

    # Upcoming appointments
    if appointments:
        story.append(Paragraph("Upcoming Appointments", h2_style))
        appt_data = [["Date/Time", "Doctor", "Notes"]]
        for a in appointments:
            appt_data.append([a["appointment_time"], a["doctor_name"], a.get("notes") or "—"])
        story.append(_build_table(appt_data, has_header=True))
        story.append(Spacer(1, 0.4 * cm))

    # Behavioral notes
    story.append(Paragraph("Behavioral Notes", h2_style))
    notes_text = (
        f"Patient demonstrates a weekly adherence rate of {weekly['weekly_score']:.1f}%. "
        f"Risk level is classified as <b>{risk['risk_level']}</b> with a score of {risk['score']:.1f}. "
        f"Clinician review is recommended for any HIGH or CRITICAL classification."
    )
    story.append(Paragraph(notes_text, body_style))

    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(f"Generated: {utcnow_str()}", ParagraphStyle("footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(story)

    # Persist path in DB
    execute(
        "INSERT INTO reports (patient_id, file_path, created_at) VALUES (?, ?, ?)",
        (patient_id, str(filepath), utcnow_str()),
    )
    logger.info("PDF report generated: %s", filepath)
    return str(filepath)


def _build_table(data: list, has_header: bool = False) -> Table:
    """Helper to build a styled ReportLab table."""
    t = Table(data, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0 if has_header else -1), colors.HexColor("#EEF2F7")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if has_header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    t.setStyle(TableStyle(style))
    return t


def get_reports(patient_id: int) -> list[dict]:
    rows = fetchall(
        "SELECT * FROM reports WHERE patient_id = ? ORDER BY created_at DESC",
        (patient_id,),
    )
    return rows_to_dicts(rows)
