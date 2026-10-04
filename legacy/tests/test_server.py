"""Tests for public ASGI routing, forms, and authentication boundaries."""

import json
import unittest
from unittest.mock import patch

from db.AppDb import User
from tests.asgi import request
from web.server import app

WALLET = "4" + "1" * 94


class ServerTest(unittest.TestCase):
    def test_health(self):
        response = request(app, "/health")
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(response.body), {"status": "ok"})

    def test_missing_route(self):
        response = request(app, "/missing")
        self.assertEqual(response.status, 404)
        self.assertEqual(json.loads(response.body), {"error": "not_found"})

    def test_known_path_with_wrong_method(self):
        response = request(app, "/login", method="POST")
        self.assertEqual(response.status, 405)
        self.assertEqual(json.loads(response.body), {"error": "method_not_allowed"})

    def test_unknown_api_operation(self):
        response = request(
            app,
            "/api",
            method="POST",
            form={"MODULE": "AppMgr", "METHOD": "missing"},
        )
        self.assertEqual(response.status, 404)
        self.assertEqual(json.loads(response.body), {"error": "unknown_operation"})

    def test_head_omits_body_but_preserves_content_length(self):
        get_response = request(app, "/health")
        head_response = request(app, "/health", method="HEAD")
        self.assertEqual(head_response.status, 200)
        self.assertEqual(head_response.body, b"")
        self.assertEqual(
            head_response.headers[b"content-length"],
            get_response.headers[b"content-length"],
        )

    def test_login_and_signup_render_current_forms(self):
        login = request(app, "/login")
        signup = request(app, "/signup")
        self.assertEqual((login.status, signup.status), (200, 200))
        self.assertIn(b'<form method="post" action="/api">', login.body)
        self.assertIn(b'name="METHOD" value="authenticate"', login.body)
        self.assertIn(b"Monero wallet address", signup.body)

    @patch("web.UserSession.UserSession")
    def test_protected_route_redirects_without_authenticated_session(self, sessions):
        sessions.return_value.resolve.return_value = None
        response = request(app, "/dashboard")
        self.assertEqual(response.status, 303)
        self.assertEqual(response.headers[b"location"], b"/login")

    @patch("mgr.AppMgr.PoolMgr")
    @patch("mgr.AppMgr.AppDb")
    @patch("web.UserSession.UserSession")
    def test_dashboard_uses_account_from_session(self, sessions, accounts, pools):
        sessions.return_value.resolve.return_value = 7
        accounts.return_value.get_user.return_value = User(7, "miner", WALLET, "user")
        pools.return_value.list_pools.return_value = []
        response = request(app, "/dashboard")
        self.assertEqual(response.status, 200)
        self.assertIn(b"miner", response.body)
        accounts.return_value.get_user.assert_called_once_with(7)

    @patch("mgr.AppMgr.PoolMgr")
    @patch("mgr.AppMgr.AcctMgr")
    @patch("web.UserSession.UserSession")
    def test_successful_login_sets_rotated_session_cookie(
        self, sessions, accounts, pools
    ):
        accounts.return_value.authenticate.return_value = User(
            7, "miner", WALLET, "user"
        )
        pools.return_value.list_pools.return_value = []
        sessions.return_value.authenticate.return_value = (
            b"xmr_session=token; HttpOnly; Path=/; SameSite=Lax"
        )
        response = request(
            app,
            "/api",
            method="POST",
            form={
                "MODULE": "AppMgr",
                "METHOD": "authenticate",
                "username": "miner",
                "password": "correct",
            },
        )
        self.assertEqual(response.status, 200)
        self.assertIn(b"miner", response.body)
        self.assertIn(b"xmr_session=token", response.headers[b"set-cookie"])
        sessions.return_value.authenticate.assert_called_once_with(7, secure=False)

    @patch("mgr.AppMgr.AcctMgr")
    def test_invalid_login_uses_login_error_template(self, accounts):
        from mgr.AcctMgr import InvalidCredentialsError

        accounts.return_value.authenticate.side_effect = InvalidCredentialsError()
        response = request(
            app,
            "/api",
            method="POST",
            form={
                "MODULE": "AppMgr",
                "METHOD": "authenticate",
                "username": "miner",
                "password": "wrong",
            },
        )
        self.assertEqual(response.status, 401)
        self.assertIn(b"Invalid username or password", response.body)


if __name__ == "__main__":
    unittest.main()
