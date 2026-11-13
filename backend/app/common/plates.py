"""Turkish licence plates: one stored spelling, "34 ABC 123", whatever the user typed."""

import re

_PLATE = re.compile(r"(\d{2})([A-Z]{1,3})(\d{2,5})")


def compact_plate(value):
    """Spelling-insensitive key for comparing plates: no spaces, upper case."""
    return re.sub(r"\s+", "", str(value or "")).upper().replace("İ", "I")


def normalize_plate(value):
    """'34abc123', '34 ABC123' -> '34 ABC 123'. Anything that is not a Turkish plate is only
    trimmed and upper-cased, so foreign or temporary plates are kept as entered."""
    raw = compact_plate(value)
    match = _PLATE.fullmatch(raw)
    if match:
        return " ".join(match.groups())
    return re.sub(r"\s+", " ", str(value or "")).strip().upper().replace("İ", "I")
