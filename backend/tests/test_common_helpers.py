import unittest
from datetime import datetime, timedelta, timezone

from app.common.security import session_expired, token_digest
from app.common.time import instant, interval_contains


class CommonHelperTests(unittest.TestCase):
    def test_assignment_handoffs_are_half_open_for_exact_times(self):
        handoff = "2026-10-15T12:00:00+03:00"
        self.assertFalse(interval_contains("2026-10-01", handoff, handoff))
        self.assertTrue(interval_contains(handoff, None, "2026-10-15T09:00:00Z"))
        self.assertTrue(interval_contains("2026-10-01", handoff, "2026-10-15"))
        self.assertTrue(interval_contains(handoff, None, "2026-10-15"))
        self.assertFalse(interval_contains("invalid", None, "2026-10-15T09:00:00Z"))
        self.assertFalse(interval_contains("2026-10-01", None, ""))
        self.assertEqual(instant("2026-10-15T12:00:00").utcoffset(), timedelta(hours=3))

    def test_invalid_or_naive_expiry_fails_closed(self):
        for value in [
            None,
            "invalid",
            "2026-10-15T12:00:00",
            (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
        ]:
            self.assertTrue(session_expired(value))
        self.assertFalse(
            session_expired((datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())
        )
        self.assertEqual(len(token_digest("fixture")), 64)
        self.assertNotEqual(token_digest("fixture"), token_digest("other"))
