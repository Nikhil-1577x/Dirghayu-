"""
alert_service.py – WhatsApp alert cascade via Twilio + per-patient cooldowns + DB logging.

TASK 5 — Cooldown policy (verified and documented):

  MISSED DOSE → family WhatsApp:
    • Cooldown: 4 hours PER PATIENT (not global).
      Checked via alert_log WHERE patient_id=? AND alert_type='MISSED_DOSE'.
    • This prevents spamming family for every dose check cycle.

  RISK_ESCALATION → doctor WhatsApp:
    • Triggered only when risk_score > 70 (RISK_SCORE_DOCTOR_THRESHOLD).
    • Cooldown: 12 hours PER PATIENT (not global).
      Checked via alert_log WHERE patient_id=? AND alert_type='RISK_ESCALATION'.

  DRUG HOLIDAY → family + doctor WhatsApp:
    • *** BYPASSES all cooldowns entirely. ***
    • Drug holiday (18+ hours of zero activity) is a medical emergency.
      The alert must always fire when detected, even if one was sent recently.
    • No cooldown check is performed.

  DAILY SUMMARY → family WhatsApp:
    • Fired by APScheduler CronTrigger at 20:00 UTC.
    • CronTrigger is idempotent by design: it stores next_run_time in the
      scheduler. If the server restarts after 20:00, the scheduler will
      calculate the next trigger as the following day's 20:00 — it does NOT
      fire again on the same day after a restart.
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
from app.utils.time_utils import utcnow, utcnow_str
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
    """
    Check whether a recent alert of this type was already sent FOR THIS patient.
    Cooldowns are always per-patient — never global.
    """
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
    Returns True on success, False on failure (or not configured).
    """
    if not settings.TWILIO_ACCOUNT_SID or settings.TWILIO_ACCOUNT_SID.startswith("ACxx"):
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

    Step 1 – Family WhatsApp alert.
      Cooldown: 4 hours per patient (FAMILY_ALERT_COOLDOWN_HOURS).
      Rationale: prevents alert spam on every scheduler cycle.

    Step 2 – Doctor WhatsApp escalation (only if risk_score > 70).
      Cooldown: 12 hours per patient (DOCTOR_ALERT_COOLDOWN_HOURS).
      Rationale: doctors should not be disturbed for every missed dose,
      only when the patient's overall risk is already elevated.
    """
    patient = fetchone("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if patient is None:
        logger.error("Patient %d not found for missed dose alert", patient_id)
        return

    # ── Step 1: Family alert — 4-hour per-patient cooldown ────────────────
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
            logger.debug(
                "Family missed-dose alert skipped (4h cooldown active) for patient %d", patient_id
            )

    # ── Step 2: Doctor escalation — 12-hour per-patient cooldown ─────────
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
            logger.debug(
                "Doctor escalation alert skipped (12h cooldown active) for patient %d", patient_id
            )


def alert_drug_holiday(patient_id: int) -> None:
    """
    Send URGENT drug holiday alert to both family AND doctor.

    *** COOLDOWN BYPASSED INTENTIONALLY ***
    A drug holiday (18+ hours of zero medication activity) is a medical emergency.
    This alert must fire every time it is detected, regardless of any previous alerts.
    Do NOT add a cooldown check here.
    """
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
            # No cooldown — drug holiday alerts always fire
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
    """
    Daily adherence summary to family.

    Fired by APScheduler CronTrigger at 20:00 UTC.
    CronTrigger is restart-safe: if the server restarts at 21:00, the next
    trigger will be calculated as the following day's 20:00 — it will NOT
    fire again on the same day.
    """
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
