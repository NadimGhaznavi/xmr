"""Presentation workflows and template context assembly."""

from __future__ import annotations

from collections.abc import Mapping

from db.AppDb import AppDb, User
from db.PoolDb import PoolNotFoundError
from mgr.AcctMgr import (
    AccountAlreadyExistsError,
    AccountValidationError,
    AcctMgr,
    InvalidCredentialsError,
)
from mgr.PoolMgr import PoolAlreadyExistsError, PoolMgr, PoolValidationError
from web.Interface import (
    AuthenticatedViewResult,
    JsonResult,
    RedirectResult,
    Result,
    ViewResult,
)


def health(arguments: Mapping[str, str]) -> Result:
    del arguments
    return JsonResult({"status": "ok"})


def index(arguments: Mapping[str, str]) -> Result:
    del arguments
    return JsonResult({"name": "Bear and Moose XMR API", "status": "ok"})


def login(arguments: Mapping[str, str]) -> Result:
    del arguments
    return ViewResult({"form_error": ""})


def authenticate(arguments: Mapping[str, str]) -> Result:
    try:
        user = AcctMgr().authenticate(
            arguments.get("username", ""), arguments.get("password", "")
        )
    except InvalidCredentialsError:
        return ViewResult(
            {"form_error": "Invalid username or password."},
            401,
        )
    return AuthenticatedViewResult(user.user_id, _dashboard_context(user))


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
    return AuthenticatedViewResult(user.user_id, _dashboard_context(user))


def dashboard(arguments: Mapping[str, str]) -> Result:
    user = AppDb().get_user(_account_id(arguments))
    if user is None:
        return RedirectResult("/login")
    return ViewResult(_dashboard_context(user))


def new_pool(arguments: Mapping[str, str]) -> Result:
    account_id = _account_id(arguments)
    return ViewResult(
        _pool_form_context(available_chains=_available_chains(account_id))
    )


def create_pool(arguments: Mapping[str, str]) -> Result:
    chain = arguments.get("chain", "")
    try:
        PoolMgr().create_pool(_account_id(arguments), chain)
    except (PoolValidationError, PoolAlreadyExistsError) as error:
        return ViewResult(
            _pool_form_context(
                chain=chain,
                form_error=str(error),
                available_chains=_available_chains(_account_id(arguments)),
            ),
            422,
        )
    return RedirectResult("/dashboard")


def edit_pool(arguments: Mapping[str, str]) -> Result:
    try:
        pool = PoolMgr().get_pool(_account_id(arguments), _pool_id(arguments))
    except (PoolNotFoundError, ValueError):
        return ViewResult({"message": "Pool not found."}, 404)
    return ViewResult(
        _pool_form_context(
            pool=pool,
            chain=pool.chain,
            available_chains=_available_chains(pool.account_id, pool.chain),
        )
    )


def update_pool(arguments: Mapping[str, str]) -> Result:
    account_id = _account_id(arguments)
    try:
        pool_id = _pool_id(arguments)
        pool = PoolMgr().get_pool(account_id, pool_id)
    except (PoolNotFoundError, ValueError):
        return ViewResult({"message": "Pool not found."}, 404)
    chain = arguments.get("chain", "")
    try:
        PoolMgr().update_pool(account_id, pool_id, chain)
    except (PoolValidationError, PoolAlreadyExistsError) as error:
        return ViewResult(
            _pool_form_context(
                pool=pool,
                chain=chain,
                form_error=str(error),
                available_chains=_available_chains(account_id, pool.chain),
            ),
            422,
        )
    return RedirectResult("/dashboard")


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


def _dashboard_context(user: User) -> dict[str, object]:
    return {
        "username": user.username,
        "wallet": user.wallet_address,
        "pools": PoolMgr().list_pools(user.user_id),
        "total_hashrate": 0,
        "total_payout_atomic": 0,
    }


def _pool_form_context(**values: object) -> dict[str, object]:
    context: dict[str, object] = {
        "chain": "",
        "form_error": "",
        "available_chains": (),
    }
    context.update(values)
    return context


def _available_chains(account_id: int, current: str | None = None) -> list[str]:
    used = {pool.chain for pool in PoolMgr().list_pools(account_id)}
    return [
        chain
        for chain in ("main", "mini", "nano")
        if chain == current or chain not in used
    ]


def _account_id(arguments: Mapping[str, str]) -> int:
    account_id = int(arguments.get("_account_id", ""))
    if account_id <= 0:
        raise ValueError("invalid account ID")
    return account_id


def _pool_id(arguments: Mapping[str, str]) -> int:
    pool_id = int(arguments.get("pool_id", ""))
    if pool_id <= 0:
        raise ValueError("invalid pool ID")
    return pool_id
