"""LAN-only account administration ASGI server."""

from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import hmac
import logging
import os
from ipaddress import IPv4Network, ip_address, ip_network
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from constants.DDefaults import DDefault
from db.AdminDb import AdminDb
from web.Interface import Route, Send
from web.Server import Server

LOG = logging.getLogger(__name__)
TEMPLATES = Environment(
    loader=FileSystemLoader(Path(__file__).with_name("templates")),
    autoescape=select_autoescape(("html", "xml")),
    undefined=StrictUndefined,
)
ROUTES = {
    ("GET", "/"): Route("AdminMgr:list_accounts", "accounts.html", blocking=True),
    ("HEAD", "/"): Route("AdminMgr:list_accounts", "accounts.html", blocking=True),
    ("GET", "/account"): Route(
        "AdminMgr:edit_account", "edit-account.html", blocking=True
    ),
    ("HEAD", "/account"): Route(
        "AdminMgr:edit_account", "edit-account.html", blocking=True
    ),
    ("GET", "/health"): Route("AdminMgr:health"),
    ("HEAD", "/health"): Route("AdminMgr:health"),
    ("GET", "/img/logo.png"): Route("AdminMgr:logo", blocking=True),
    ("HEAD", "/img/logo.png"): Route("AdminMgr:logo", blocking=True),
}
ACTIONS = {
    "AdminMgr:update_account": Route(
        "AdminMgr:update_account", "edit-account.html", blocking=True
    ),
    "AdminMgr:disable_account": Route(
        "AdminMgr:disable_account", "edit-account.html", blocking=True
    ),
    "AdminMgr:enable_account": Route(
        "AdminMgr:enable_account", "edit-account.html", blocking=True
    ),
}


class AdminServer(Server):
    """Restrict account administration to trusted LAN clients and the hot DB."""

    def __init__(self) -> None:
        trusted_lan = os.getenv("XMR_TRUSTED_LAN", DDefault.TRUSTED_LAN)
        network = ip_network(trusted_lan, strict=True)
        if not isinstance(network, IPv4Network):
            raise ValueError("XMR_TRUSTED_LAN must be an IPv4 network")
        self._trusted_lan = network
        self._authentication = BasicAuthentication.from_env()
        self._database = AdminDb()
        super().__init__(
            ROUTES,
            ACTIONS,
            templates=TEMPLATES,
            not_found_target="AdminMgr:not_found",
            method_not_allowed_target="AdminMgr:method_not_allowed",
        )

    def client_is_allowed(self, scope: dict[str, Any]) -> bool:
        client = scope.get("client")
        if not client:
            return False
        try:
            allowed = ip_address(str(client[0])) in self._trusted_lan
        except ValueError:
            allowed = False
        if not allowed:
            LOG.warning("Rejected admin connection from %s", client[0])
        return allowed

    async def request_is_authenticated(self, scope: dict[str, Any]) -> bool:
        return await asyncio.to_thread(self._authentication.verify, scope)

    async def site_data_is_available(self, scope: dict[str, Any]) -> bool:
        if scope.get("path") in {"/health", "/img/logo.png"}:
            return True
        return await asyncio.to_thread(self._database.site_data_is_writable)

    async def reject_unavailable(self, scope: dict[str, Any], send: Send) -> None:
        include_body = str(scope["method"]).upper() != "HEAD"
        body = TEMPLATES.get_template("cold.html").render().encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 503,
                "headers": [
                    (b"content-type", b"text/html; charset=utf-8"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send(
            {"type": "http.response.body", "body": body if include_body else b""}
        )


class BasicAuthentication:
    """Verify the dedicated browser credential without storing its plaintext."""

    def __init__(self, username: str, encoded_hash: str) -> None:
        fields = encoded_hash.split("$")
        if len(fields) != 6 or fields[0] != "scrypt":
            raise ValueError("XMR_ADMIN_WEB_PASSWORD_HASH has an invalid format")
        try:
            self._n, self._r, self._p = (int(value) for value in fields[1:4])
            self._salt = base64.b64decode(fields[4], validate=True)
            self._digest = base64.b64decode(fields[5], validate=True)
        except (ValueError, binascii.Error) as error:
            raise ValueError(
                "XMR_ADMIN_WEB_PASSWORD_HASH has an invalid format"
            ) from error
        if not username or not self._salt or len(self._digest) != 32:
            raise ValueError("admin browser credentials are invalid")
        self._username = username

    @classmethod
    def from_env(cls) -> BasicAuthentication:
        return cls(
            os.getenv("XMR_ADMIN_WEB_USER", ""),
            os.getenv("XMR_ADMIN_WEB_PASSWORD_HASH", ""),
        )

    def verify(self, scope: dict[str, Any]) -> bool:
        supplied = _basic_credentials(scope)
        if supplied is None:
            return False
        username, password = supplied
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=self._salt,
            n=self._n,
            r=self._r,
            p=self._p,
            dklen=len(self._digest),
        )
        return hmac.compare_digest(username, self._username) and hmac.compare_digest(
            digest, self._digest
        )


def _basic_credentials(scope: dict[str, Any]) -> tuple[str, str] | None:
    for name, value in scope.get("headers", ()):
        if name.lower() != b"authorization":
            continue
        try:
            scheme, encoded = value.decode("ascii").split(" ", maxsplit=1)
            if scheme.lower() != "basic":
                return None
            decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
            username, separator, password = decoded.partition(":")
            return (username, password) if separator else None
        except (ValueError, UnicodeDecodeError, binascii.Error):
            return None
    return None


app = AdminServer()


if __name__ == "__main__":
    import uvicorn  # type: ignore[import-not-found]

    uvicorn.run(
        app,
        # AdminServer rejects peers outside TRUSTED_LAN before authentication.
        host="0.0.0.0",  # nosec B104
        port=int(DDefault.ADMIN_PORT),
        server_header=False,
    )
