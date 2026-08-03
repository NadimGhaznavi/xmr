import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "web" / "xmrdb.py"
SPEC = importlib.util.spec_from_file_location("xmrdb", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
xmrdb = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = xmrdb
SPEC.loader.exec_module(xmrdb)


class FakeCursor:
    description = (("id",), ("name",))
    lastrowid = 7
    rowcount = 1

    def __init__(self) -> None:
        self.statement = None
        self.parameters = None
        self.closed = False

    def execute(self, statement, parameters=()):
        self.statement = statement
        self.parameters = parameters

    def fetchone(self):
        return (1, "miner")

    def fetchall(self):
        return [(1, "miner"), (2, "worker")]

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self) -> None:
        self.cursors = []
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        cursor = FakeCursor()
        self.cursors.append(cursor)
        return cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class XMRDBTest(unittest.TestCase):
    def setUp(self):
        self.config = xmrdb.DatabaseConfig.from_env({"XMR_DB_PASSWORD": "secret"})
        self.connection = FakeConnection()
        self.database = xmrdb.XMRDB(
            self.config, connector=lambda **options: self.connection
        )

    def test_requires_password(self):
        with self.assertRaises(xmrdb.DatabaseConfigurationError):
            xmrdb.DatabaseConfig.from_env({})

    def test_fetch_all_returns_named_columns(self):
        rows = self.database.fetch_all("SELECT id, name FROM miners WHERE id > ?", (0,))

        self.assertEqual(rows, [{"id": 1, "name": "miner"}, {"id": 2, "name": "worker"}])
        self.assertEqual(self.connection.cursors[0].parameters, (0,))
        self.assertTrue(self.connection.committed)
        self.assertTrue(self.connection.closed)

    def test_execute_returns_metadata(self):
        result = self.database.execute("INSERT INTO miners (name) VALUES (?)", ("miner",))

        self.assertEqual(result.affected_rows, 1)
        self.assertEqual(result.last_insert_id, 7)

    def test_transaction_rolls_back_on_error(self):
        with self.assertRaises(RuntimeError):
            with self.database.transaction():
                raise RuntimeError("failed")

        self.assertTrue(self.connection.rolled_back)
        self.assertFalse(self.connection.committed)
        self.assertTrue(self.connection.closed)


if __name__ == "__main__":
    unittest.main()
