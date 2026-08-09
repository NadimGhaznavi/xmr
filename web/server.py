"""Lean ASGI route dispatcher for the Bear and Moose XMR backend."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from web.Interface import Handler, Route, compile_dispatch, compile_route

ASGIMessage = dict[str, Any]
Receive = Callable[[], Awaitable[ASGIMessage]]
Send = Callable[[ASGIMessage], Awaitable[None]]
ROUTE_DEFINITIONS = {
    ("GET", "/"): Route("AppMgr:index"),
    ("HEAD", "/"): Route("AppMgr:index"),
    ("GET", "/health"): Route("AppMgr:health"),
    ("HEAD", "/health"): Route("AppMgr:health"),
    ("GET", "/login"): Route("AppMgr:login", "login.html"),
    ("HEAD", "/login"): Route("AppMgr:login", "login.html"),
    ("GET", "/signup"): Route("AppMgr:signup", "signup.html"),
    ("HEAD", "/signup"): Route("AppMgr:signup", "signup.html"),
}
ACTION_DEFINITIONS = {
    "AppMgr:new_account": Route(
        "AppMgr:new_account",
        "dashboard.html",
        error_template="signup.html",
        blocking=True,
    ),
}

ROUTES: dict[tuple[str, str], Handler] = {
    route: compile_route(definition) for route, definition in ROUTE_DEFINITIONS.items()
}
ROUTES[("POST", "/api")] = compile_dispatch(ACTION_DEFINITIONS)
NOT_FOUND = compile_route(Route("AppMgr:not_found"))
METHOD_NOT_ALLOWED = compile_route(Route("AppMgr:method_not_allowed"))
KNOWN_PATHS = {path for _, path in ROUTES}


async def _route(scope: dict[str, Any], receive: Receive, send: Send) -> None:
    route = (str(scope["method"]).upper(), str(scope["path"]))
    handler = ROUTES.get(route)
    if handler is None:
        handler = METHOD_NOT_ALLOWED if route[1] in KNOWN_PATHS else NOT_FOUND
    await handler(scope, receive, send)


async def _handle_lifespan(receive: Receive, send: Send) -> None:
    while True:
        message = await receive()
        if message["type"] == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
        elif message["type"] == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})
            return


async def app(scope: dict[str, Any], receive: Receive, send: Send) -> None:
    """Dispatch an ASGI request."""

    if scope["type"] == "http":
        await _route(scope, receive, send)
    elif scope["type"] == "lifespan":
        await _handle_lifespan(receive, send)
