"""
database.py – SQLite initialisation using sqlite-utils.
All CREATE TABLE statements live here.
"""
import sqlite3
from pathlib import Path

from app.config import settings


def get_db_path() -> str:
    return settings.DB_PATH


def get_connection() -> sqlite3.Connection:
    """Return a raw sqlite3 connection with row_factory enabled."""
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    """Create all tables if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    -- ── Patients ──────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS patients (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT    NOT NULL,
        age           INTEGER NOT NULL,
        gender        TEXT    NOT NULL,
        phone         TEXT    NOT NULL,
        family_phone  TEXT,
        doctor_phone  TEXT,
        created_at    TEXT    DEFAULT (datetime('now'))
    );

    -- ── Medications ───────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS medications (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id    INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        name          TEXT    NOT NULL,
        dose          TEXT    NOT NULL,
        schedule_time TEXT    NOT NULL   -- HH:MM format
    );

    -- ── Dose events ───────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS dose_events (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id    INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        medication_id INTEGER NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
        timestamp     TEXT    NOT NULL,
        status        TEXT    NOT NULL CHECK(status IN ('TAKEN','LATE','MISSED')),
        source        TEXT    NOT NULL CHECK(source IN ('ESP32','manual'))
    );

    -- ── Biomarker readings ────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS biomarker_readings (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id     INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        biomarker_type TEXT    NOT NULL,
        value          REAL    NOT NULL,
        timestamp      TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- ── Risk scores ───────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS risk_scores (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        score      REAL    NOT NULL,
        risk_level TEXT    NOT NULL,
        timestamp  TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- ── Alert log ─────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS alert_log (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        alert_type TEXT    NOT NULL,
        message    TEXT    NOT NULL,
        sent_to    TEXT    NOT NULL,
        timestamp  TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- ── Appointments ──────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS appointments (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id       INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        appointment_time TEXT    NOT NULL,
        doctor_name      TEXT    NOT NULL,
        notes            TEXT
    );

    -- ── Reports ───────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS reports (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        file_path  TEXT    NOT NULL,
        created_at TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- ── Drug interactions (GAP 3) ─────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS drug_interactions (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        drug_a        TEXT    NOT NULL,
        drug_b        TEXT    NOT NULL,
        severity      TEXT    NOT NULL CHECK(severity IN ('SEVERE','MODERATE')),
        clinical_note TEXT    NOT NULL
    );

    -- ── Environment readings – DHT22 (GAP 4) ─────────────────────────────
    CREATE TABLE IF NOT EXISTS environment_readings (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id     INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        temperature_c  REAL    NOT NULL,
        humidity_pct   REAL    NOT NULL,
        timestamp      TEXT    NOT NULL DEFAULT (datetime('now'))
    );
    """)

    conn.commit()
    conn.close()

    # Seed drug interactions idempotently after tables are created
    from app.services.drug_interaction_service import seed_drug_interactions
    seed_drug_interactions()
