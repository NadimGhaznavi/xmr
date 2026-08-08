"""Mining application workflows."""

from db.MiningDb import MiningDb


class MiningMgr:
    def __init__(self, database: MiningDb | None = None) -> None:
        self._database = database or MiningDb()
