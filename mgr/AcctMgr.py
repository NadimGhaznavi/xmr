"""Account application workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from db.AppDb import (
    AppDb,
    DuplicateUserError,
    User,
    UserRole,
)

USERNAME_PATTERN = re.compile(
    r"(?:[A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9_-]{0,30}[A-Za-z0-9])\Z"
)
MONERO_ADDRESS_PATTERN = re.compile(
    r"[48][123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{94}"
    r"(?:[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{11})?\Z"
)


class AccountStore(Protocol):
    def create_user(
        self,
        username: str,
        password_hash: str,
        wallet_address: str,
        *,
        role: UserRole = "user",
    ) -> User: ...


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
        database: AppDb | AccountStore | None = None,
        *,
        password_hasher: Hasher | None = None,
    ) -> None:
        self._database = database or AppDb()
        self._password_hasher = password_hasher or _default_password_hasher()

    def create_user(self, username: str, password: str, wallet_address: str) -> User:
        username = username.strip()
        wallet_address = wallet_address.strip()
        errors = self._validate_signup(username, password, wallet_address)
        if errors:
            raise AccountValidationError(errors)

        password_hash = self._password_hasher.hash(password)
        try:
            return self._database.create_user(username, password_hash, wallet_address)
        except DuplicateUserError as error:
            raise AccountAlreadyExistsError(
                "the username or wallet is already registered"
            ) from error

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
