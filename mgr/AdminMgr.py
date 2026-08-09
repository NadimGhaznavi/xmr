"""Presentation workflows for account administration."""

from __future__ import annotations

from collections.abc import Mapping

from db.AdminDb import AccountNotFoundError, AdminDb
from db.AppDb import DuplicateUserError, User, UserStatus
from mgr.AcctMgr import AcctMgr
from web.Interface import JsonResult, RedirectResult, Result, ViewResult


def health(arguments: Mapping[str, str]) -> Result:
    del arguments
    return JsonResult({"status": "ok"})


def not_found(arguments: Mapping[str, str]) -> Result:
    del arguments
    return JsonResult({"error": "not_found"}, 404)


def method_not_allowed(arguments: Mapping[str, str]) -> Result:
    del arguments
    return JsonResult({"error": "method_not_allowed"}, 405)


def list_accounts(arguments: Mapping[str, str]) -> Result:
    del arguments
    return ViewResult({"accounts": AdminDb().list_accounts()})


def edit_account(arguments: Mapping[str, str]) -> Result:
    try:
        account = AdminDb().get_account(_account_id(arguments))
    except (AccountNotFoundError, ValueError):
        return ViewResult({"message": "Account not found."}, 404)
    return ViewResult(_edit_context(account))


def update_account(arguments: Mapping[str, str]) -> Result:
    database = AdminDb()
    try:
        account_id = _account_id(arguments)
        account = database.get_account(account_id)
    except (AccountNotFoundError, ValueError):
        return ViewResult({"message": "Account not found."}, 404)

    username = arguments.get("username", "").strip()
    wallet = arguments.get("wallet", "").strip()
    errors = AcctMgr.validate_profile(username, wallet)
    if errors:
        return ViewResult(
            _edit_context(account, username=username, wallet=wallet, errors=errors),
            422,
        )
    try:
        database.update_account(account_id, username, wallet)
    except DuplicateUserError:
        return ViewResult(
            _edit_context(
                account,
                username=username,
                wallet=wallet,
                form_error="That username or wallet is already registered.",
            ),
            409,
        )
    return RedirectResult("/")


def disable_account(arguments: Mapping[str, str]) -> Result:
    return _set_status(arguments, "disabled")


def enable_account(arguments: Mapping[str, str]) -> Result:
    return _set_status(arguments, "active")


def _set_status(arguments: Mapping[str, str], status: UserStatus) -> Result:
    database = AdminDb()
    try:
        account_id = _account_id(arguments)
        account = database.get_account(account_id)
    except (AccountNotFoundError, ValueError):
        return ViewResult({"message": "Account not found."}, 404)
    if arguments.get("confirm_username", "") != account.username:
        return ViewResult(
            _edit_context(
                account,
                form_error="Enter the account username to confirm this action.",
            ),
            422,
        )
    database.set_account_status(account_id, status)
    return RedirectResult("/")


def _account_id(arguments: Mapping[str, str]) -> int:
    account_id = int(arguments.get("account_id", ""))
    if account_id <= 0:
        raise ValueError("invalid account ID")
    return account_id


def _edit_context(account: User, **values: object) -> dict[str, object]:
    context: dict[str, object] = {
        "account": account,
        "username": account.username,
        "wallet": account.wallet_address,
        "errors": {},
        "form_error": "",
    }
    context.update(values)
    return context
