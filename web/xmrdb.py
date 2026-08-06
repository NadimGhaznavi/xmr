"""Database access layer for the XMR application."""

from __future__ import annotations

import os
import shlex
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol


SCHEMA_MIGRATIONS: tuple[tuple[int, tuple[str, ...]], ...] = (
    (
        1,
        (
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                username VARCHAR(64) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
                created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                PRIMARY KEY (id),
                UNIQUE KEY uq_accounts_username (username)
            ) ENGINE=InnoDB
              DEFAULT CHARACTER SET utf8mb4
              COLLATE utf8mb4_unicode_ci
            """,
            """
            CREATE TABLE IF NOT EXISTS miner_profiles (
                account_id BIGINT UNSIGNED NOT NULL,
                wallet_address VARCHAR(106)
                    CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
                p2pool_port SMALLINT UNSIGNED NOT NULL,
                PRIMARY KEY (account_id),
                UNIQUE KEY uq_miner_profiles_wallet (wallet_address),
                UNIQUE KEY uq_miner_profiles_port (p2pool_port),
                CONSTRAINT chk_miner_profiles_port
                    CHECK (p2pool_port BETWEEN 1024 AND 65535),
                CONSTRAINT fk_miner_profiles_account
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS p2pool_port_allocator (
                singleton_id TINYINT UNSIGNED NOT NULL,
                next_port INT UNSIGNED NOT NULL,
                PRIMARY KEY (singleton_id),
                CONSTRAINT chk_p2pool_port_allocator_singleton
                    CHECK (singleton_id = 1)
            ) ENGINE=InnoDB
            """,
            """
            INSERT IGNORE INTO p2pool_port_allocator (singleton_id, next_port)
            VALUES (1, 1024)
            """,
        ),
    ),
)

AccountRole = Literal["user", "admin"]


class DatabaseConfigurationError(ValueError):
    """Raised when database configuration is missing or invalid."""


class PortRangeExhaustedError(RuntimeError):
    """Raised when no unassigned P2Pool port remains in the configured range."""


class DuplicateAccountError(RuntimeError):
    """Raised when an account conflicts with an existing unique value."""


class Cursor(Protocol):
    description: Sequence[Sequence[Any]] | None
    lastrowid: int | None
    rowcount: int

    def execute(self, statement: str, parameters: Sequence[Any] = ()) -> Any: ...
    def fetchone(self) -> Sequence[Any] | None: ...
    def fetchall(self) -> Sequence[Sequence[Any]]: ...
    def close(self) -> None: ...


class Connection(Protocol):
    def cursor(self) -> Cursor: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...


Connector = Callable[..., Connection]


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    connect_timeout: int = 10
    p2pool_port_min: int = 20000
    p2pool_port_max: int = 29999

    @classmethod
    def from_env(
        cls, environment: Mapping[str, str] | None = None
    ) -> "DatabaseConfig":
        env = os.environ if environment is None else environment

        password = env.get("XMR_DB_PASSWORD", "")
        if not password:
            raise DatabaseConfigurationError("XMR_DB_PASSWORD is required")

        port = _read_positive_int(env, "XMR_DB_PORT", 3306, maximum=65535)
        timeout = _read_positive_int(env, "XMR_DB_CONNECT_TIMEOUT", 10)
        port_min = _read_positive_int(
            env, "XMR_P2POOL_PORT_MIN", 20000, maximum=65535
        )
        port_max = _read_positive_int(
            env, "XMR_P2POOL_PORT_MAX", 29999, maximum=65535
        )
        if port_min < 1024 or port_min > port_max:
            raise DatabaseConfigurationError("invalid P2Pool port range")

        return cls(
            host=env.get("XMR_DB_HOST", "localhost"),
            port=port,
            database=env.get("XMR_DB_NAME", "xmr"),
            user=env.get("XMR_DB_USER", "xmr"),
            password=password,
            connect_timeout=timeout,
            p2pool_port_min=port_min,
            p2pool_port_max=port_max,
        )

    @classmethod
    def from_env_file(cls, path: str | Path) -> "DatabaseConfig":
        return cls.from_env(_read_environment_file(Path(path)))

    def connection_options(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "connect_timeout": self.connect_timeout,
        }


@dataclass(frozen=True, slots=True)
class QueryResult:
    affected_rows: int
    last_insert_id: int | None


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


class XMRDBSession:
    """A set of database operations sharing one connection."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def execute(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> QueryResult:
        with _cursor(self._connection) as cursor:
            cursor.execute(statement, parameters)
            return QueryResult(cursor.rowcount, cursor.lastrowid)

    def fetch_one(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> dict[str, Any] | None:
        with _cursor(self._connection) as cursor:
            cursor.execute(statement, parameters)
            row = cursor.fetchone()
            return None if row is None else _as_dict(cursor, row)

    def fetch_all(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        with _cursor(self._connection) as cursor:
            cursor.execute(statement, parameters)
            return [_as_dict(cursor, row) for row in cursor.fetchall()]


class XMRDB:
    """Create isolated MariaDB connections and manage their transactions."""

    def __init__(
        self,
        config: DatabaseConfig | None = None,
        *,
        connector: Connector | None = None,
    ) -> None:
        self._config = config or DatabaseConfig.from_env()
        self._connector = connector or _mariadb_connector

    @contextmanager
    def transaction(self) -> Iterator[XMRDBSession]:
        connection = self._connector(**self._config.connection_options())
        try:
            yield XMRDBSession(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def execute(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> QueryResult:
        with self.transaction() as session:
            return session.execute(statement, parameters)

    def fetch_one(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> dict[str, Any] | None:
        with self.transaction() as session:
            return session.fetch_one(statement, parameters)

    def fetch_all(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        with self.transaction() as session:
            return session.fetch_all(statement, parameters)

    def initialize_schema(self) -> None:
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INT UNSIGNED NOT NULL,
                applied_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                PRIMARY KEY (version)
            ) ENGINE=InnoDB
            """
        )
        applied = {
            int(row["version"])
            for row in self.fetch_all("SELECT version FROM schema_migrations")
        }

        for version, statements in SCHEMA_MIGRATIONS:
            if version in applied:
                continue
            for statement in statements:
                self.execute(statement)
            self.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
            )

    def reset_schema(self) -> None:
        """Permanently remove every table owned by this application."""

        for statement in (
            "DROP TABLE IF EXISTS miner_profiles",
            "DROP TABLE IF EXISTS p2pool_port_allocator",
            "DROP TABLE IF EXISTS accounts",
            "DROP TABLE IF EXISTS schema_migrations",
        ):
            self.execute(statement)

    def create_account(
        self,
        username: str,
        password_hash: str,
        *,
        role: AccountRole = "user",
    ) -> CreatedAccount:
        _validate_account_values(username, password_hash, role)
        result = self.execute(
            "INSERT INTO accounts (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role),
        )
        if result.last_insert_id is None:
            raise RuntimeError("MariaDB did not return an account ID")
        return CreatedAccount(result.last_insert_id, username, role)

    def create_miner_account(
        self, username: str, password_hash: str, wallet_address: str
    ) -> CreatedMinerAccount:
        _validate_account_values(username, password_hash, "user")
        if not wallet_address or len(wallet_address) > 106:
            raise ValueError("wallet address must contain 1 to 106 characters")

        try:
            with self.transaction() as session:
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
            if getattr(error, "errno", None) == 1062:
                raise DuplicateAccountError(
                    "username or wallet already exists"
                ) from error
            raise

        return CreatedMinerAccount(
            result.last_insert_id, username, wallet_address, port
        )

    def _allocate_p2pool_port(self, session: XMRDBSession) -> int:
        allocator = session.fetch_one(
            """
            SELECT next_port
            FROM p2pool_port_allocator
            WHERE singleton_id = 1
            FOR UPDATE
            """
        )
        if allocator is None:
            raise RuntimeError("P2Pool port allocator is not initialized")

        candidate = max(int(allocator["next_port"]), self._config.p2pool_port_min)
        while candidate <= self._config.p2pool_port_max:
            existing = session.fetch_one(
                "SELECT account_id FROM miner_profiles WHERE p2pool_port = ?",
                (candidate,),
            )
            if existing is None:
                break
            candidate += 1

        if candidate > self._config.p2pool_port_max:
            raise PortRangeExhaustedError("no P2Pool ports are available")

        session.execute(
            """
            UPDATE p2pool_port_allocator
            SET next_port = ?
            WHERE singleton_id = 1
            """,
            (candidate + 1,),
        )
        return candidate


def _read_positive_int(
    environment: Mapping[str, str],
    name: str,
    default: int,
    *,
    maximum: int | None = None,
) -> int:
    raw_value = environment.get(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as error:
        raise DatabaseConfigurationError(f"{name} must be an integer") from error

    if value <= 0 or (maximum is not None and value > maximum):
        raise DatabaseConfigurationError(f"{name} is outside the valid range")
    return value


def _read_environment_file(path: Path) -> dict[str, str]:
    environment: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        try:
            fields = shlex.split(stripped, comments=True, posix=True)
        except ValueError as error:
            raise DatabaseConfigurationError(
                f"invalid environment file syntax on line {line_number}"
            ) from error
        if len(fields) != 1 or "=" not in fields[0]:
            raise DatabaseConfigurationError(
                f"invalid environment assignment on line {line_number}"
            )

        name, value = fields[0].split("=", 1)
        if not name.startswith("XMR_"):
            raise DatabaseConfigurationError(
                f"unexpected environment key on line {line_number}"
            )
        environment[name] = value

    return environment


def _validate_account_values(
    username: str, password_hash: str, role: AccountRole
) -> None:
    if not username or len(username) > 64:
        raise ValueError("username must contain 1 to 64 characters")
    if not password_hash or len(password_hash) > 255:
        raise ValueError("password hash must contain 1 to 255 characters")
    if role not in {"user", "admin"}:
        raise ValueError("role must be 'user' or 'admin'")


@contextmanager
def _cursor(connection: Connection) -> Iterator[Cursor]:
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        cursor.close()


def _as_dict(cursor: Cursor, row: Sequence[Any]) -> dict[str, Any]:
    if cursor.description is None:
        return {}
    return {
        str(column[0]): value
        for column, value in zip(cursor.description, row, strict=True)
    }


def _mariadb_connector(**options: Any) -> Connection:
    import mariadb

    return mariadb.connect(**options)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage the XMR database schema")
    parser.add_argument("command", choices=("migrate", "reset"))
    parser.add_argument("--env-file", type=Path)
    arguments = parser.parse_args()

    config = (
        DatabaseConfig.from_env_file(arguments.env_file)
        if arguments.env_file
        else DatabaseConfig.from_env()
    )
    database = XMRDB(config)

    if arguments.command == "migrate":
        database.initialize_schema()
    elif arguments.command == "reset":
        database.reset_schema()
