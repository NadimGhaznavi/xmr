"""Application persistence backed by MariaDB."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from .DbMgr import DbMgr
from .XmrDb import XmrDb

UserRole = Literal["user", "admin"]
UserStatus = Literal["active", "disabled"]


class DuplicateUserError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class User:
    user_id: int
    username: str
    wallet_address: str
    role: UserRole
    status: UserStatus = "active"
    created_at: datetime | None = None
    disabled_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class LoginAccount:
    user: User
    password_hash: str


class AppDb:
    """Read and write application data through ``XmrDb``."""

    def __init__(self, database: DbMgr | None = None) -> None:
        self._database = database or XmrDb()

    def initialize_schema(self) -> None:
        self._database.execute(_USERS_SCHEMA)

    def reset_schema(self) -> None:
        self._database.execute("DROP TABLE IF EXISTS users")

    def create_user(
        self,
        username: str,
        password_hash: str,
        wallet_address: str,
        *,
        role: UserRole = "user",
    ) -> User:
        try:
            result = self._database.execute(
                """
                INSERT INTO users (username, password_hash, wallet_address, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, password_hash, wallet_address, role),
            )
        except Exception as error:
            if getattr(error, "errno", None) == 1062:
                raise DuplicateUserError("username or wallet already exists") from error
            raise

        if result.last_insert_id is None:
            raise RuntimeError("MariaDB did not return a user ID")
        return User(result.last_insert_id, username, wallet_address, role)

    def get_user(self, account_id: int) -> User | None:
        row = self._database.fetch_one(
            """
            SELECT id, username, wallet_address, role, status, created_at,
                   disabled_at
            FROM users
            WHERE id = ? AND status = 'active'
            """,
            (account_id,),
        )
        return None if row is None else _user_from_row(row)

    def find_login_account(self, username: str) -> LoginAccount | None:
        row = self._database.fetch_one(
            """
            SELECT id, username, password_hash, wallet_address, role, status,
                   created_at, disabled_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        if row is None:
            return None
        return LoginAccount(_user_from_row(row), str(row["password_hash"]))


def _user_from_row(row: dict[str, Any]) -> User:
    role = str(row["role"])
    status = str(row["status"])
    if role not in {"user", "admin"} or status not in {"active", "disabled"}:
        raise ValueError("database returned an invalid account")
    return User(
        int(row["id"]),
        str(row["username"]),
        str(row["wallet_address"]),
        role,  # type: ignore[arg-type]
        status,  # type: ignore[arg-type]
        row["created_at"],
        row["disabled_at"],
    )


_USERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    wallet_address VARCHAR(106) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    status ENUM('active', 'disabled') NOT NULL DEFAULT 'active',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    disabled_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_wallet (wallet_address)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
"""
