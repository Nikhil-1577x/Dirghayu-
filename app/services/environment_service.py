"""
environment_service.py – DHT22 temperature/humidity MQTT subscriber (GAP 4).

- Subscribes to pillbox/environment
- Stores readings in environment_readings table
- Alerts:
    temp > 30°C → WhatsApp to family (6h cooldown per patient)
    temp > 35°C → WhatsApp to doctor also (6h cooldown per patient)
"""
import json
import logging
import threading
from typing import Optional

from app.config import settings
from app.utils.time_utils import utcnow, utcnow_str
from app.utils.db_utils import execute, fetchall, fetchone
from app.utils.constants import AlertType

logger = logging.getLogger(__name__)

MQTT_ENV_TOPIC = "pillbox/environment"
TEMP_WARN_THRESHOLD = 30.0     # °C – family alert
TEMP_SEVERE_THRESHOLD = 35.0  # °C – escalate to doctor
ENV_ALERT_COOLDOWN_HOURS = 6


def store_environment_reading(
    patient_id: int,
    temperature_c: float,
    humidity_pct: float,
    timestamp: str,
) -> int:
    row_id = execute(
        """INSERT INTO environment_readings (patient_id, temperature_c, humidity_pct, timestamp)
           VALUES (?, ?, ?, ?)""",
        (patient_id, temperature_c, humidity_pct, timestamp),
    )
    logger.debug(
        "Env reading stored: patient=%d temp=%.1f°C humidity=%.1f%% id=%d",
        patient_id, temperature_c, humidity_pct, row_id,
    )
    return row_id


def _is_env_alert_on_cooldown(patient_id: int, alert_level: str) -> bool:
    """
    Cooldown: 6 hours PER PATIENT per alert_level ("WARM" | "HOT").
    Prevents spamming family/doctor for persistent high temperature.
    """
    from datetime import timedelta
    cutoff = (utcnow() - timedelta(hours=ENV_ALERT_COOLDOWN_HOURS)).isoformat()
    # Use sent_to field to distinguish alert level in alert_log
    row = fetchone(
        """SELECT id FROM alert_log
           WHERE patient_id = ? AND alert_type = 'MISSED_DOSE'
             AND sent_to LIKE ? AND timestamp > ?
           LIMIT 1""",
        (patient_id, f"%env_{alert_level}%", cutoff),
    )
    return row is not None


def _log_env_alert(patient_id: int, message: str, sent_to: str, tag: str) -> None:
    """Log into alert_log with a tagged sent_to field for cooldown tracking."""
    execute(
        """INSERT INTO alert_log (patient_id, alert_type, message, sent_to, timestamp)
           VALUES (?,?,?,?,?)""",
        (patient_id, AlertType.RISK_ESCALATION.value, message, f"{sent_to}|env_{tag}", utcnow_str()),
    )


def _is_temp_cooldown_active(patient_id: int, tag: str) -> bool:
    """Check 6h cooldown for environment alerts per patient per severity tag."""
    from datetime import timedelta
    cutoff = (utcnow() - timedelta(hours=ENV_ALERT_COOLDOWN_HOURS)).isoformat()
    row = fetchone(
        """SELECT id FROM alert_log
           WHERE patient_id = ? AND sent_to LIKE ? AND timestamp > ?
           LIMIT 1""",
        (patient_id, f"%env_{tag}%", cutoff),
    )
    return row is not None


def process_environment_event(payload_bytes: bytes) -> None:
    """Parse and process a DHT22 MQTT message."""
    from app.services.alert_service import send_whatsapp

    try:
        data = json.loads(payload_bytes.decode("utf-8"))
        patient_id   = int(data["patient_id"])
        temperature  = float(data["temperature_c"])
        humidity     = float(data["humidity_pct"])
        timestamp    = data.get("timestamp", utcnow_str())
    except Exception as exc:
        logger.error("Environment payload parse error: %s | raw: %s", exc, payload_bytes)
        return

    # 1. Store reading
    store_environment_reading(patient_id, temperature, humidity, timestamp)

    patient = fetchone("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if patient is None:
        logger.warning("Environment event: patient %d not found", patient_id)
        return

    patient_name = patient["name"]

    # ── 2. Warm alert (>30°C) → family WhatsApp, 6h cooldown ────────────
    if temperature > TEMP_WARN_THRESHOLD and patient["family_phone"]:
        if not _is_temp_cooldown_active(patient_id, "warm"):
            msg = (
                f"🌡️ Warning: {patient_name}'s medication storage temperature is "
                f"{temperature:.1f}°C with {humidity:.0f}% humidity.\n"
                f"Insulin and some medications degrade above 30°C. "
                f"Please move medications to a cooler location immediately."
            )
            sent = send_whatsapp(patient["family_phone"], msg)
            if sent:
                _log_env_alert(patient_id, msg, patient["family_phone"], "warm")
            logger.warning(
                "High temp alert (%.1f°C) sent for patient %d", temperature, patient_id
            )
        else:
            logger.debug("Temp alert 'warm' on 6h cooldown for patient %d", patient_id)

    # ── 3. Severe alert (>35°C) → doctor WhatsApp also, 6h cooldown ──────
    if temperature > TEMP_SEVERE_THRESHOLD and patient["doctor_phone"]:
        if not _is_temp_cooldown_active(patient_id, "hot"):
            msg = (
                f"🚨 CRITICAL TEMPERATURE ALERT for {patient_name}: "
                f"Medication storage reached {temperature:.1f}°C. "
                f"Insulin potency may be compromised. "
                f"Patient's medication efficacy is at risk — clinical review recommended."
            )
            sent = send_whatsapp(patient["doctor_phone"], msg)
            if sent:
                _log_env_alert(patient_id, msg, patient["doctor_phone"], "hot")
            logger.critical(
                "SEVERE temp alert (%.1f°C) sent to doctor for patient %d",
                temperature, patient_id,
            )
        else:
            logger.debug("Temp alert 'hot' on 6h cooldown for patient %d", patient_id)


def get_environment_readings(patient_id: int, limit: int = 50) -> list[dict]:
    """Return recent environment readings for a patient."""
    from app.utils.db_utils import rows_to_dicts
    rows = fetchall(
        """SELECT * FROM environment_readings
           WHERE patient_id = ? ORDER BY timestamp DESC LIMIT ?""",
        (patient_id, limit),
    )
    return rows_to_dicts(rows)
