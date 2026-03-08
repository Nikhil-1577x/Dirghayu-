"""
alert_service.py – WhatsApp alert cascade via Twilio + alert cooldown + DB logging.

Cascade logic:
  1. On missed dose → send WhatsApp to family
  2. If risk_score > 70 → escalate to doctor
  3. Cooldowns: family=4h, doctor=12h
"""
import logging
from datetime import timedelta
from typing import Optional

from twilio.rest import Client

from app.config import settings
from app.utils.constants import (
    AlertType, FAMILY_ALERT_COOLDOWN_HOURS, DOCTOR_ALERT_COOLDOWN_HOURS,
    RISK_SCORE_DOCTOR_THRESHOLD,
)
from app.utils.time_utils import utcnow, utcnow_str, parse_iso
from app.utils.db_utils import execute, fetchone, rows_to_dicts, fetchall

logger = logging.getLogger(__name__)


def _get_twilio_client() -> Client:
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def _whatsapp_number(phone: str) -> str:
    """Ensure number is in whatsapp:+xxx format."""
    if not phone.startswith("whatsapp:"):
        return f"whatsapp:{phone}"
    return phone


def _is_on_cooldown(patient_id: int, alert_type: AlertType, cooldown_hours: int) -> bool:
    """Check whether a recent alert of this type was already sent."""
    cutoff = (utcnow() - timedelta(hours=cooldown_hours)).isoformat()
    row = fetchone(
        """SELECT id FROM alert_log
           WHERE patient_id = ? AND alert_type = ? AND timestamp > ?
           LIMIT 1""",
        (patient_id, alert_type.value, cutoff),
    )
    return row is not None


def _log_alert(
    patient_id: int,
    alert_type: AlertType,
    message: str,
    sent_to: str,
) -> int:
    return execute(
        "INSERT INTO alert_log (patient_id, alert_type, message, sent_to, timestamp) VALUES (?,?,?,?,?)",
        (patient_id, alert_type.value, message, sent_to, utcnow_str()),
    )


def send_whatsapp(to_number: str, message: str) -> bool:
    """
    Send a WhatsApp message via Twilio.
    Returns True on success, False on failure.
    """
    if not settings.TWILIO_ACCOUNT_SID or settings.TWILIO_ACCOUNT_SID.startswith("AC" + "xx"):
        logger.warning("Twilio not configured – skipping WhatsApp send to %s", to_number)
        return False
    try:
        client = _get_twilio_client()
        client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=_whatsapp_number(to_number),
            body=message,
        )
        logger.info("WhatsApp sent to %s", to_number)
        return True
    except Exception as exc:
        logger.error("Twilio error: %s", exc)
        return False


def alert_missed_dose(patient_id: int, medication_name: str, risk_score: Optional[float] = None) -> None:
    """
    Missed dose alert cascade:
      Step 1 – Alert family (if not on cooldown)
      Step 2 – Escalate to doctor if risk_score > threshold
    """
    patient = fetchone("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if patient is None:
        logger.error("Patient %d not found for missed dose alert", patient_id)
        return

    # ── Step 1: Family alert ──────────────────────────────────────────────
    if patient["family_phone"]:
        if not _is_on_cooldown(patient_id, AlertType.MISSED_DOSE, FAMILY_ALERT_COOLDOWN_HOURS):
            msg = (
                f"⚠️ Alert: {patient['name']} missed their {medication_name} dose. "
                f"Please check on them."
            )
            sent = send_whatsapp(patient["family_phone"], msg)
            if sent:
                _log_alert(patient_id, AlertType.MISSED_DOSE, msg, patient["family_phone"])
        else:
            logger.debug("Family alert on cooldown for patient %d", patient_id)

    # ── Step 2: Doctor escalation ─────────────────────────────────────────
    if risk_score is not None and risk_score > RISK_SCORE_DOCTOR_THRESHOLD and patient["doctor_phone"]:
        if not _is_on_cooldown(patient_id, AlertType.RISK_ESCALATION, DOCTOR_ALERT_COOLDOWN_HOURS):
            msg = (
                f"🚨 Doctor Alert: Patient {patient['name']} missed {medication_name}. "
                f"Risk Score: {risk_score:.1f}. Immediate attention may be required."
            )
            sent = send_whatsapp(patient["doctor_phone"], msg)
            if sent:
                _log_alert(patient_id, AlertType.RISK_ESCALATION, msg, patient["doctor_phone"])
        else:
            logger.debug("Doctor alert on cooldown for patient %d", patient_id)


def alert_drug_holiday(patient_id: int) -> None:
    """Send URGENT drug holiday alert to family and doctor."""
    patient = fetchone("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if patient is None:
        return

    msg = (
        f"🚨 URGENT: {patient['name']} has had NO medication activity for 18+ hours. "
        f"Drug holiday detected. Immediate follow-up required."
    )
    for phone_field in ("family_phone", "doctor_phone"):
        phone = patient[phone_field]
        if phone:
            send_whatsapp(phone, msg)
            _log_alert(patient_id, AlertType.DRUG_HOLIDAY, msg, phone)


def send_dose_reminder(patient_id: int, medication_name: str, dose: str, schedule_time: str) -> None:
    """Scheduled dose reminder to patient."""
    patient = fetchone("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if patient is None:
        return
    msg = (
        f"💊 Reminder: Time to take your {medication_name} ({dose}) "
        f"scheduled at {schedule_time}."
    )
    send_whatsapp(patient["phone"], msg)
    _log_alert(patient_id, AlertType.DOSE_REMINDER, msg, patient["phone"])


def send_daily_summary(patient_id: int, adherence: dict) -> None:
    """Daily adherence summary to family."""
    patient = fetchone("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if patient is None:
        return
    msg = (
        f"📊 Daily Summary for {patient['name']}:\n"
        f"  Doses taken today: {adherence.get('taken', 0)}/{adherence.get('total', 0)}\n"
        f"  Weekly adherence: {adherence.get('weekly_score', 0):.1f}%"
    )
    if patient["family_phone"]:
        send_whatsapp(patient["family_phone"], msg)
        _log_alert(patient_id, AlertType.DAILY_SUMMARY, msg, patient["family_phone"])


def get_alert_history(patient_id: int) -> list[dict]:
    rows = fetchall(
        "SELECT * FROM alert_log WHERE patient_id = ? ORDER BY timestamp DESC",
        (patient_id,),
    )
    return rows_to_dicts(rows)
