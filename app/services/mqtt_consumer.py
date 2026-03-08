"""
mqtt_consumer.py – Paho MQTT subscriber for dose events AND DHT22 environment readings.

Topics:
  pillbox/dose_event   – ESP32 dose taken/missed events
  pillbox/environment  – DHT22 temperature + humidity readings (GAP 4)

Dose event flow:
  1. Parse + validate payload
  2. Classify dose (TAKEN / LATE / MISSED)
  3. Record in dose_events
  4. Drug holiday check + alert cascade
  5. Recompute risk score
  6. Push WebSocket update

Environment event flow:
  1. Parse payload  
  2. Store in environment_readings
  3. Temperature threshold checks → WhatsApp alerts (6h cooldown)
"""
import json
import logging
import threading

import paho.mqtt.client as mqtt

from app.config import settings
from app.utils.constants import DoseSource, AlertType, WSEventType
from app.utils.time_utils import utcnow_str

logger = logging.getLogger(__name__)

_client: mqtt.Client | None = None


# ── Callbacks ─────────────────────────────────────────────────────────────────

def _on_connect(client: mqtt.Client, userdata, flags, rc: int) -> None:
    if rc == 0:
        logger.info("MQTT connected to %s:%s", settings.MQTT_BROKER, settings.MQTT_PORT)
        # Subscribe to both topics
        client.subscribe(settings.MQTT_DOSE_TOPIC)
        logger.info("Subscribed to topic: %s", settings.MQTT_DOSE_TOPIC)
        client.subscribe(MQTT_ENV_TOPIC)
        logger.info("Subscribed to topic: %s", MQTT_ENV_TOPIC)
    else:
        logger.error("MQTT connection failed with rc=%d", rc)


MQTT_ENV_TOPIC = "pillbox/environment"


def _on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
    """Route incoming messages based on topic."""
    if msg.topic == settings.MQTT_DOSE_TOPIC:
        threading.Thread(target=_process_dose_event, args=(msg.payload,), daemon=True).start()
    elif msg.topic == MQTT_ENV_TOPIC:
        threading.Thread(target=_process_environment_event, args=(msg.payload,), daemon=True).start()
    else:
        logger.debug("Received message on unhandled topic: %s", msg.topic)


# ── Dose event handler ────────────────────────────────────────────────────────

def _process_dose_event(payload: bytes) -> None:
    """Parse, validate and process a dose event payload."""
    from app.models.dose_event import MQTTDosePayload
    from app.services.adherence_engine import (
        classify_dose, record_dose_event, check_drug_holiday,
    )
    from app.services.risk_service import compute_and_store_risk
    from app.services.alert_service import alert_missed_dose, alert_drug_holiday
    from app.api.websocket_routes import broadcast

    try:
        data = json.loads(payload.decode("utf-8"))
        event_payload = MQTTDosePayload(**data)
    except Exception as exc:
        logger.error("MQTT dose payload parse error: %s | raw: %s", exc, payload)
        return

    patient_id    = event_payload.patient_id
    medication_id = event_payload.medication_id
    timestamp     = event_payload.timestamp

    # 1. Classify
    status = classify_dose(medication_id, timestamp)

    # 2. Record in DB
    record_dose_event(patient_id, medication_id, timestamp, status, DoseSource.ESP32)

    # 3. Drug holiday check
    if check_drug_holiday(patient_id):
        logger.warning("Drug holiday detected for patient %d", patient_id)
        alert_drug_holiday(patient_id)

    # 4. Alert cascade if MISSED
    if status.value == "MISSED":
        risk_data = compute_and_store_risk(patient_id)
        alert_missed_dose(patient_id, f"med#{medication_id}", risk_data["score"])
        ws_event = {
            "type":       WSEventType.ALERT_TRIGGERED.value,
            "patient_id": patient_id,
            "alert_type": AlertType.MISSED_DOSE.value,
            "timestamp":  utcnow_str(),
        }
    else:
        risk_data = compute_and_store_risk(patient_id)
        ws_event = {
            "type":          WSEventType.DOSE_EVENT.value,
            "patient_id":    patient_id,
            "status":        status.value,
            "medication_id": medication_id,
            "timestamp":     timestamp,
        }

    # 5. Broadcast WebSocket update
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(broadcast(patient_id, ws_event))
        else:
            loop.run_until_complete(broadcast(patient_id, ws_event))
    except Exception as exc:
        logger.warning("WebSocket broadcast error: %s", exc)

    # 6. Risk update push
    risk_event = {
        "type":       WSEventType.RISK_UPDATE.value,
        "patient_id": patient_id,
        "score":      risk_data["score"],
        "risk_level": risk_data["risk_level"],
        "timestamp":  risk_data["timestamp"],
    }
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(broadcast(patient_id, risk_event))
    except Exception:
        pass

    logger.info("MQTT dose event processed: patient=%d status=%s", patient_id, status.value)


# ── Environment event handler (GAP 4) ─────────────────────────────────────────

def _process_environment_event(payload: bytes) -> None:
    """
    Handle DHT22 temperature/humidity readings from pillbox/environment.
    Delegates all logic to environment_service.
    """
    from app.services.environment_service import process_environment_event
    process_environment_event(payload)


# ── MQTT lifecycle ────────────────────────────────────────────────────────────

def _on_disconnect(client: mqtt.Client, userdata, rc: int) -> None:
    if rc != 0:
        logger.warning("MQTT unexpected disconnect rc=%d – will auto-reconnect", rc)


def start_mqtt_client() -> None:
    """Connect and start the MQTT background loop."""
    global _client
    _client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID, clean_session=True)
    _client.on_connect    = _on_connect
    _client.on_message    = _on_message
    _client.on_disconnect = _on_disconnect

    if settings.MQTT_USERNAME:
        _client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

    try:
        _client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
        _client.loop_start()
        logger.info("MQTT loop started")
    except Exception as exc:
        logger.error("Failed to connect to MQTT broker: %s", exc)


def stop_mqtt_client() -> None:
    global _client
    if _client:
        _client.loop_stop()
        _client.disconnect()
        logger.info("MQTT client disconnected")
