"""Presentation workflows and template context assembly."""

from __future__ import annotations

from collections.abc import Mapping

from mgr.AcctMgr import AccountAlreadyExistsError, AccountValidationError, AcctMgr
from web.Interface import JsonResult, Result, ViewResult


def health(arguments: Mapping[str, str]) -> Result:
    del arguments
    return JsonResult({"status": "ok"})


def index(arguments: Mapping[str, str]) -> Result:
    del arguments
    return JsonResult({"name": "Bear and Moose XMR API", "status": "ok"})


def login(arguments: Mapping[str, str]) -> Result:
    del arguments
    return ViewResult()


def signup(arguments: Mapping[str, str]) -> Result:
    del arguments
    return ViewResult(_signup_context())


def new_account(arguments: Mapping[str, str]) -> Result:
    username = arguments.get("username", "")
    password = arguments.get("password", "")
    wallet = arguments.get("wallet", "")
    try:
        user = AcctMgr().create_user(username, password, wallet)
    except AccountValidationError as error:
        return ViewResult(
            _signup_context(errors=error.errors, username=username, wallet=wallet),
            422,
        )
    except AccountAlreadyExistsError:
        return ViewResult(
            _signup_context(
                form_error="That username or wallet is already registered.",
                username=username,
                wallet=wallet,
            ),
            409,
        )
    return ViewResult(
        {
            "username": user.username,
            "wallet": user.wallet_address,
            "pools": [],
            "total_hashrate": 0,
            "total_payout_atomic": 0,
        }
    )


def not_found(arguments: Mapping[str, str]) -> Result:
    del arguments
    return JsonResult({"error": "not_found"}, 404)


def method_not_allowed(arguments: Mapping[str, str]) -> Result:
    del arguments
    return JsonResult({"error": "method_not_allowed"}, 405)


def _signup_context(**values: object) -> dict[str, object]:
    context: dict[str, object] = {
        "errors": {},
        "form_error": "",
        "username": "",
        "wallet": "",
    }
    context.update(values)
    return context
