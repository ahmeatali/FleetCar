import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import email_utils  # noqa: E402


class _Response:
    def __init__(self, body=b"{}"):
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class GmailApiDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "GMAIL_API_CLIENT_ID": "client-id",
            "GMAIL_API_CLIENT_SECRET": "client-secret",
            "GMAIL_API_REFRESH_TOKEN": "refresh-token",
            "GMAIL_API_SENDER": "fleet@example.com",
            "SMTP_HOST": "",
            "SMTP_USER": "",
            "SMTP_PASS": "",
        })
        self.env.start()
        self.load_env = patch.object(email_utils, "_load_env_file")
        self.load_env.start()

    def tearDown(self):
        self.load_env.stop()
        self.env.stop()

    @patch.object(email_utils, "urlopen")
    def test_verification_email_uses_gmail_https_api(self, urlopen):
        urlopen.side_effect = [
            _Response(json.dumps({"access_token": "short-lived-access-token"}).encode()),
            _Response(json.dumps({"id": "message-id"}).encode()),
        ]

        result = email_utils.send_email_verification_email(
            "customer@example.net", "Customer", "verification-token"
        )

        self.assertTrue(result["email_sent"])
        self.assertEqual(urlopen.call_count, 2)
        token_request, send_request = [call.args[0] for call in urlopen.call_args_list]
        self.assertEqual(token_request.full_url, "https://oauth2.googleapis.com/token")
        self.assertEqual(
            send_request.full_url,
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        )
        self.assertEqual(send_request.get_header("Authorization"), "Bearer short-lived-access-token")


if __name__ == "__main__":
    unittest.main()
