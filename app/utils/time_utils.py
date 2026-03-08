"""
time_utils.py – Datetime helpers.
"""
from datetime import datetime, timezone, timedelta


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def utcnow_str() -> str:
    return utcnow().isoformat()


def parse_iso(ts: str) -> datetime:
    """Parse ISO-8601 string, attach UTC tzinfo if naive."""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def minutes_since(ts: str) -> float:
    """Return minutes elapsed since ts (ISO string)."""
    return (utcnow() - parse_iso(ts)).total_seconds() / 60


def hours_since(ts: str) -> float:
    """Return hours elapsed since ts (ISO string)."""
    return (utcnow() - parse_iso(ts)).total_seconds() / 3600


def today_start_utc() -> datetime:
    """Return start of today (UTC)."""
    n = utcnow()
    return n.replace(hour=0, minute=0, second=0, microsecond=0)


def week_start_utc() -> datetime:
    """Return start of the current week (Monday, UTC)."""
    n = utcnow()
    monday = n - timedelta(days=n.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def scheduled_datetime_today(schedule_time: str) -> datetime:
    """
    Build today's scheduled datetime from HH:MM string.
    Returns a UTC-aware datetime.
    """
    h, m = map(int, schedule_time.split(":"))
    return utcnow().replace(hour=h, minute=m, second=0, microsecond=0)
