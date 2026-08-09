"""Tests for pool business rules."""

import unittest
from datetime import datetime

from db.PoolDb import DuplicatePoolError, Pool
from mgr.PoolMgr import PoolAlreadyExistsError, PoolMgr, PoolValidationError

NOW = datetime(2026, 8, 9, 12, 0, 0)


class Pools:
    def __init__(self, duplicate=False):
        self.duplicate = duplicate
        self.created = []
        self.updated = []
        self.pool = Pool(3, 7, "mini", 33333, NOW, NOW)

    def create_pool(self, account_id, chain):
        self.created.append((account_id, chain))
        if self.duplicate:
            raise DuplicatePoolError("duplicate")
        return self.pool

    def list_pools(self, account_id):
        return [self.pool] if account_id == 7 else []

    def get_pool(self, account_id, pool_id):
        if (account_id, pool_id) != (7, 3):
            raise AssertionError("ownership arguments changed")
        return self.pool

    def update_chain(self, account_id, pool_id, chain):
        self.updated.append((account_id, pool_id, chain))
        if self.duplicate:
            raise DuplicatePoolError("duplicate")
        return self.pool


class PoolMgrTest(unittest.TestCase):
    def test_normalizes_valid_chain(self):
        database = Pools()
        self.assertEqual(PoolMgr(database).create_pool(7, " MINI "), database.pool)
        self.assertEqual(database.created, [(7, "mini")])

    def test_rejects_invalid_chain_before_database_call(self):
        database = Pools()
        with self.assertRaisesRegex(PoolValidationError, "main, mini, or nano"):
            PoolMgr(database).create_pool(7, "sidechain")
        self.assertEqual(database.created, [])

    def test_translates_duplicate_create(self):
        with self.assertRaisesRegex(PoolAlreadyExistsError, "mini pool"):
            PoolMgr(Pools(duplicate=True)).create_pool(7, "mini")

    def test_preserves_account_ownership_for_get(self):
        pool = PoolMgr(Pools()).get_pool(7, 3)
        self.assertEqual((pool.account_id, pool.pool_id), (7, 3))

    def test_normalizes_update_and_translates_duplicates(self):
        database = Pools()
        PoolMgr(database).update_pool(7, 3, " NANO ")
        self.assertEqual(database.updated, [(7, 3, "nano")])
        with self.assertRaisesRegex(PoolAlreadyExistsError, "main pool"):
            PoolMgr(Pools(duplicate=True)).update_pool(7, 3, "main")


if __name__ == "__main__":
    unittest.main()
