"""Shared lean ASGI server and route dispatch."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jinja2 import Environment

from web.Interface import (
    TEMPLATES,
    Handler,
    Receive,
    Route,
    Send,
    compile_dispatch,
    compile_route,
)


class Server:
    """Route requests through a fixed, server-owned operation registry."""

    def __init__(
        self,
        routes: Mapping[tuple[str, str], Route],
        actions: Mapping[str, Route],
        *,
        templates: Environment = TEMPLATES,
        not_found_target: str = "AppMgr:not_found",
        method_not_allowed_target: str = "AppMgr:method_not_allowed",
    ) -> None:
        self._templates = templates
        self._routes: dict[tuple[str, str], Handler] = {
            route: compile_route(definition, templates)
            for route, definition in routes.items()
        }
        if actions:
            self._routes[("POST", "/api")] = compile_dispatch(actions, templates)
        self._not_found = compile_route(Route(not_found_target), templates)
        self._method_not_allowed = compile_route(
            Route(method_not_allowed_target), templates
        )
        self._known_paths = {path for _, path in self._routes}

    async def __call__(
        self, scope: dict[str, Any], receive: Receive, send: Send
    ) -> None:
        if scope["type"] == "http":
            if not self.client_is_allowed(scope):
                await self.reject_client(scope, send)
                return
            if not await self.site_data_is_available(scope):
                await self.reject_unavailable(scope, send)
                return
            await self._route(scope, receive, send)
        elif scope["type"] == "lifespan":
            await self._handle_lifespan(receive, send)

    def client_is_allowed(self, scope: dict[str, Any]) -> bool:
        del scope
        return True

    async def site_data_is_available(self, scope: dict[str, Any]) -> bool:
        del scope
        return True

    async def reject_client(self, scope: dict[str, Any], send: Send) -> None:
        del scope
        await _plain_response(send, 403, "Forbidden")

    async def reject_unavailable(self, scope: dict[str, Any], send: Send) -> None:
        del scope
        await _plain_response(send, 503, "Site administration is unavailable")

    async def _route(self, scope: dict[str, Any], receive: Receive, send: Send) -> None:
        route = (str(scope["method"]).upper(), str(scope["path"]))
        handler = self._routes.get(route)
        if handler is None:
            handler = (
                self._method_not_allowed
                if route[1] in self._known_paths
                else self._not_found
            )
        await handler(scope, receive, send)

    @staticmethod
    async def _handle_lifespan(receive: Receive, send: Send) -> None:
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return


async def _plain_response(send: Send, status: int, content: str) -> None:
    body = content.encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"text/plain; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})
