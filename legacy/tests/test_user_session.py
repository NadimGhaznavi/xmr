"""Tests for the HTTP cookie adapter around server-side sessions."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from web.UserSession import (
    HTTP_COOKIE_NAME,
    SECURE_COOKIE_NAME,
    UserSession,
    _read_cookie,
)

TOKEN = "a" * 43


class UserSessionTest(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ, {"XMR_SESSION_SECRET": "ab" * 32, "XMR_DB_PASSWORD": "test"}
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    @patch("web.UserSession.SessMgr")
    def test_resolves_authenticated_cookie(self, manager_class):
        manager_class.return_value.get_authenticated.return_value = SimpleNamespace(
            account_id=7
        )
        session = UserSession()
        scope = {"headers": [(b"cookie", f"{SECURE_COOKIE_NAME}={TOKEN}".encode())]}
        self.assertEqual(session.resolve(scope), 7)
        manager_class.return_value.get_authenticated.assert_called_once_with(TOKEN)

    @patch("web.UserSession.SessMgr")
    def test_missing_or_unknown_session_is_anonymous(self, manager_class):
        manager_class.return_value.get_authenticated.return_value = None
        session = UserSession()
        self.assertIsNone(session.resolve({"headers": []}))
        self.assertIsNone(
            session.resolve(
                {"headers": [(b"cookie", f"{HTTP_COOKIE_NAME}={TOKEN}".encode())]}
            )
        )

    @patch("web.UserSession.SessMgr")
    def test_authentication_cookie_security_matches_transport(self, manager_class):
        manager_class.return_value.get_or_create.return_value = SimpleNamespace()
        manager_class.return_value.authenticate.return_value = SimpleNamespace(
            token=TOKEN
        )
        session = UserSession()
        secure = session.authenticate(7, secure=True)
        insecure = session.authenticate(7, secure=False)
        self.assertIn(SECURE_COOKIE_NAME.encode(), secure)
        self.assertIn(b"Secure", secure)
        self.assertIn(HTTP_COOKIE_NAME.encode(), insecure)
        self.assertNotIn(b"Secure", insecure)
        for cookie in (secure, insecure):
            self.assertIn(b"HttpOnly", cookie)
            self.assertIn(b"SameSite=Lax", cookie)
            self.assertIn(b"Max-Age=1800", cookie)

    def test_rejects_missing_or_invalid_secret(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "missing or invalid"):
                UserSession()
        with patch.dict(os.environ, {"XMR_SESSION_SECRET": "not-hex"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "missing or invalid"):
                UserSession()

    def test_cookie_reader_handles_malformed_and_both_names(self):
        self.assertIsNone(_read_cookie({"headers": [(b"cookie", b"\xff")]}))
        scope = {
            "headers": [
                (
                    b"cookie",
                    f"{HTTP_COOKIE_NAME}=http; {SECURE_COOKIE_NAME}=secure".encode(),
                )
            ]
        }
        self.assertEqual(_read_cookie(scope), "secure")


if __name__ == "__main__":
    unittest.main()
