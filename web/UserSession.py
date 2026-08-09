"""Authenticate public requests with opaque server-side sessions."""

from __future__ import annotations

import os
from http.cookies import SimpleCookie
from typing import Any

from db.SessDb import SessDb
from mgr.SessMgr import SessMgr

SECURE_COOKIE_NAME = "__Host-xmr_session"
HTTP_COOKIE_NAME = "xmr_session"


class UserSession:
    def __init__(self) -> None:
        try:
            secret = bytes.fromhex(os.environ["XMR_SESSION_SECRET"])
        except (KeyError, ValueError) as error:
            raise RuntimeError("XMR_SESSION_SECRET is missing or invalid") from error
        self._sessions = SessMgr(SessDb(), secret)

    def resolve(self, scope: dict[str, Any]) -> int | None:
        token = _read_cookie(scope)
        if token is None:
            return None
        session = self._sessions.get_authenticated(token)
        return None if session is None else session.account_id

    def authenticate(self, account_id: int, *, secure: bool) -> bytes:
        anonymous = self._sessions.get_or_create(None)
        session = self._sessions.authenticate(anonymous, account_id)
        cookie = SimpleCookie()
        cookie_name = SECURE_COOKIE_NAME if secure else HTTP_COOKIE_NAME
        cookie[cookie_name] = session.token
        morsel = cookie[cookie_name]
        morsel["path"] = "/"
        morsel["max-age"] = "1800"
        morsel["secure"] = secure
        morsel["httponly"] = True
        morsel["samesite"] = "Lax"
        return morsel.OutputString().encode("ascii")


def _read_cookie(scope: dict[str, Any]) -> str | None:
    for name, value in scope.get("headers", ()):
        if name.lower() != b"cookie":
            continue
        cookie = SimpleCookie()
        try:
            cookie.load(value.decode("ascii"))
        except (UnicodeDecodeError, ValueError):
            return None
        for cookie_name in (SECURE_COOKIE_NAME, HTTP_COOKIE_NAME):
            morsel = cookie.get(cookie_name)
            if morsel is not None:
                return morsel.value
        return None
    return None
