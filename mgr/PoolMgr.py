"""Business rules for user-owned pools."""

from __future__ import annotations

from db.PoolDb import Chain, DuplicatePoolError, Pool, PoolDb


class PoolValidationError(ValueError):
    pass


class PoolAlreadyExistsError(RuntimeError):
    pass


class PoolMgr:
    def __init__(self, database: PoolDb | None = None) -> None:
        self._database = database or PoolDb()

    def create_pool(self, account_id: int, chain_value: str) -> Pool:
        chain = _chain(chain_value)
        try:
            return self._database.create_pool(account_id, chain)
        except DuplicatePoolError as error:
            raise PoolAlreadyExistsError(f"You already have a {chain} pool.") from error

    def list_pools(self, account_id: int) -> list[Pool]:
        return self._database.list_pools(account_id)

    def get_pool(self, account_id: int, pool_id: int) -> Pool:
        return self._database.get_pool(account_id, pool_id)

    def update_pool(self, account_id: int, pool_id: int, chain_value: str) -> Pool:
        chain = _chain(chain_value)
        try:
            return self._database.update_chain(account_id, pool_id, chain)
        except DuplicatePoolError as error:
            raise PoolAlreadyExistsError(f"You already have a {chain} pool.") from error


def _chain(value: str) -> Chain:
    normalized = value.strip().lower()
    if normalized not in {"main", "mini", "nano"}:
        raise PoolValidationError("Choose main, mini, or nano.")
    return normalized  # type: ignore[return-value]
