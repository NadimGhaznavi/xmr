"""Adapt registered application operations to ASGI and Jinja."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

Message = dict[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
Arguments = Mapping[str, str]


@dataclass(frozen=True, slots=True)
class ViewResult:
    context: Mapping[str, Any] = field(default_factory=dict)
    status: int = 200


@dataclass(frozen=True, slots=True)
class RedirectResult:
    location: str
    status: int = 303


@dataclass(frozen=True, slots=True)
class JsonResult:
    payload: Mapping[str, Any]
    status: int = 200


Result = ViewResult | RedirectResult | JsonResult
Operation = Callable[[Arguments], Result]
Handler = Callable[[dict[str, Any], Receive, Send], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class Route:
    target: str
    template: str | None = None
    blocking: bool = False


TEMPLATES = Environment(
    loader=FileSystemLoader(Path(__file__).with_name("templates")),
    autoescape=select_autoescape(("html", "xml")),
    undefined=StrictUndefined,
)


def compile_route(route: Route) -> Handler:
    operation = _resolve(route.target)

    async def handle(scope: dict[str, Any], receive: Receive, send: Send) -> None:
        arguments = await _read_arguments(scope, receive)
        result = await _run(route, operation, arguments)
        await _respond(scope, send, route, result)

    return handle


def compile_dispatch(routes: Mapping[str, Route]) -> Handler:
    operations = {target: _resolve(route.target) for target, route in routes.items()}

    async def dispatch(scope: dict[str, Any], receive: Receive, send: Send) -> None:
        try:
            arguments = await _read_arguments(scope, receive)
        except (UnicodeDecodeError, ValueError):
            await _send_json(send, 400, {"error": "invalid_request"})
            return

        target = f"{arguments.pop('MODULE', '')}:{arguments.pop('METHOD', '')}"
        route = routes.get(target)
        if route is None:
            await _send_json(send, 404, {"error": "unknown_operation"})
            return

        result = await _run(route, operations[target], arguments)
        await _respond(scope, send, route, result)

    return dispatch


def _resolve(target: str) -> Operation:
    module_name, method_name = target.split(":", maxsplit=1)
    operation = getattr(import_module(f"mgr.{module_name}"), method_name)
    if not callable(operation):
        raise TypeError(f"route target is not callable: {target}")
    return operation


async def _run(route: Route, operation: Operation, arguments: Arguments) -> Result:
    if route.blocking:
        return await asyncio.to_thread(operation, arguments)
    return operation(arguments)


async def _read_arguments(scope: dict[str, Any], receive: Receive) -> dict[str, str]:
    if str(scope["method"]).upper() not in {"POST", "PUT", "PATCH"}:
        return {}
    body = await _read_body(receive)
    values = parse_qs(body.decode("utf-8"), keep_blank_values=True, max_num_fields=32)
    return {name: entries[0] for name, entries in values.items()}


async def _read_body(receive: Receive, *, limit: int = 16_384) -> bytes:
    body = bytearray()
    while True:
        message = await receive()
        if message["type"] != "http.request":
            continue
        body.extend(message.get("body", b""))
        if len(body) > limit:
            raise ValueError("request body is too large")
        if not message.get("more_body", False):
            return bytes(body)


async def _respond(
    scope: dict[str, Any], send: Send, route: Route, result: Result
) -> None:
    include_body = str(scope["method"]).upper() != "HEAD"
    if isinstance(result, RedirectResult):
        await _send_redirect(send, result.status, result.location)
    elif isinstance(result, JsonResult):
        await _send_json(send, result.status, result.payload, include_body=include_body)
    elif route.template is None:
        raise RuntimeError(f"route {route.target} has no template")
    else:
        content = TEMPLATES.get_template(route.template).render(**result.context)
        await _send_html(send, result.status, content, include_body=include_body)


async def _send_json(
    send: Send,
    status: int,
    payload: Mapping[str, Any],
    *,
    include_body: bool = True,
) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body if include_body else b""})


async def _send_html(
    send: Send, status: int, content: str, *, include_body: bool = True
) -> None:
    body = content.encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"text/html; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body if include_body else b""})


async def _send_redirect(send: Send, status: int, location: str) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"location", location.encode("ascii")),
                (b"content-length", b"0"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": b""})
