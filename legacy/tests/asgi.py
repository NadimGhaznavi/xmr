"""Small dependency-free ASGI request harness used by server tests."""

import asyncio
from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict[bytes, bytes]
    body: bytes


def request(
    app,
    path="/",
    *,
    method="GET",
    query=None,
    form=None,
    headers=(),
    scheme="http",
    client=("192.168.0.10", 50000),
):
    messages = []
    body = urlencode(form or {}).encode("utf-8")
    request_headers = list(headers)
    if form is not None:
        request_headers.append((b"content-type", b"application/x-www-form-urlencoded"))
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": scheme,
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": urlencode(query or {}).encode("utf-8"),
        "headers": request_headers,
        "client": client,
        "server": ("testserver", 80),
    }
    received = False

    async def receive():
        nonlocal received
        if received:
            return {"type": "http.disconnect"}
        received = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    asyncio.run(app(scope, receive, send))
    start = messages[0]
    body_parts = [message.get("body", b"") for message in messages[1:]]
    return Response(
        start["status"],
        dict(start.get("headers", ())),
        b"".join(body_parts),
    )
