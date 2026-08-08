"""Server-side session persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .DbMgr import DbMgr
from .XmrDb import XmrDb


class SessDb:
    """Translate session operations into parameterized SQL."""

    def __init__(self, database: DbMgr | None = None) -> None:
        self._database = database or XmrDb()

    def initialize_schema(self) -> None:
        self._database.execute(_SESSION_SCHEMA)

    def reset_schema(self) -> None:
        self._database.execute("DROP TABLE IF EXISTS sessions")

    def find_active(self, token_digest: bytes, now: datetime) -> dict[str, Any] | None:
        return self._database.fetch_one(
            """
            SELECT id, account_id, authenticated, created_at, last_activity_at,
                   expires_at, absolute_expires_at
            FROM sessions
            WHERE token_digest = ? AND revoked_at IS NULL
              AND expires_at > ? AND absolute_expires_at > ?
            """,
            (token_digest, now, now),
        )

    def create(
        self,
        token_digest: bytes,
        created_at: datetime,
        expires_at: datetime,
        absolute_expires_at: datetime,
    ) -> int:
        result = self._database.execute(
            """
            INSERT INTO sessions
                (token_digest, authenticated, created_at, last_activity_at,
                 expires_at, absolute_expires_at)
            VALUES (?, FALSE, ?, ?, ?, ?)
            """,
            (token_digest, created_at, created_at, expires_at, absolute_expires_at),
        )
        if result.last_insert_id is None:
            raise RuntimeError("MariaDB did not return a session ID")
        return result.last_insert_id

    def touch(self, session_id: int, now: datetime, expires_at: datetime) -> bool:
        result = self._database.execute(
            """
            UPDATE sessions SET last_activity_at = ?, expires_at = ?
            WHERE id = ? AND revoked_at IS NULL
              AND expires_at > ? AND absolute_expires_at > ?
            """,
            (now, expires_at, session_id, now, now),
        )
        return result.affected_rows == 1

    def authenticate_and_rotate(
        self,
        session_id: int,
        account_id: int,
        old_digest: bytes,
        new_digest: bytes,
        now: datetime,
        expires_at: datetime,
    ) -> bool:
        result = self._database.execute(
            """
            UPDATE sessions
            SET token_digest = ?, account_id = ?, authenticated = TRUE,
                last_activity_at = ?, expires_at = ?
            WHERE id = ? AND token_digest = ? AND revoked_at IS NULL
              AND expires_at > ? AND absolute_expires_at > ?
            """,
            (
                new_digest,
                account_id,
                now,
                expires_at,
                session_id,
                old_digest,
                now,
                now,
            ),
        )
        return result.affected_rows == 1

    def revoke(self, token_digest: bytes, now: datetime) -> None:
        self._database.execute(
            """
            UPDATE sessions SET revoked_at = ?
            WHERE token_digest = ? AND revoked_at IS NULL
            """,
            (now, token_digest),
        )


_SESSION_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    token_digest BINARY(32) NOT NULL,
    account_id BIGINT UNSIGNED NULL,
    authenticated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME(6) NOT NULL,
    last_activity_at DATETIME(6) NOT NULL,
    expires_at DATETIME(6) NOT NULL,
    absolute_expires_at DATETIME(6) NOT NULL,
    revoked_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_sessions_token_digest (token_digest),
    KEY ix_sessions_expiry (expires_at),
    KEY ix_sessions_account (account_id),
    CONSTRAINT fk_sessions_account FOREIGN KEY (account_id)
        REFERENCES accounts (id) ON DELETE CASCADE
) ENGINE=InnoDB
"""
