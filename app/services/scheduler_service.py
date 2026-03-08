"""
scheduler_service.py – APScheduler background jobs.

Tasks:
  1. Dose reminders        – runs at each medication's schedule_time
  2. Daily family summary  – every day at 8 PM UTC
  3. Drug holiday scan     – every hour
  4. Pre-visit report      – 48 h before appointment → PDF → doctor WhatsApp
"""
import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.utils.db_utils import fetchall, rows_to_dicts

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler(timezone="UTC")


# ── Job functions ─────────────────────────────────────────────────────────────

def _send_dose_reminders() -> None:
    """
    For every medication whose schedule_time matches now (within 1 minute window),
    send a reminder to the patient.
    """
    from app.services.alert_service import send_dose_reminder

    now_hhmm = datetime.now(timezone.utc).strftime("%H:%M")
    meds = fetchall(
        "SELECT m.*, p.phone FROM medications m JOIN patients p ON p.id = m.patient_id",
    )
    for med in meds:
        if med["schedule_time"] == now_hhmm:
            try:
                send_dose_reminder(
                    patient_id=med["patient_id"],
                    medication_name=med["name"],
                    dose=med["dose"],
                    schedule_time=med["schedule_time"],
                )
            except Exception as exc:
                logger.error("Reminder failed for med %d: %s", med["id"], exc)


def _send_daily_summaries() -> None:
    """Send adherence summary to all patients' families at 8 PM UTC."""
    from app.services.adherence_engine import get_daily_adherence, get_weekly_adherence
    from app.services.alert_service import send_daily_summary

    patients = fetchall("SELECT id FROM patients")
    for p in patients:
        pid = p["id"]
        try:
            daily = get_daily_adherence(pid)
            weekly = get_weekly_adherence(pid)
            adherence = {**daily, "weekly_score": weekly["weekly_score"]}
            send_daily_summary(pid, adherence)
        except Exception as exc:
            logger.error("Daily summary failed for patient %d: %s", pid, exc)


# ── GAP 2: Morning daily protocol ─────────────────────────────────────────────

# Per-medication food/timing context for known NCD drugs
_MED_GUIDANCE: dict[str, str] = {
    "metformin":    "Take WITH breakfast and dinner. NEVER on an empty stomach — reduces GI side effects.",
    "amlodipine":   "Take at the same time each day. Food does not affect absorption.",
    "insulin":      "Administer as prescribed. NO exercise within 2 hours after dose — hypoglycemia risk.",
    "glipizide":    "Take 30 minutes before meals. Monitor for low blood sugar.",
    "atorvastatin": "Take at any time of day, preferably in the evening. Avoid grapefruit.",
    "aspirin":      "Take with food or a full glass of water to protect the stomach.",
    "losartan":     "Take at the same time each day. Avoid potassium-rich supplements.",
    "ramipril":     "Take on an empty stomach for best absorption. Avoid NSAIDs.",
}

_DEFAULT_MED_GUIDANCE = "Take as prescribed. Consult your doctor if unsure."


def _morning_guidance_for_med(name: str, dose: str, schedule_time: str) -> str:
    name_lower = name.strip().lower()
    guidance = _DEFAULT_MED_GUIDANCE
    for keyword, tip in _MED_GUIDANCE.items():
        if keyword in name_lower:
            guidance = tip
            break
    return f"  💊 {name} {dose} @ {schedule_time}\n     {guidance}"


def _send_morning_protocols() -> None:
    """
    GAP 2 — Send personalised 7 AM daily protocol to every patient.

    Message contains:
    - Each medication with its food/timing guidance
    - Exercise recommendation (20 min walk, avoid within 2h of insulin)
    - Appointment reminder if an appointment is within 72 hours

    Fired via CronTrigger at 07:00 UTC daily (≈ 12:30 PM IST / adjustable).
    Uses existing Twilio WhatsApp service — no new sender needed.
    """
    from app.services.alert_service import send_whatsapp, _log_alert
    from app.utils.constants import AlertType

    now = datetime.now(timezone.utc)
    window_72h = (now + timedelta(hours=72)).isoformat()

    patients = fetchall("SELECT * FROM patients")
    for patient in patients:
        pid = patient["id"]
        phone = patient["phone"]
        if not phone:
            continue

        try:
            # Build medication protocol section
            meds = fetchall(
                "SELECT name, dose, schedule_time FROM medications WHERE patient_id = ? ORDER BY schedule_time",
                (pid,),
            )
            if not meds:
                continue

            med_lines = "\n".join(
                _morning_guidance_for_med(m["name"], m["dose"], m["schedule_time"])
                for m in meds
            )

            # Check if any medication is insulin to add exercise warning
            has_insulin = any("insulin" in m["name"].lower() for m in meds)
            if has_insulin:
                exercise_tip = (
                    "🏃 Exercise: 20-min walk recommended between 6–8am or 5–7pm.\n"
                    "   ⚠️ Do NOT exercise within 2 hours of insulin dose."
                )
            else:
                exercise_tip = (
                    "🏃 Exercise: 20-min walk recommended between 6–8am or 5–7pm.\n"
                    "   Best done on a light stomach for blood sugar control."
                )

            # Upcoming appointment within 72 hours
            upcoming = fetchall(
                """SELECT appointment_time, doctor_name FROM appointments
                   WHERE patient_id = ? AND appointment_time BETWEEN ? AND ?
                   ORDER BY appointment_time LIMIT 1""",
                (pid, now.isoformat(), window_72h),
            )
            appt_line = ""
            if upcoming:
                appt = upcoming[0]
                appt_line = (
                    f"\n\n📅 APPOINTMENT REMINDER:\n"
                    f"   You have an appointment with {appt['doctor_name']}\n"
                    f"   on {appt['appointment_time'][:16].replace('T', ' at ')} UTC.\n"
                    f"   Please bring your medication log and glucose readings."
                )

            msg = (
                f"🌅 Good morning, {patient['name']}!\n\n"
                f"Here is your health protocol for today:\n\n"
                f"{med_lines}\n\n"
                f"{exercise_tip}"
                f"{appt_line}\n\n"
                f"Stay consistent — every dose counts. 💙"
            )

            send_whatsapp(phone, msg)
            _log_alert(pid, AlertType.DOSE_REMINDER, msg, phone)
            logger.info("Morning protocol sent to patient %d", pid)

        except Exception as exc:
            logger.error("Morning protocol failed for patient %d: %s", pid, exc)

