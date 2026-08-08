"""Mining persistence boundary."""

from .DbMgr import DbMgr
from .XmrDb import XmrDb


class MiningDb:
    def __init__(self, database: DbMgr | None = None) -> None:
        self._database = database or XmrDb()
