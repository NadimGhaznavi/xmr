"""Account application workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from db.AcctDb import (
    AccountRole,
    AcctDb,
    CreatedAccount,
    CreatedMinerAccount,
    DuplicateAccountError,
)


USERNAME_PATTERN = re.compile(
    r"(?:[A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9_-]{0,30}[A-Za-z0-9])\Z"
)
MONERO_ADDRESS_PATTERN = re.compile(
    r"[48][123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{94}"
    r"(?:[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{11})?\Z"
)


class AccountStore(Protocol):
    def create_account(
        self, username: str, password_hash: str, *, role: AccountRole = "user"
    ) -> CreatedAccount: ...

    def create_miner_account(
        self, username: str, password_hash: str, wallet_address: str
    ) -> CreatedMinerAccount: ...


class Hasher(Protocol):
    def hash(self, password: str | bytes) -> str: ...


@dataclass(frozen=True, slots=True)
class AccountValidationError(ValueError):
    errors: dict[str, str]

    def __str__(self) -> str:
        return "invalid account details"


class AccountAlreadyExistsError(RuntimeError):
    """Raised when the username or wallet is already registered."""


class AcctMgr:
    """Validate, secure, and persist account requests."""

    def __init__(
        self,
        database: AcctDb | AccountStore | None = None,
        *,
        password_hasher: Hasher | None = None,
    ) -> None:
        self._database = database or AcctDb()
        self._password_hasher = password_hasher or _default_password_hasher()

    def create_account(
        self, username: str, password_hash: str, *, role: AccountRole = "user"
    ) -> CreatedAccount:
        self._validate_account(username, password_hash, role)
        return self._database.create_account(username, password_hash, role=role)

    def create_miner_account(
        self, username: str, password: str, wallet_address: str
    ) -> CreatedMinerAccount:
        username = username.strip()
        wallet_address = wallet_address.strip()
        errors = self._validate_signup(username, password, wallet_address)
        if errors:
            raise AccountValidationError(errors)

        password_hash = self._password_hasher.hash(password)
        try:
            return self._database.create_miner_account(
                username, password_hash, wallet_address
            )
        except DuplicateAccountError as error:
            raise AccountAlreadyExistsError(
                "the username or wallet is already registered"
            ) from error

    @staticmethod
    def _validate_account(username: str, password_hash: str, role: AccountRole) -> None:
        if not username or len(username) > 64:
            raise ValueError("username must contain 1 to 64 characters")
        if not password_hash or len(password_hash) > 255:
            raise ValueError("password hash must contain 1 to 255 characters")
        if role not in {"user", "admin"}:
            raise ValueError("role must be 'user' or 'admin'")

    @staticmethod
    def _validate_signup(
        username: str, password: str, wallet_address: str
    ) -> dict[str, str]:
        errors: dict[str, str] = {}
        if not USERNAME_PATTERN.fullmatch(username):
            errors["username"] = (
                "Use 1–32 letters, numbers, underscores, or hyphens; "
                "start and end with a letter or number."
            )
        if len(password) < 12:
            # This is a validation message, not a hard-coded credential.
            errors["password"] = "Use at least 12 characters."  # nosec B105
        elif len(password) > 1024:
            # This is a validation message, not a hard-coded credential.
            errors["password"] = "Password is too long."  # nosec B105
        if not MONERO_ADDRESS_PATTERN.fullmatch(wallet_address):
            errors["wallet"] = "Enter a valid mainnet Monero wallet address."
        return errors


def _default_password_hasher() -> Hasher:
    from argon2 import PasswordHasher  # type: ignore[import-not-found]

    return PasswordHasher()
