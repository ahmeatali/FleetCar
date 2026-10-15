"""Canonical storage timestamps and Turkish business-day/assignment semantics."""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

BUSINESS_TIMEZONE = ZoneInfo("Europe/Istanbul")


def business_today():
    return datetime.now(BUSINESS_TIMEZONE).date()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def instant(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=BUSINESS_TIMEZONE)


def interval_contains(start, end, when):
    """Exact times are half-open; date-only handoffs intentionally remain ambiguous."""
    if not start or not when:
        return False
    moment = str(when)
    try:
        if len(moment) <= 10:
            date.fromisoformat(moment)
            return start[:10] <= moment and (not end or moment <= end[:10])
        return instant(start) <= instant(moment) and (not end or instant(moment) < instant(end))
    except (ValueError, TypeError):
        return False
