"""Secure server-side session lifecycle management."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from db.SessDb import SessDb


@dataclass(frozen=True, slots=True)
class Session:
    session_id: int
    token: str
    account_id: int | None
    authenticated: bool
    expires_at: datetime
    absolute_expires_at: datetime


class SessMgr:
    """Create and validate opaque sessions without exposing server state."""

    def __init__(
        self,
        database: SessDb,
        secret: bytes,
        *,
        idle_timeout: timedelta = timedelta(minutes=30),
        absolute_lifetime: timedelta = timedelta(hours=12),
    ) -> None:
        if len(secret) < 32:
            raise ValueError("session secret must contain at least 32 bytes")
        if idle_timeout <= timedelta(0) or absolute_lifetime < idle_timeout:
            raise ValueError("invalid session lifetime")
        self._database = database
        self._secret = secret
        self._idle_timeout = idle_timeout
        self._absolute_lifetime = absolute_lifetime

    def get_or_create(self, token: str | None) -> Session:
        now = datetime.now(UTC).replace(tzinfo=None)
        if token and self._valid_token_shape(token):
            row = self._database.find_active(self._digest(token), now)
            if row is not None:
                absolute_expiry = row["absolute_expires_at"]
                expires_at = min(now + self._idle_timeout, absolute_expiry)
                if self._database.touch(int(row["id"]), now, expires_at):
                    return Session(
                        int(row["id"]),
                        token,
                        row["account_id"],
                        bool(row["authenticated"]),
                        expires_at,
                        absolute_expiry,
                    )
        return self._create(now)

    def get_authenticated(self, token: str) -> Session | None:
        now = datetime.now(UTC).replace(tzinfo=None)
        if not self._valid_token_shape(token):
            return None
        row = self._database.find_active(self._digest(token), now)
        if row is None or not bool(row["authenticated"]):
            return None
        absolute_expiry = row["absolute_expires_at"]
        expires_at = min(now + self._idle_timeout, absolute_expiry)
        if not self._database.touch(int(row["id"]), now, expires_at):
            return None
        account_id = row["account_id"]
        if account_id is None:
            return None
        return Session(
            int(row["id"]),
            token,
            int(account_id),
            True,
            expires_at,
            absolute_expiry,
        )

    def authenticate(self, session: Session, account_id: int) -> Session:
        if account_id <= 0:
            raise ValueError("account ID must be positive")
        now = datetime.now(UTC).replace(tzinfo=None)
        new_token = self._new_token()
        expires_at = min(now + self._idle_timeout, session.absolute_expires_at)
        changed = self._database.authenticate_and_rotate(
            session.session_id,
            account_id,
            self._digest(session.token),
            self._digest(new_token),
            now,
            expires_at,
        )
        if not changed:
            raise RuntimeError("session expired or was revoked")
        return Session(
            session.session_id,
            new_token,
            account_id,
            True,
            expires_at,
            session.absolute_expires_at,
        )

    def revoke(self, token: str) -> None:
        if self._valid_token_shape(token):
            self._database.revoke(
                self._digest(token), datetime.now(UTC).replace(tzinfo=None)
            )

    def _create(self, now: datetime) -> Session:
        token = self._new_token()
        expires_at = now + self._idle_timeout
        absolute_expiry = now + self._absolute_lifetime
        session_id = self._database.create(
            self._digest(token), now, expires_at, absolute_expiry
        )
        return Session(session_id, token, None, False, expires_at, absolute_expiry)

    def _digest(self, token: str) -> bytes:
        return hmac.new(self._secret, token.encode("ascii"), hashlib.sha256).digest()

    @staticmethod
    def _new_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def _valid_token_shape(token: str) -> bool:
        return (
            40 <= len(token) <= 64
            and token.isascii()
            and token.replace("-", "").replace("_", "").isalnum()
        )
