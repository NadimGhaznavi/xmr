"""Authenticate public requests with opaque server-side sessions."""

from __future__ import annotations

import os
from http.cookies import SimpleCookie
from typing import Any

from db.SessDb import SessDb
from mgr.SessMgr import SessMgr

COOKIE_NAME = "__Host-xmr_session"


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

    def authenticate(self, account_id: int) -> bytes:
        anonymous = self._sessions.get_or_create(None)
        session = self._sessions.authenticate(anonymous, account_id)
        cookie = SimpleCookie()
        cookie[COOKIE_NAME] = session.token
        morsel = cookie[COOKIE_NAME]
        morsel["path"] = "/"
        morsel["max-age"] = "1800"
        morsel["secure"] = True
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
        morsel = cookie.get(COOKIE_NAME)
        return None if morsel is None else morsel.value
    return None
