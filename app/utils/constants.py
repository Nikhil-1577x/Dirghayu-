"""
constants.py – System-wide magic numbers and enumerations.
"""
from enum import Enum


# ── Adherence thresholds (minutes) ────────────────────────────────────────
TAKEN_WINDOW_MINUTES: int = 30      # ±30 min of scheduled time → TAKEN
LATE_WINDOW_MINUTES: int = 120      # ±2 h                       → LATE
DRUG_HOLIDAY_HOURS: int = 18        # No activity for 18 h       → URGENT alert

# ── Alert cooldown ────────────────────────────────────────────────────────
FAMILY_ALERT_COOLDOWN_HOURS: int = 4
DOCTOR_ALERT_COOLDOWN_HOURS: int = 12

# ── Risk escalation ───────────────────────────────────────────────────────
RISK_SCORE_DOCTOR_THRESHOLD: float = 70.0

# ── Pre-visit report trigger ──────────────────────────────────────────────
PRE_VISIT_HOURS_BEFORE: int = 48

# ── Weekly score ──────────────────────────────────────────────────────────
WEEKLY_WINDOW_DAYS: int = 7


class DoseStatus(str, Enum):
    TAKEN = "TAKEN"
    LATE = "LATE"
    MISSED = "MISSED"


class DoseSource(str, Enum):
    ESP32 = "ESP32"
    MANUAL = "manual"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertType(str, Enum):
    MISSED_DOSE = "MISSED_DOSE"
    DRUG_HOLIDAY = "DRUG_HOLIDAY"
    DOSE_REMINDER = "DOSE_REMINDER"
    DAILY_SUMMARY = "DAILY_SUMMARY"
    PRE_VISIT_REPORT = "PRE_VISIT_REPORT"
    RISK_ESCALATION = "RISK_ESCALATION"


class WSEventType(str, Enum):
    DOSE_EVENT = "dose_event"
    RISK_UPDATE = "risk_update"
    ALERT_TRIGGERED = "alert_triggered"
