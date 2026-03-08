#!/usr/bin/env python3
"""
seed_demo_data.py – Populate realistic 8-week patient history for Dirghau demo day.

IDEMPOTENT: Running this script multiple times will NOT create duplicate data.
Each section checks for existing records before inserting.

Patient profile: Ramesh Kumar, 67, male, diabetic + hypertensive
Medications:
  - Metformin 500mg  | twice daily  | 08:00 and 20:00
  - Amlodipine 5mg   | once daily   | 09:00

8-week dose history (~85% TAKEN, 8% LATE, 5% MISSED, 2% gaps/drug holidays)
Adherence deliberately deteriorates weeks 6-7 then partially recovers week 8.
"""

import sqlite3
import sys
import os
import random
from datetime import datetime, timedelta, timezone

# ── Bootstrap path so we can import app modules ───────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.database import init_db, get_connection

random.seed(42)   # reproducible


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _days_ago(n: int) -> datetime:
    return _now() - timedelta(days=n)


def _at(base: datetime, hour: int, minute: int = 0, offset_minutes: int = 0) -> datetime:
    dt = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
    dt += timedelta(minutes=offset_minutes)
    return dt


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# Seed functions
# ═══════════════════════════════════════════════════════════════════════════════

def seed_patient(conn: sqlite3.Connection) -> int:
    """Create patient if not exists. Return patient_id."""
    cur = conn.execute("SELECT id FROM patients WHERE name = 'Ramesh Kumar' LIMIT 1")
    row = cur.fetchone()
    if row:
        print(f"  [SKIP] Patient 'Ramesh Kumar' already exists (id={row[0]})")
        return row[0]

    cur = conn.execute(
        """INSERT INTO patients (name, age, gender, phone, family_phone, doctor_phone)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("Ramesh Kumar", 67, "male", "+919876543210", "+919876543211", "+912233445566"),
    )
    conn.commit()
    print(f"  [OK] Created patient 'Ramesh Kumar' (id={cur.lastrowid})")
    return cur.lastrowid


def seed_medications(conn: sqlite3.Connection, patient_id: int) -> tuple[int, int, int]:
    """Create medications if not exists. Returns (met_am_id, met_pm_id, aml_id)."""
    ids = []
    meds_to_create = [
        ("Metformin",   "500mg", "08:00"),
        ("Metformin",   "500mg", "20:00"),
        ("Amlodipine",  "5mg",   "09:00"),
    ]
    for name, dose, sched in meds_to_create:
        cur = conn.execute(
            "SELECT id FROM medications WHERE patient_id=? AND name=? AND schedule_time=?",
            (patient_id, name, sched),
        )
        row = cur.fetchone()
        if row:
            print(f"  [SKIP] Medication '{name} {sched}' already exists (id={row[0]})")
            ids.append(row[0])
        else:
            cur = conn.execute(
                "INSERT INTO medications (patient_id, name, dose, schedule_time) VALUES (?,?,?,?)",
                (patient_id, name, dose, sched),
            )
            conn.commit()
            ids.append(cur.lastrowid)
            print(f"  [OK] Created medication '{name} {dose} @ {sched}' (id={cur.lastrowid})")
    return tuple(ids)


def _pick_status_and_offset(week: int) -> tuple[str, int | None]:
    """
    Return (status, offset_minutes_or_None).
    offset_minutes is None → skip this dose entirely (drug holiday gap).

    Week adherence profile:
      Weeks 1-4:  Normal    – 90% taken, 5% late, 4% missed, 1% skipped
      Weeks 5-6:  Declining – 75% taken, 12% late, 10% missed, 3% skipped
      Week 7:     Bad       – 60% taken, 15% late, 18% missed, 7% skipped
      Week 8:     Recovery  – 80% taken, 10% late, 8% missed, 2% skipped
    """
    profiles = {
        range(1, 5): dict(taken=0.90, late=0.05, missed=0.04, skip=0.01),
        range(5, 7): dict(taken=0.75, late=0.12, missed=0.10, skip=0.03),
        range(7, 8): dict(taken=0.60, late=0.15, missed=0.18, skip=0.07),
        range(8, 9): dict(taken=0.80, late=0.10, missed=0.08, skip=0.02),
    }
    p = {}
    for r, v in profiles.items():
        if week in r:
            p = v
            break
    if not p:
        p = dict(taken=0.85, late=0.08, missed=0.05, skip=0.02)

    roll = random.random()
    if roll < p["skip"]:
        return "SKIP", None            # drug-holiday gap
    elif roll < p["skip"] + p["taken"]:
        return "TAKEN", random.randint(-25, 25)
    elif roll < p["skip"] + p["taken"] + p["late"]:
        return "LATE", random.randint(35, 110)
    else:
        return "MISSED", 150           # recorded as MISSED > 2 hrs


def seed_dose_events(conn: sqlite3.Connection, patient_id: int, med_ids: tuple) -> None:
    """Insert 8 weeks of dose events for all 3 medications."""
    existing = conn.execute(
        "SELECT COUNT(*) FROM dose_events WHERE patient_id=?", (patient_id,)
    ).fetchone()[0]
    if existing > 0:
        print(f"  [SKIP] {existing} dose events already exist for patient {patient_id}")
        return

    met_am_id, met_pm_id, aml_id = med_ids
    dose_schedule = [
        (met_am_id, 8,  0),   # Metformin AM
        (met_pm_id, 20, 0),   # Metformin PM
        (aml_id,    9,  0),   # Amlodipine
    ]

    total_days = 56  # 8 weeks
    inserted = 0

    for day_offset in range(total_days, 0, -1):   # oldest first
        day_date = _days_ago(day_offset)
        week_num = (total_days - day_offset) // 7 + 1

        for med_id, hour, minute in dose_schedule:
            # Special: consistently skip evening Metformin on Sundays (behavioral note)
            if med_id == met_pm_id and day_date.weekday() == 6:   # Sunday = 6
                continue   # intentional gap → forces drug holiday pattern

            status, offset_min = _pick_status_and_offset(week_num)
            if status == "SKIP":
                continue

            event_dt = _at(day_date, hour, minute, offset_min or 0)
            conn.execute(
                """INSERT INTO dose_events (patient_id, medication_id, timestamp, status, source)
                   VALUES (?, ?, ?, ?, ?)""",
                (patient_id, med_id, _iso(event_dt), status, "ESP32"),
            )
            inserted += 1

    conn.commit()
    print(f"  [OK] Inserted {inserted} dose events (8 weeks)")


def seed_biomarkers(conn: sqlite3.Connection, patient_id: int) -> None:
    """6 biomarker readings spaced across 8 weeks."""
    existing = conn.execute(
        "SELECT COUNT(*) FROM biomarker_readings WHERE patient_id=?", (patient_id,)
    ).fetchone()[0]
    if existing > 0:
        print(f"  [SKIP] {existing} biomarker readings already exist for patient {patient_id}")
        return

    # Readings spaced ~9 days apart across 8 weeks (weeks 1,2,3,5,6,8)
    week_offsets = [56, 47, 38, 29, 18, 7]   # days ago

    hba1c_values   = [7.2, 7.4, 7.6, 7.5, 7.8, 7.9]
    bp_values      = [138, 142, 145, 143, 148, 151]
    glucose_values = [118, 124, 131, 128, 136, 142]

    for i, days_back in enumerate(week_offsets):
        ts = _iso(_days_ago(days_back))
        conn.execute(
            "INSERT INTO biomarker_readings (patient_id, biomarker_type, value, timestamp) VALUES (?,?,?,?)",
            (patient_id, "HbA1c", hba1c_values[i], ts),
        )
        conn.execute(
            "INSERT INTO biomarker_readings (patient_id, biomarker_type, value, timestamp) VALUES (?,?,?,?)",
            (patient_id, "systolic_bp", bp_values[i], ts),
        )
        conn.execute(
            "INSERT INTO biomarker_readings (patient_id, biomarker_type, value, timestamp) VALUES (?,?,?,?)",
            (patient_id, "fasting_glucose", glucose_values[i], ts),
        )

    conn.commit()
    print(f"  [OK] Inserted 18 biomarker readings (6 time-points × 3 types)")


def seed_appointments(conn: sqlite3.Connection, patient_id: int) -> None:
    """2 appointments: 3 days from now and 6 weeks from now."""
    existing = conn.execute(
        "SELECT COUNT(*) FROM appointments WHERE patient_id=?", (patient_id,)
    ).fetchone()[0]
    if existing > 0:
        print(f"  [SKIP] {existing} appointments already exist for patient {patient_id}")
        return

    appt_soon = _now() + timedelta(days=3)
    appt_far  = _now() + timedelta(weeks=6)

    conn.execute(
        """INSERT INTO appointments (patient_id, appointment_time, doctor_name, notes)
           VALUES (?, ?, ?, ?)""",
        (patient_id, _iso(appt_soon), "Dr. Ananya Sharma",
         "Quarterly diabetes + hypertension review. Bring latest home glucose readings."),
    )
    conn.execute(
        """INSERT INTO appointments (patient_id, appointment_time, doctor_name, notes)
           VALUES (?, ?, ?, ?)""",
        (patient_id, _iso(appt_far), "Dr. Ananya Sharma",
         "6-week follow-up. Review HbA1c trend and medication compliance."),
    )
    conn.commit()
    print(f"  [OK] Created 2 appointments (3 days from now, 6 weeks from now)")


def seed_risk_scores(conn: sqlite3.Connection, patient_id: int) -> None:
    """Weekly risk scores showing LOW → MODERATE → HIGH progression."""
    existing = conn.execute(
        "SELECT COUNT(*) FROM risk_scores WHERE patient_id=?", (patient_id,)
    ).fetchone()[0]
    if existing > 0:
        print(f"  [SKIP] {existing} risk scores already exist for patient {patient_id}")
        return

    # (score, level, days_ago)
    weekly_risk = [
        (22.0, "LOW",      56),
        (28.5, "LOW",      49),
        (35.0, "MODERATE", 42),
        (41.2, "MODERATE", 35),
        (55.8, "MODERATE", 28),
        (68.4, "HIGH",     21),
        (74.1, "HIGH",     14),
        (62.3, "MODERATE",  7),
    ]

    for score, level, days_back in weekly_risk:
        ts = _iso(_days_ago(days_back))
        conn.execute(
            "INSERT INTO risk_scores (patient_id, score, risk_level, timestamp) VALUES (?,?,?,?)",
            (patient_id, score, level, ts),
        )

    conn.commit()
    print(f"  [OK] Inserted 8 weekly risk scores (LOW → MODERATE → HIGH → MODERATE)")


def seed_behavioral_note(conn: sqlite3.Connection, patient_id: int) -> None:
    """Log the Sunday evening skip pattern as an alert_log entry."""
    existing = conn.execute(
        "SELECT COUNT(*) FROM alert_log WHERE patient_id=? AND alert_type='MISSED_DOSE' AND message LIKE '%Sunday%'",
        (patient_id,),
    ).fetchone()[0]
    if existing > 0:
        print(f"  [SKIP] Behavioral note (Sunday skip pattern) already logged")
        return

    ts = _iso(_days_ago(7))
    conn.execute(
        """INSERT INTO alert_log (patient_id, alert_type, message, sent_to, timestamp)
           VALUES (?,?,?,?,?)""",
        (
            patient_id,
            "MISSED_DOSE",
            "⚠️ Behavioral Pattern Flagged: Ramesh Kumar consistently skips his "
            "evening Metformin dose on Sundays. This pattern has been observed "
            "across 6 of the last 8 Sundays. Doctor review recommended.",
            "system",
            ts,
        ),
    )
    conn.commit()
    print(f"  [OK] Logged behavioral note: Sunday evening Metformin skip pattern")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Dirghau – Demo Data Seeder")
    print("=" * 60)

    print("\n[1] Initialising database...")
    init_db()
    print("  [OK] Database ready")

    conn = get_connection()

    print("\n[2] Seeding patient...")
    patient_id = seed_patient(conn)

    print("\n[3] Seeding medications...")
    med_ids = seed_medications(conn, patient_id)

    print("\n[4] Seeding 8-week dose event history...")
    seed_dose_events(conn, patient_id, med_ids)

    print("\n[5] Seeding biomarker readings...")
    seed_biomarkers(conn, patient_id)

    print("\n[6] Seeding appointments...")
    seed_appointments(conn, patient_id)

    print("\n[7] Seeding weekly risk scores...")
    seed_risk_scores(conn, patient_id)

    print("\n[8] Logging behavioral pattern note...")
    seed_behavioral_note(conn, patient_id)

    conn.close()

    print("\n" + "=" * 60)
    print(f"  ✅ Seed complete. Patient ID = {patient_id}")
    print("  Start the server:  uvicorn app.main:app --reload")
    print(f"  Dashboard:         GET http://localhost:8000/patient/{patient_id}/dashboard")
    print("=" * 60)


if __name__ == "__main__":
    main()
