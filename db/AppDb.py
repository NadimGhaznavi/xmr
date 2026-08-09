"""Application persistence backed by MariaDB."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .DbMgr import DbMgr
from .XmrDb import XmrDb

UserRole = Literal["user", "admin"]


class DuplicateUserError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class User:
    user_id: int
    username: str
    wallet_address: str
    role: UserRole


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


_USERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    wallet_address VARCHAR(106) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_wallet (wallet_address)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
"""
