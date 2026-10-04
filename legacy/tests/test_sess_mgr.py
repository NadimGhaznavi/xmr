"""Tests for opaque server-side session management."""

import hashlib
import hmac
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from mgr.SessMgr import SessMgr

SECRET = b"s" * 32
TOKEN = "a" * 43
ROTATED = "b" * 43


class Sessions:
    def __init__(self):
        self.row = None
        self.touch_result = True
        self.rotate_result = True
        self.created = []
        self.touched = []
        self.rotated = []
        self.revoked = []
        self.lookups = []

    def find_active(self, digest, now):
        self.lookups.append((digest, now))
        return self.row

    def create(self, digest, created_at, expires_at, absolute_expires_at):
        self.created.append((digest, created_at, expires_at, absolute_expires_at))
        return 11

    def touch(self, session_id, now, expires_at):
        self.touched.append((session_id, now, expires_at))
        return self.touch_result

    def authenticate_and_rotate(self, *arguments):
        self.rotated.append(arguments)
        return self.rotate_result

    def revoke(self, digest, now):
        self.revoked.append((digest, now))


class SessMgrTest(unittest.TestCase):
    def test_validates_secret_and_lifetimes(self):
        database = Sessions()
        with self.assertRaisesRegex(ValueError, "at least 32 bytes"):
            SessMgr(database, b"short")
        with self.assertRaisesRegex(ValueError, "invalid session lifetime"):
            SessMgr(database, SECRET, idle_timeout=timedelta(0))
        with self.assertRaisesRegex(ValueError, "invalid session lifetime"):
            SessMgr(
                database,
                SECRET,
                idle_timeout=timedelta(hours=2),
                absolute_lifetime=timedelta(hours=1),
            )

    @patch("mgr.SessMgr.secrets.token_urlsafe", return_value=TOKEN)
    def test_creates_hmac_digested_session(self, unused_token):
        del unused_token
        database = Sessions()
        session = SessMgr(database, SECRET).get_or_create(None)
        digest = hmac.new(SECRET, TOKEN.encode("ascii"), hashlib.sha256).digest()
        self.assertEqual((session.session_id, session.token), (11, TOKEN))
        self.assertEqual(database.created[0][0], digest)
        self.assertEqual(
            session.expires_at - database.created[0][1], timedelta(minutes=30)
        )
        self.assertEqual(
            session.absolute_expires_at - database.created[0][1], timedelta(hours=12)
        )

    def test_reuses_and_touches_active_session(self):
        database = Sessions()
        database.row = {
            "id": 5,
            "account_id": None,
            "authenticated": False,
            "absolute_expires_at": datetime.now() + timedelta(hours=1),
        }
        session = SessMgr(database, SECRET).get_or_create(TOKEN)
        self.assertEqual((session.session_id, session.token), (5, TOKEN))
        self.assertEqual(len(database.touched), 1)
        self.assertEqual(database.created, [])

    def test_invalid_token_is_not_queried_or_revoked(self):
        database = Sessions()
        manager = SessMgr(database, SECRET)
        self.assertIsNone(manager.get_authenticated("bad token"))
        manager.revoke("bad token")
        self.assertEqual((database.lookups, database.revoked), ([], []))

    def test_resolves_authenticated_session(self):
        database = Sessions()
        database.row = {
            "id": 5,
            "account_id": 7,
            "authenticated": True,
            "absolute_expires_at": datetime.now() + timedelta(hours=1),
        }
        session = SessMgr(database, SECRET).get_authenticated(TOKEN)
        self.assertIsNotNone(session)
        self.assertEqual(session.account_id, 7)
        self.assertTrue(session.authenticated)

    @patch("mgr.SessMgr.secrets.token_urlsafe", return_value=ROTATED)
    def test_authentication_rotates_token(self, unused_token):
        del unused_token
        database = Sessions()
        manager = SessMgr(database, SECRET)
        with patch("mgr.SessMgr.secrets.token_urlsafe", return_value=TOKEN):
            anonymous = manager._create(datetime.now())
        result = manager.authenticate(anonymous, 7)
        self.assertEqual((result.token, result.account_id), (ROTATED, 7))
        self.assertTrue(result.authenticated)
        self.assertNotEqual(database.rotated[0][2], database.rotated[0][3])

    def test_failed_rotation_and_valid_revoke(self):
        database = Sessions()
        database.rotate_result = False
        manager = SessMgr(database, SECRET)
        with patch("mgr.SessMgr.secrets.token_urlsafe", return_value=TOKEN):
            anonymous = manager._create(datetime.now())
        with self.assertRaisesRegex(RuntimeError, "expired or was revoked"):
            manager.authenticate(anonymous, 7)
        manager.revoke(TOKEN)
        self.assertEqual(len(database.revoked), 1)


if __name__ == "__main__":
    unittest.main()
