"""ASGI entry point for the Bear and Moose XMR backend."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ASGIMessage = dict[str, Any]
Receive = Callable[[], Awaitable[ASGIMessage]]
Send = Callable[[ASGIMessage], Awaitable[None]]

TEMPLATES = Environment(
    loader=FileSystemLoader(Path(__file__).with_name("templates")),
    autoescape=select_autoescape(("html", "xml")),
    undefined=StrictUndefined,
)


async def _send_json(
    send: Send,
    status: int,
    payload: dict[str, Any],
    *,
    include_body: bool = True,
) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode("ascii")),
    ]

    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": headers,
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": body if include_body else b"",
        }
    )


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


async def _handle_http(scope: dict[str, Any], send: Send) -> None:
    method = scope["method"].upper()
    path = scope["path"]

    if method not in {"GET", "HEAD"}:
        await _send_json(
            send,
            405,
            {"error": "method_not_allowed"},
            include_body=method != "HEAD",
        )
        return

    if path == "/health":
        status = 200
        payload = {"status": "ok"}
    elif path in {"/login", "/signup"}:
        template = TEMPLATES.get_template(f"{path[1:]}.html")
        await _send_html(send, 200, template.render(), include_body=method != "HEAD")
        return
    elif path == "/":
        status = 200
        payload = {"name": "Bear and Moose XMR API", "status": "ok"}
    else:
        status = 404
        payload = {"error": "not_found"}

    await _send_json(send, status, payload, include_body=method != "HEAD")


async def _handle_lifespan(receive: Receive, send: Send) -> None:
    while True:
        message = await receive()

        if message["type"] == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
        elif message["type"] == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})
            return


async def app(scope: dict[str, Any], receive: Receive, send: Send) -> None:
    """Serve the backend API using the ASGI protocol."""

    if scope["type"] == "lifespan":
        await _handle_lifespan(receive, send)
    elif scope["type"] == "http":
        await _handle_http(scope, send)
