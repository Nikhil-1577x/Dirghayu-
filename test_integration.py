#!/usr/bin/env python3
"""
test_integration.py – Dirghau Backend End-to-End Integration Test

Tests the full event flow without physical hardware.
Requires:
  - FastAPI server running at localhost:8000
  - Mosquitto MQTT broker running at localhost:1883

Run:
  python test_integration.py
"""

import json
import sys
import time
import threading
import socket
from datetime import datetime, timedelta, timezone

# ── Check dependencies ────────────────────────────────────────────────────────
try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Run: pip install requests")
    sys.exit(1)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("ERROR: 'paho-mqtt' not installed. Run: pip install paho-mqtt")
    sys.exit(1)

try:
    import websocket as ws_lib
except ImportError:
    print("ERROR: 'websocket-client' not installed. Run: pip install websocket-client")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
BASE_URL       = "http://localhost:8000"
WS_URL         = "ws://localhost:8000"
MQTT_BROKER    = "localhost"
MQTT_PORT      = 1883
MQTT_TOPIC     = "pillbox/dose_event"
TEST_PATIENT_ID = 999
PASS_CHAR = "✅ PASS"
FAIL_CHAR = "❌ FAIL"

results: list[tuple[str, bool]] = []
ws_messages: list[dict] = []


# ═══════════════════════════════════════════════════════════════════════════════
# Pre-flight checks
# ═══════════════════════════════════════════════════════════════════════════════

def check_server() -> bool:
    """Check if FastAPI server is up."""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def check_mqtt() -> bool:
    """Check if Mosquitto is accepting TCP connections."""
    try:
        s = socket.create_connection((MQTT_BROKER, MQTT_PORT), timeout=3)
        s.close()
        return True
    except Exception:
        return False


def preflight():
    print("\n" + "=" * 60)
    print("  Dirghau Integration Test")
    print("=" * 60)

    print("\n[PRE-FLIGHT] Checking services...")

    if not check_server():
        print(f"\n  ❌ FastAPI server is NOT running at {BASE_URL}")
        print("  To start it, run:")
        print("    cd Backend")
        print("    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    print(f"  ✅ FastAPI server is running at {BASE_URL}")

    if not check_mqtt():
        print(f"\n  ❌ Mosquitto MQTT broker is NOT running at {MQTT_BROKER}:{MQTT_PORT}")
        print("  To start Mosquitto on Windows:")
        print("    1. Install from: https://mosquitto.org/download")
        print("    2. Open Services (Win+R → services.msc)")
        print("    3. Find 'Mosquitto Broker' and click Start")
        print("  Or run:  net start mosquitto")
        sys.exit(1)
    print(f"  ✅ Mosquitto broker is running at {MQTT_BROKER}:{MQTT_PORT}")


# ═══════════════════════════════════════════════════════════════════════════════
# Test utilities
# ═══════════════════════════════════════════════════════════════════════════════

def record(name: str, passed: bool):
    results.append((name, passed))
    status = PASS_CHAR if passed else FAIL_CHAR
    print(f"  {status}  {name}")


def get(path: str) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=10)


def post(path: str, data: dict) -> requests.Response:
    return requests.post(f"{BASE_URL}{path}", json=data, timeout=10)


# ═══════════════════════════════════════════════════════════════════════════════
# Test steps
# ═══════════════════════════════════════════════════════════════════════════════

def step_ensure_test_patient() -> int:
    """Step 3: POST to create patient 999 if not already exists."""
    print(f"\n[STEP 3] Ensuring test patient (id={TEST_PATIENT_ID}) exists...")

    # Check if exists
    resp = get(f"/patient/{TEST_PATIENT_ID}")
    if resp.status_code == 200:
        print(f"  [SKIP] Patient {TEST_PATIENT_ID} already exists")
        return TEST_PATIENT_ID

    # Create patient — note: we can't force a specific ID in SQLite AUTOINCREMENT.
    # We create the patient and use whatever ID is returned.
    payload = {
        "name": "Test Patient",
        "age": 55,
        "gender": "male",
        "phone": "+10000000001",
        "family_phone": "+10000000002",
        "doctor_phone": "+10000000003",
    }
    resp = post("/patient/", payload)
    assert resp.status_code == 201, f"Patient create failed: {resp.text}"
    pid = resp.json()["id"]
    print(f"  [OK] Created test patient (id={pid})")
    return pid


def step_add_medication(patient_id: int) -> int:
    """Step 4: Add medication scheduled 2 minutes from now."""
    print(f"\n[STEP 4] Adding medication scheduled 2 minutes from now...")

    now_utc = datetime.now(timezone.utc)
    sched_time = (now_utc + timedelta(minutes=2)).strftime("%H:%M")

    payload = {
        "name": "TestMed",
        "dose": "100mg",
        "schedule_time": sched_time,
    }
    resp = post(f"/patient/{patient_id}/medication", payload)
    assert resp.status_code == 201, f"Medication create failed: {resp.text}"
    med_id = resp.json()["id"]
    print(f"  [OK] Created medication TestMed @ {sched_time} (id={med_id})")
    return med_id


