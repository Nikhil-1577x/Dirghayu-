# Smart Medication Adherence System – Backend

> Production-grade Python backend for a smart pill dispenser system.  
> Stack: **FastAPI · SQLite · Mosquitto MQTT · APScheduler · Twilio · ReportLab · WebSockets**

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI entrypoint
│   ├── config.py            # Settings from .env
│   ├── database.py          # SQLite init + schema
│   ├── models/              # Pydantic schemas
│   ├── services/            # Business logic
│   ├── api/                 # REST + WebSocket routes
│   ├── utils/               # db_utils, time_utils, constants
│   └── ai_modules/          # OCR, risk prediction, narrative
├── mqtt_publisher_example.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Create virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your Twilio credentials and MQTT settings
```

### 4. Install and start Mosquitto MQTT broker

```bash
# Windows (download from https://mosquitto.org/download/)
net start mosquitto

# Linux
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

### 5. Start the FastAPI server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server starts at: **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/patient/` | Create patient |
| `GET` | `/patient/` | List all patients |
| `GET` | `/patient/{id}` | Get patient |
| `GET` | `/patient/{id}/dashboard` | Full dashboard |
| `GET` | `/patient/{id}/adherence` | Adherence stats |
| `GET` | `/patient/{id}/biomarkers` | Biomarker readings |
| `POST` | `/patient/{id}/biomarkers` | Add biomarker manually |
| `POST` | `/patient/{id}/biomarkers/ocr` | OCR image upload |
| `GET` | `/patient/{id}/risk` | Latest risk score |
| `POST` | `/patient/{id}/risk/compute` | Force recompute risk |
| `GET` | `/patient/{id}/alerts` | Alert history |
| `POST` | `/patient/{id}/report` | Generate PDF report |
| `GET` | `/patient/{id}/reports` | List reports |
| `GET` | `/patient/{id}/report/download/{report_id}` | Download PDF |
| `POST` | `/patient/{id}/medication` | Add medication |
| `GET` | `/patient/{id}/medications` | List medications |
| `POST` | `/patient/{id}/appointment` | Add appointment |
| `GET` | `/patient/{id}/appointments` | List appointments |
| `WS` | `/ws/{patient_id}` | WebSocket realtime events |

---

## Example API Responses

### GET /patient/1/dashboard

```json
{
  "patient": {
    "id": 1, "name": "Jane Doe", "age": 62,
    "gender": "female", "phone": "+1234567890"
  },
  "latest_biomarkers": {
    "blood_glucose": {"value": 97.5, "timestamp": "2026-03-08T14:00:00+00:00"}
  },
  "risk_score": {"score": 23.5, "risk_level": "LOW", "timestamp": "..."},
  "weekly_adherence": {"taken": 18, "missed": 2, "total": 20, "weekly_score": 90.0},
  "daily_adherence": {"taken": 3, "missed": 0, "total": 3, "daily_score": 100.0},
  "recent_alerts": []
}
```

### GET /patient/1/adherence

```json
{
  "patient_id": 1,
  "daily_adherence": {"taken": 3, "missed": 0, "total": 3, "daily_score": 100.0},
  "weekly_score": 90.0,
  "weekly_adherence": {"taken": 18, "missed": 2, "total": 20, "weekly_score": 90.0},
  "missed_doses": []
}
```

### GET /patient/1/risk

```json
{
  "patient_id": 1,
  "id": 5,
  "score": 23.5,
  "risk_level": "LOW",
  "timestamp": "2026-03-08T14:05:00+00:00"
}
```

### POST /patient/1/report → 201

```json
{
  "patient_id": 1,
  "file_path": "reports/1_20260308_140500.pdf",
  "message": "Report generated successfully"
}
```

---

## WebSocket Events

Connect to `ws://localhost:8000/ws/{patient_id}`

### Received event types

```json
// dose_event
{"type": "dose_event", "patient_id": 1, "status": "TAKEN", "medication_id": 2, "timestamp": "..."}

// risk_update
{"type": "risk_update", "patient_id": 1, "score": 35.0, "risk_level": "MODERATE", "timestamp": "..."}

// alert_triggered
{"type": "alert_triggered", "patient_id": 1, "alert_type": "MISSED_DOSE", "timestamp": "..."}
```

---

## MQTT Publisher Example (ESP32 Simulator)

```bash
python mqtt_publisher_example.py
```

Publishes to `pillbox/dose_event` every 5 seconds:

```json
{
  "patient_id": 1,
  "medication_id": 2,
  "timestamp": "2026-03-08T08:05:00+00:00",
  "event": "taken"
}
```

---

## Adherence Rules

| Status | Condition |
|--------|-----------|
| `TAKEN` | Within ±30 minutes of scheduled time |
| `LATE` | Within 2 hours of scheduled time |
| `MISSED` | No dose after 2 hours |
| `DRUG HOLIDAY` | No activity for 18+ hours |

### Risk Levels

| Level | Score Range |
|-------|-------------|
| `LOW` | 0 – 39 |
| `MODERATE` | 40 – 69 |
| `HIGH` | 70 – 84 |
| `CRITICAL` | 85 – 100 |

---

## Alert Cascade

1. **Missed dose** → WhatsApp to **family** (cooldown: 4h)
2. **Risk score > 70** → Escalate to **doctor** (cooldown: 12h)
3. **Drug holiday** → Urgent WhatsApp to **both**
4. **Daily summary** → Every 8 PM UTC → family
5. **Pre-visit report** → 48h before appointment → PDF + doctor WhatsApp

---

## Twilio WhatsApp Setup

1. Create account at [twilio.com](https://twilio.com)
2. Enable WhatsApp Sandbox
3. Add credentials to `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxx
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ```

---

## API Key Security

Pass header `X-API-Key: <your-key>` (set in `.env`).  
To enforce, uncomment the `raise HTTPException` line in `main.py::verify_api_key`.
