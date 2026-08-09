"""Tests for LAN, Basic Auth, and hot/cold admin boundaries."""

import base64
import hashlib
import os
import unittest

from tests.asgi import request

PASSWORD = "long-admin-password"
SALT = b"0123456789abcdef"
DIGEST = hashlib.scrypt(PASSWORD.encode(), salt=SALT, n=16384, r=8, p=1, dklen=32)
ENCODED_HASH = "scrypt$16384$8$1${}${}".format(
    base64.b64encode(SALT).decode(), base64.b64encode(DIGEST).decode()
)
os.environ.setdefault("XMR_ADMIN_DB_PASSWORD", "database-password")
os.environ.setdefault("XMR_ADMIN_WEB_USER", "xmradmin")
os.environ.setdefault("XMR_ADMIN_WEB_PASSWORD_HASH", ENCODED_HASH)

from admin.server import AdminServer, BasicAuthentication  # noqa: E402


class Authentication:
    def __init__(self, allowed):
        self.allowed = allowed

    def verify(self, scope):
        return self.allowed


class Database:
    def __init__(self, writable):
        self.writable = writable
        self.checks = 0

    def site_data_is_writable(self):
        self.checks += 1
        return self.writable


class AdminServerTest(unittest.TestCase):
    def server(self, *, authenticated=True, writable=True):
        server = AdminServer()
        server._authentication = Authentication(authenticated)
        server._database = Database(writable)
        return server

    def test_rejects_client_outside_trusted_lan_before_authentication(self):
        server = self.server()
        response = request(server, client=("203.0.113.5", 50000))
        self.assertEqual(response.status, 403)
        self.assertEqual(server._database.checks, 0)

    def test_requires_basic_authentication_inside_lan(self):
        response = request(self.server(authenticated=False))
        self.assertEqual(response.status, 401)
        self.assertIn(b"Basic realm", response.headers[b"www-authenticate"])

    def test_cold_node_returns_service_unavailable_for_site_data(self):
        response = request(self.server(writable=False))
        self.assertEqual(response.status, 503)
        self.assertIn(b"cold cluster node", response.body)

    def test_health_bypasses_database_role_but_not_authentication(self):
        server = self.server(writable=False)
        response = request(server, "/health")
        self.assertEqual(response.status, 200)
        self.assertEqual(server._database.checks, 0)

    def test_basic_auth_accepts_only_matching_credentials(self):
        authentication = BasicAuthentication("xmradmin", ENCODED_HASH)

        def scope(username, password):
            value = base64.b64encode(f"{username}:{password}".encode())
            return {"headers": [(b"authorization", b"Basic " + value)]}

        self.assertTrue(authentication.verify(scope("xmradmin", PASSWORD)))
        self.assertFalse(authentication.verify(scope("other", PASSWORD)))
        self.assertFalse(authentication.verify(scope("xmradmin", "wrong")))
        self.assertFalse(authentication.verify({"headers": []}))

    def test_rejects_invalid_hash_configuration(self):
        with self.assertRaisesRegex(ValueError, "invalid format"):
            BasicAuthentication("xmradmin", "not-a-hash")
        with self.assertRaisesRegex(ValueError, "credentials are invalid"):
            BasicAuthentication("", ENCODED_HASH)


if __name__ == "__main__":
    unittest.main()
