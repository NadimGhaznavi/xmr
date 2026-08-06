"""ASGI entry point for the Bear and Moose XMR backend."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

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


async def _send_redirect(send: Send, location: str) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 303,
            "headers": [(b"location", location.encode("ascii")), (b"content-length", b"0")],
        }
    )
    await send({"type": "http.response.body", "body": b""})


async def _read_request_body(receive: Receive, *, limit: int = 16_384) -> bytes:
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


def _render_signup(**context: Any) -> str:
    defaults: dict[str, Any] = {
        "errors": {},
        "form_error": "",
        "username": "",
        "wallet": "",
    }
    defaults.update(context)
    return TEMPLATES.get_template("signup.html").render(**defaults)


async def _handle_signup(receive: Receive, send: Send) -> None:
    from application.new_acct import (
        AccountAlreadyExistsError,
        AccountValidationError,
        NewAccount,
    )

    try:
        raw_body = await _read_request_body(receive)
        values = parse_qs(
            raw_body.decode("utf-8"), keep_blank_values=True, max_num_fields=10
        )
    except (UnicodeDecodeError, ValueError):
        await _send_html(
            send, 400, _render_signup(form_error="Invalid signup request.")
        )
        return

    username = values.get("username", [""])[0]
    password = values.get("password", [""])[0]
    wallet = values.get("wallet", [""])[0]

    try:
        await asyncio.to_thread(NewAccount().execute, username, password, wallet)
    except AccountValidationError as error:
        await _send_html(
            send,
            422,
            _render_signup(
                errors=error.errors,
                username=username,
                wallet=wallet,
            ),
        )
        return
    except AccountAlreadyExistsError:
        await _send_html(
            send,
            409,
            _render_signup(
                form_error="That username or wallet is already registered.",
                username=username,
                wallet=wallet,
            ),
        )
        return

    await _send_redirect(send, "/login?created=1")


async def _handle_http(scope: dict[str, Any], receive: Receive, send: Send) -> None:
    method = scope["method"].upper()
    path = scope["path"]

    if method == "POST" and path == "/signup":
        await _handle_signup(receive, send)
        return

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
        content = _render_signup() if path == "/signup" else template.render()
        await _send_html(send, 200, content, include_body=method != "HEAD")
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
        await _handle_http(scope, receive, send)
