"""Mining-pool application workflows."""

from db.PoolDb import PoolDb


class PoolMgr:
    def __init__(self, database: PoolDb | None = None) -> None:
        self._database = database or PoolDb()
