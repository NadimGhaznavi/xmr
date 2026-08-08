"""ASGI middleware for opaque, server-side sessions."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from http.cookies import SimpleCookie
from typing import Any

from mgr.SessMgr import SessMgr

ASGIApp = Callable[[dict[str, Any], Callable[..., Awaitable[Any]], Callable[..., Awaitable[Any]]], Awaitable[None]]


class ServerSessionMiddleware:
    """Resolve a database session and expose it as ``scope['xmr.session']``."""

    def __init__(
        self,
        app: ASGIApp,
        sessions: SessMgr,
        *,
        cookie_name: str = "__Host-xmr_session",
    ) -> None:
        self._app = app
        self._sessions = sessions
        self._cookie_name = cookie_name

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        supplied_token = self._read_cookie(scope)
        session = await asyncio.to_thread(self._sessions.get_or_create, supplied_token)
        scope["xmr.session"] = session

        async def send_with_cookie(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", ()))
                headers.append((b"set-cookie", self._cookie_value(session.token)))
                message = {**message, "headers": headers}
            await send(message)

        await self._app(scope, receive, send_with_cookie)

    def _read_cookie(self, scope: dict[str, Any]) -> str | None:
        for name, value in scope.get("headers", ()):
            if name.lower() != b"cookie":
                continue
            cookie = SimpleCookie()
            try:
                cookie.load(value.decode("ascii"))
            except (UnicodeDecodeError, ValueError):
                return None
            morsel = cookie.get(self._cookie_name)
            return None if morsel is None else morsel.value
        return None

    def _cookie_value(self, token: str) -> bytes:
        cookie = SimpleCookie()
        cookie[self._cookie_name] = token
        morsel = cookie[self._cookie_name]
        morsel["path"] = "/"
        morsel["max-age"] = "1800"
        morsel["secure"] = True
        morsel["httponly"] = True
        morsel["samesite"] = "Lax"
        return morsel.OutputString().encode("ascii")
