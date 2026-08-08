"""SQL persistence for accounts and miner account profiles."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from .DbMgr import DbMgr, DbSession
from .XmrDb import XmrDb

AccountRole = Literal["user", "admin"]


class PortRangeExhaustedError(RuntimeError):
    pass


class DuplicateAccountError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CreatedAccount:
    account_id: int
    username: str
    role: AccountRole


@dataclass(frozen=True, slots=True)
class CreatedMinerAccount:
    account_id: int
    username: str
    wallet_address: str
    p2pool_port: int


@dataclass(frozen=True, slots=True)
class AcctDbConfig:
    p2pool_port_min: int = 20000
    p2pool_port_max: int = 29999

    @classmethod
    def from_env(cls, environment: Mapping[str, str] | None = None) -> "AcctDbConfig":
        env = os.environ if environment is None else environment
        try:
            port_min = int(env.get("XMR_P2POOL_PORT_MIN", "20000"))
            port_max = int(env.get("XMR_P2POOL_PORT_MAX", "29999"))
        except ValueError as error:
            raise ValueError("P2Pool ports must be integers") from error
        if port_min < 1024 or port_max > 65535 or port_min > port_max:
            raise ValueError("invalid P2Pool port range")
        return cls(port_min, port_max)


class AcctDb:
    """Translate account persistence requests into SQL for ``XmrDb``."""

    def __init__(
        self,
        database: DbMgr | None = None,
        *,
        config: AcctDbConfig | None = None,
    ) -> None:
        self._database = database or XmrDb()
        self._config = config or AcctDbConfig.from_env()

    def initialize_schema(self) -> None:
        for statement in _SCHEMA:
            self._database.execute(statement)

    def reset_schema(self) -> None:
        for statement in (
            "DROP TABLE IF EXISTS miner_profiles",
            "DROP TABLE IF EXISTS p2pool_port_allocator",
            "DROP TABLE IF EXISTS accounts",
        ):
            self._database.execute(statement)

    def create_account(
        self, username: str, password_hash: str, *, role: AccountRole = "user"
    ) -> CreatedAccount:
        try:
            result = self._database.execute(
                "INSERT INTO accounts (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role),
            )
        except Exception as error:
            self._translate_duplicate(error)
            raise
        if result.last_insert_id is None:
            raise RuntimeError("MariaDB did not return an account ID")
        return CreatedAccount(result.last_insert_id, username, role)

    def create_miner_account(
        self, username: str, password_hash: str, wallet_address: str
    ) -> CreatedMinerAccount:
        try:
            with self._database.transaction() as session:
                result = session.execute(
                    """
                    INSERT INTO accounts (username, password_hash, role)
                    VALUES (?, ?, 'user')
                    """,
                    (username, password_hash),
                )
                if result.last_insert_id is None:
                    raise RuntimeError("MariaDB did not return an account ID")
                port = self._allocate_p2pool_port(session)
                session.execute(
                    """
                    INSERT INTO miner_profiles
                        (account_id, wallet_address, p2pool_port)
                    VALUES (?, ?, ?)
                    """,
                    (result.last_insert_id, wallet_address, port),
                )
        except Exception as error:
            self._translate_duplicate(error)
            raise
        return CreatedMinerAccount(result.last_insert_id, username, wallet_address, port)

    def _allocate_p2pool_port(self, session: DbSession) -> int:
        allocator = session.fetch_one(
            """
            SELECT next_port FROM p2pool_port_allocator
            WHERE singleton_id = 1 FOR UPDATE
            """
        )
        if allocator is None:
            raise RuntimeError("P2Pool port allocator is not initialized")

        candidate = max(int(allocator["next_port"]), self._config.p2pool_port_min)
        while candidate <= self._config.p2pool_port_max:
            if session.fetch_one(
                "SELECT account_id FROM miner_profiles WHERE p2pool_port = ?",
                (candidate,),
            ) is None:
                break
            candidate += 1
        if candidate > self._config.p2pool_port_max:
            raise PortRangeExhaustedError("no P2Pool ports are available")
        session.execute(
            "UPDATE p2pool_port_allocator SET next_port = ? WHERE singleton_id = 1",
            (candidate + 1,),
        )
        return candidate

    @staticmethod
    def _translate_duplicate(error: Exception) -> None:
        if getattr(error, "errno", None) == 1062:
            raise DuplicateAccountError(
                "username or wallet already exists"
            ) from error


_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS accounts (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        username VARCHAR(64) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
        created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        PRIMARY KEY (id), UNIQUE KEY uq_accounts_username (username)
    ) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS miner_profiles (
        account_id BIGINT UNSIGNED NOT NULL,
        wallet_address VARCHAR(106) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
        p2pool_port SMALLINT UNSIGNED NOT NULL,
        PRIMARY KEY (account_id),
        UNIQUE KEY uq_miner_profiles_wallet (wallet_address),
        UNIQUE KEY uq_miner_profiles_port (p2pool_port),
        CONSTRAINT chk_miner_profiles_port CHECK (p2pool_port BETWEEN 1024 AND 65535),
        CONSTRAINT fk_miner_profiles_account FOREIGN KEY (account_id)
            REFERENCES accounts (id) ON DELETE CASCADE
    ) ENGINE=InnoDB
    """,
    """
    CREATE TABLE IF NOT EXISTS p2pool_port_allocator (
        singleton_id TINYINT UNSIGNED NOT NULL,
        next_port INT UNSIGNED NOT NULL,
        PRIMARY KEY (singleton_id),
        CONSTRAINT chk_p2pool_port_allocator_singleton CHECK (singleton_id = 1)
    ) ENGINE=InnoDB
    """,
    "INSERT IGNORE INTO p2pool_port_allocator (singleton_id, next_port) VALUES (1, 1024)",
)
