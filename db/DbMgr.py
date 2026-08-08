"""Interface shared by database backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class QueryResult:
    affected_rows: int
    last_insert_id: int | None


class DbSession(Protocol):
    def execute(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> QueryResult: ...

    def fetch_one(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> dict[str, Any] | None: ...

    def fetch_all(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]: ...


class DbMgr(ABC):
    """Contract for executing SQL and managing transactions."""

    @abstractmethod
    def transaction(self) -> AbstractContextManager[DbSession]:
        raise NotImplementedError

    @abstractmethod
    def execute(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> QueryResult:
        raise NotImplementedError

    @abstractmethod
    def fetch_one(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def fetch_all(
        self, statement: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        raise NotImplementedError
