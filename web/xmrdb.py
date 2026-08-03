"""Database access layer for the XMR application."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Protocol


class DatabaseConfigurationError(ValueError):
    """Raised when database configuration is missing or invalid."""


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

        return cls(
            host=env.get("XMR_DB_HOST", "localhost"),
            port=port,
            database=env.get("XMR_DB_NAME", "xmr"),
            user=env.get("XMR_DB_USER", "xmr"),
            password=password,
            connect_timeout=timeout,
        )

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