def _check_drug_holidays() -> None:
    """Check every patient for drug holiday every hour."""
    from app.services.adherence_engine import check_drug_holiday
    from app.services.alert_service import alert_drug_holiday

    patients = fetchall("SELECT id FROM patients")
    for p in patients:
        pid = p["id"]
        try:
            if check_drug_holiday(pid):
                alert_drug_holiday(pid)
        except Exception as exc:
            logger.error("Drug holiday check failed for patient %d: %s", pid, exc)


def _check_pre_visit_reports() -> None:
    """
    Every hour check if any appointment is within pre-visit hours.
    If so generate PDF report and notify doctor.
    """
    from app.services.report_service import generate_report
    from app.services.alert_service import send_whatsapp
    from app.utils.db_utils import fetchone

    threshold_hours = settings.PRE_VISIT_HOURS_BEFORE
    now = datetime.now(timezone.utc)
    window_start = now.isoformat()
    window_end = (now + timedelta(hours=threshold_hours + 1)).isoformat()

    appts = fetchall(
        """SELECT a.*, p.doctor_phone, p.name AS patient_name
           FROM appointments a JOIN patients p ON p.id = a.patient_id
           WHERE a.appointment_time BETWEEN ? AND ?""",
        (window_start, window_end),
    )
    for appt in appts:
        pid = appt["patient_id"]
        try:
            # Check if report already sent for this appointment
            existing = fetchall(
                "SELECT id FROM alert_log WHERE patient_id=? AND alert_type='PRE_VISIT_REPORT' AND timestamp >= ?",
                (pid, (now - timedelta(hours=1)).isoformat()),
            )
            if existing:
                continue

            path = generate_report(pid)
            doc_phone = appt["doctor_phone"]
            if doc_phone:
                msg = (
                    f"📋 Pre-visit report for {appt['patient_name']} "
                    f"(appointment: {appt['appointment_time']}) – "
                    f"Report generated at: {path}"
                )
                send_whatsapp(doc_phone, msg)
                from app.utils.constants import AlertType
                from app.utils.db_utils import execute
                from app.utils.time_utils import utcnow_str
                execute(
                    "INSERT INTO alert_log (patient_id, alert_type, message, sent_to, timestamp) VALUES (?,?,?,?,?)",
                    (pid, AlertType.PRE_VISIT_REPORT.value, msg, doc_phone, utcnow_str()),
                )
            logger.info("Pre-visit report sent for patient %d, appt: %s", pid, appt["appointment_time"])
        except Exception as exc:
            logger.error("Pre-visit report failed for patient %d: %s", pid, exc)


# ── Scheduler lifecycle ───────────────────────────────────────────────────────

def start_scheduler() -> None:
    """Register all jobs and start the scheduler."""
    # Dose reminders – run every minute, the job decides who to alert
    _scheduler.add_job(
        _send_dose_reminders,
        trigger=IntervalTrigger(minutes=1),
        id="dose_reminders",
        replace_existing=True,
    )

    # ── Morning protocol – 7 AM UTC daily (≈ 12:30 PM IST) ─────────────────
    # GAP 2: personalised medication guidance, exercise tip, 72h appointment reminder
    _scheduler.add_job(
        _send_morning_protocols,
        trigger=CronTrigger(hour=7, minute=0),
        id="morning_protocol",
        replace_existing=True,
    )

    # Daily summary at 8 PM UTC
    _scheduler.add_job(
        _send_daily_summaries,
        trigger=CronTrigger(hour=settings.DAILY_SUMMARY_HOUR, minute=settings.DAILY_SUMMARY_MINUTE),
        id="daily_summary",
        replace_existing=True,
    )

    # Drug holiday scan – every hour
    _scheduler.add_job(
        _check_drug_holidays,
        trigger=IntervalTrigger(hours=1),
        id="drug_holiday_scan",
        replace_existing=True,
    )

    # Pre-visit report check – every hour
    _scheduler.add_job(
        _check_pre_visit_reports,
        trigger=IntervalTrigger(hours=1),
        id="pre_visit_reports",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("APScheduler started with %d jobs", len(_scheduler.get_jobs()))


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
