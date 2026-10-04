"""Persistence for user-owned P2Pool instances."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from constants.DDefault import DDefault

from .DbMgr import DbMgr
from .XmrDb import XmrDb

Chain = Literal["main", "mini", "nano"]


class DuplicatePoolError(RuntimeError):
    pass


class PoolNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class Pool:
    pool_id: int
    account_id: int
    chain: Chain
    port: int
    created_at: datetime
    updated_at: datetime


class PoolDb:
    def __init__(self, database: DbMgr | None = None) -> None:
        self._database = database or XmrDb()

    def create_pool(self, account_id: int, chain: Chain) -> Pool:
        try:
            with self._database.transaction() as session:
                sequence = session.fetch_one(
                    "SELECT next_port FROM pool_port_sequence WHERE id = 1 FOR UPDATE"
                )
                if sequence is None:
                    raise RuntimeError("pool port sequence is not initialized")
                port = int(sequence["next_port"])
                if port > 65535:
                    raise RuntimeError("no P2Pool ports remain")
                result = session.execute(
                    "INSERT INTO pools (account_id, chain, port) VALUES (?, ?, ?)",
                    (account_id, chain, port),
                )
                session.execute(
                    "UPDATE pool_port_sequence SET next_port = ? WHERE id = 1",
                    (port + 1,),
                )
        except Exception as error:
            if getattr(error, "errno", None) == 1062:
                raise DuplicatePoolError("account already has that chain") from error
            raise
        if result.last_insert_id is None:
            raise RuntimeError("MariaDB did not return a pool ID")
        return self.get_pool(account_id, result.last_insert_id)

    def list_pools(self, account_id: int) -> list[Pool]:
        rows = self._database.fetch_all(
            """
            SELECT id, account_id, chain, port, created_at, updated_at
            FROM pools WHERE account_id = ? ORDER BY id
            """,
            (account_id,),
        )
        return [_pool_from_row(row) for row in rows]

    def get_pool(self, account_id: int, pool_id: int) -> Pool:
        row = self._database.fetch_one(
            """
            SELECT id, account_id, chain, port, created_at, updated_at
            FROM pools WHERE id = ? AND account_id = ?
            """,
            (pool_id, account_id),
        )
        if row is None:
            raise PoolNotFoundError("pool does not exist")
        return _pool_from_row(row)

    def update_chain(self, account_id: int, pool_id: int, chain: Chain) -> Pool:
        try:
            result = self._database.execute(
                "UPDATE pools SET chain = ? WHERE id = ? AND account_id = ?",
                (chain, pool_id, account_id),
            )
        except Exception as error:
            if getattr(error, "errno", None) == 1062:
                raise DuplicatePoolError("account already has that chain") from error
            raise
        if result.affected_rows == 0:
            self.get_pool(account_id, pool_id)
        return self.get_pool(account_id, pool_id)


def _pool_from_row(row: dict[str, Any]) -> Pool:
    chain = str(row["chain"])
    if chain not in {"main", "mini", "nano"}:
        raise ValueError("database returned an invalid chain")
    return Pool(
        int(row["id"]),
        int(row["account_id"]),
        chain,  # type: ignore[arg-type]
        int(row["port"]),
        row["created_at"],
        row["updated_at"],
    )


if not 1 <= DDefault.STARTING_P2POOL_PORT <= 65535:
    raise ValueError("STARTING_P2POOL_PORT is outside the valid port range")


_POOL_SCHEMA_TEMPLATE = """
CREATE TABLE IF NOT EXISTS pool_port_sequence (
    id TINYINT UNSIGNED NOT NULL,
    next_port INT UNSIGNED NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT chk_pool_port_sequence_id CHECK (id = 1)
) ENGINE=InnoDB;

INSERT IGNORE INTO pool_port_sequence (id, next_port)
VALUES (1, __STARTING_PORT__);

CREATE TABLE IF NOT EXISTS pools (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    account_id BIGINT UNSIGNED NOT NULL,
    chain ENUM('main', 'mini', 'nano') NOT NULL,
    port INT UNSIGNED NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_pools_account_chain (account_id, chain),
    UNIQUE KEY uq_pools_port (port),
    CONSTRAINT fk_pools_account FOREIGN KEY (account_id)
        REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
"""

# STARTING_P2POOL_PORT is a validated integer constant, not request data.
_POOL_SCHEMA = _POOL_SCHEMA_TEMPLATE.replace(
    "__STARTING_PORT__", str(DDefault.STARTING_P2POOL_PORT)
)
