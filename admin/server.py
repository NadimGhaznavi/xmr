"""LAN-only account administration ASGI server."""

from __future__ import annotations

import asyncio
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

    async def site_data_is_available(self, scope: dict[str, Any]) -> bool:
        if scope.get("path") == "/health":
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


app = AdminServer()
