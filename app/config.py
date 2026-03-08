"""
config.py – Centralised settings loaded from .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


class Settings:
    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./medication.db")
    DB_PATH: str = os.getenv("DB_PATH", "medication.db")

    # ── MQTT ─────────────────────────────────────────────────
    MQTT_BROKER: str = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_USERNAME: str = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "")
    MQTT_DOSE_TOPIC: str = os.getenv("MQTT_DOSE_TOPIC", "pillbox/dose_event")
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID", "medication_backend")

    # ── Twilio ────────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_FROM: str = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    # ── Security ──────────────────────────────────────────────
    API_KEY: str = os.getenv("API_KEY", "changeme-super-secret-key")

    # ── Reports ───────────────────────────────────────────────
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", "reports")

    # ── Scheduler ─────────────────────────────────────────────
    DAILY_SUMMARY_HOUR: int = int(os.getenv("DAILY_SUMMARY_HOUR", "20"))
    DAILY_SUMMARY_MINUTE: int = int(os.getenv("DAILY_SUMMARY_MINUTE", "0"))
    PRE_VISIT_HOURS_BEFORE: int = int(os.getenv("PRE_VISIT_HOURS_BEFORE", "48"))

    # ── App ───────────────────────────────────────────────────
    APP_TITLE: str = "Smart Medication Adherence System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ALLOWED_ORIGINS: list = ["*"]   # Tighten in production


settings = Settings()