def step_open_websocket(patient_id: int):
    """Step 5: Open WebSocket in background thread, collect messages."""
    print(f"\n[STEP 5] Opening WebSocket connection for patient {patient_id}...")

    def on_message(wsapp, raw):
        try:
            msg = json.loads(raw)
            ws_messages.append(msg)
        except Exception:
            pass

    def on_error(wsapp, err):
        pass

    def on_open(wsapp):
        print(f"  [OK] WebSocket connected to {WS_URL}/ws/{patient_id}")

    wsapp = ws_lib.WebSocketApp(
        f"{WS_URL}/ws/{patient_id}",
        on_message=on_message,
        on_error=on_error,
        on_open=on_open,
    )
    t = threading.Thread(target=wsapp.run_forever, daemon=True)
    t.start()
    time.sleep(2)   # Give connection time to establish
    return wsapp


def step_publish_mqtt(patient_id: int, med_id: int):
    """Step 6: Publish MQTT dose event after 2-second delay (simulated scheduling)."""
    print(f"\n[STEP 6] Publishing MQTT dose event for patient {patient_id}, med {med_id}...")

    payload = json.dumps({
        "patient_id": patient_id,
        "medication_id": med_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "taken",
    })

    connected = threading.Event()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            connected.set()

    client = mqtt.Client(client_id="integration_test", clean_session=True)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=10)
    client.loop_start()
    connected.wait(timeout=5)
    result = client.publish(MQTT_TOPIC, payload, qos=1)
    result.wait_for_publish(timeout=5)
    client.loop_stop()
    client.disconnect()
    print(f"  [OK] Published: {payload}")


def step_assert_adherence(patient_id: int):
    """Step 8a: Assert dose event appears in adherence endpoint."""
    resp = get(f"/patient/{patient_id}/adherence")
    ok = resp.status_code == 200 and resp.json().get("daily_adherence", {}).get("total", 0) > 0
    record("Dose event appears in GET /patient/adherence", ok)


def step_assert_risk(patient_id: int):
    """Step 8b: Assert risk score exists."""
    resp = get(f"/patient/{patient_id}/risk")
    ok = resp.status_code == 200 and resp.json().get("score") is not None
    record("Risk score exists in GET /patient/risk", ok)


def step_assert_ws_dose_event():
    """Step 8c: Assert WebSocket received a dose_event message."""
    ok = any(m.get("type") == "dose_event" for m in ws_messages)
    record("WebSocket received dose_event message", ok)


def step_assert_ws_risk_update():
    """Step 8d: Assert WebSocket received a risk_update message."""
    ok = any(m.get("type") == "risk_update" for m in ws_messages)
    record("WebSocket received risk_update message", ok)


def step_risk_compute(patient_id: int):
    """Step 9: POST to compute risk score, assert float 0-100."""
    print(f"\n[STEP 9] Testing /patient/{patient_id}/risk/compute...")
    resp = post(f"/patient/{patient_id}/risk/compute", {})
    ok = False
    if resp.status_code == 200:
        score = resp.json().get("score")
        ok = isinstance(score, (int, float)) and 0.0 <= float(score) <= 100.0
    record("POST /risk/compute returns float score 0-100", ok)
    if ok:
        print(f"  Score = {resp.json()['score']:.2f} | Level = {resp.json()['risk_level']}")


def step_appointment_previsit(patient_id: int):
    """Step 10: POST appointment 48h from now, assert it is created."""
    print(f"\n[STEP 10] Testing appointment + pre-visit scheduling...")
    appt_time = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
    payload = {
        "appointment_time": appt_time,
        "doctor_name": "Dr. Test",
        "notes": "Integration test appointment",
    }
    resp = post(f"/patient/{patient_id}/appointment", payload)
    ok = resp.status_code == 201
    record("POST /appointment for 48h from now returns 201", ok)

    # Verify it appears in the list
    resp2 = get(f"/patient/{patient_id}/appointments")
    appts = resp2.json() if resp2.status_code == 200 else []
    found = any(a.get("appointment_time") == appt_time for a in appts)
    record("Appointment appears in GET /appointments (pre-visit eligible)", found)


# ═══════════════════════════════════════════════════════════════════════════════
# Main runner
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    preflight()

    # Step 3
    patient_id = step_ensure_test_patient()

    # Step 4
    med_id = step_add_medication(patient_id)

    # Step 5
    wsapp = step_open_websocket(patient_id)

    # Step 6: publish MQTT
    step_publish_mqtt(patient_id, med_id)

    # Step 7: Wait for processing
    print(f"\n[STEP 7] Waiting 15 seconds for MQTT processing pipeline...")
    for i in range(15, 0, -1):
        print(f"  Waiting {i}s...", end="\r")
        time.sleep(1)
    print("  Processing complete.         ")

    # Step 8: Assertions
    print(f"\n[STEP 8] Running assertions...")
    step_assert_adherence(patient_id)
    step_assert_risk(patient_id)
    step_assert_ws_dose_event()
    step_assert_ws_risk_update()

    # Step 9
    step_risk_compute(patient_id)

    # Step 10
    step_appointment_previsit(patient_id)

    # Close WebSocket
    try:
        wsapp.close()
    except Exception:
        pass

    # ── Final summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    print(f"  RESULT: {passed}/{total} tests passed")
    for name, ok in results:
        marker = "✅" if ok else "❌"
        print(f"    {marker}  {name}")

    print()
    if passed == total:
        print("  🎉  DIRGHAU BACKEND READY FOR DEMO")
    else:
        print("  ⚠️   Some tests FAILED — review the output above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
