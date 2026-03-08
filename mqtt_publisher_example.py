#!/usr/bin/env python3
"""
mqtt_publisher_example.py – Simulates an ESP32 publishing dose events.

Usage:
  python mqtt_publisher_example.py

Publishes a dose event every 5 seconds for testing purposes.
"""
import json
import time
import random
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# ── Config ─────────────────────────────────────────────────────────────────────
BROKER = "localhost"
PORT = 1883
TOPIC = "pillbox/dose_event"

PATIENT_IDS = [1, 2]
MEDICATION_IDS = [1, 2, 3]
EVENTS = ["taken", "taken", "taken", "missed"]   # weighted towards taken


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT Publisher] Connected to broker at {BROKER}:{PORT}")
    else:
        print(f"[MQTT Publisher] Connection failed rc={rc}")


def publish_dose_event(client: mqtt.Client) -> None:
    payload = {
        "patient_id": random.choice(PATIENT_IDS),
        "medication_id": random.choice(MEDICATION_IDS),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": random.choice(EVENTS),
    }
    message = json.dumps(payload)
    result = client.publish(TOPIC, message, qos=1)
    print(f"[MQTT Publisher] Published → {message}  (mid={result.mid})")


def main():
    client = mqtt.Client(client_id="esp32_simulator", clean_session=True)
    client.on_connect = on_connect
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    print(f"[MQTT Publisher] Starting – publishing to '{TOPIC}' every 5 seconds…")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            publish_dose_event(client)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n[MQTT Publisher] Stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
