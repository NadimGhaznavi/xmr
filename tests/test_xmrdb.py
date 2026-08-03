import importlib.util
import sys
import tempfile
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
        self._one = (1, "miner")
        self._all = [(1, "miner"), (2, "worker")]

    def execute(self, statement, parameters=()):
        self.statement = statement
        self.parameters = parameters
        normalized = " ".join(statement.split())
        if "SELECT next_port FROM p2pool_port_allocator" in normalized:
            self.description = (("next_port",),)
            self._one = (20000,)
        elif "SELECT account_id FROM miner_profiles" in normalized:
            self.description = (("account_id",),)
            self._one = None
        elif "SELECT version FROM schema_migrations" in normalized:
            self.description = (("version",),)
            self._all = []

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all

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

    def test_rejects_invalid_port_range(self):
        with self.assertRaises(xmrdb.DatabaseConfigurationError):
            xmrdb.DatabaseConfig.from_env(
                {
                    "XMR_DB_PASSWORD": "secret",
                    "XMR_P2POOL_PORT_MIN": "30000",
                    "XMR_P2POOL_PORT_MAX": "20000",
                }
            )

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

    def test_creates_admin_account(self):
        account = self.database.create_account("operator", "argon2-hash", role="admin")

        self.assertEqual(account.account_id, 7)
        self.assertEqual(account.role, "admin")
        self.assertEqual(
            self.connection.cursors[0].parameters,
            ("operator", "argon2-hash", "admin"),
        )

    def test_creates_miner_with_transactionally_allocated_port(self):
        account = self.database.create_miner_account(
            "miner", "argon2-hash", "4" * 95
        )

        self.assertEqual(account.account_id, 7)
        self.assertEqual(account.p2pool_port, 20000)
        self.assertTrue(self.connection.committed)
        statements = [" ".join(cursor.statement.split()) for cursor in self.connection.cursors]
        self.assertTrue(any("FOR UPDATE" in statement for statement in statements))
        self.assertTrue(any("INSERT INTO miner_profiles" in statement for statement in statements))

    def test_transaction_rolls_back_on_error(self):
        with self.assertRaises(RuntimeError):
            with self.database.transaction():
                raise RuntimeError("failed")

        self.assertTrue(self.connection.rolled_back)
        self.assertFalse(self.connection.committed)
        self.assertTrue(self.connection.closed)

    def test_reset_drops_only_application_tables_in_dependency_order(self):
        self.database.reset_schema()

        statements = [" ".join(cursor.statement.split()) for cursor in self.connection.cursors]
        self.assertEqual(
            statements,
            [
                "DROP TABLE IF EXISTS miner_profiles",
                "DROP TABLE IF EXISTS p2pool_port_allocator",
                "DROP TABLE IF EXISTS accounts",
                "DROP TABLE IF EXISTS schema_migrations",
            ],
        )

    def test_loads_private_environment_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "xmr.env"
            path.write_text(
                'XMR_DB_USER=xmr\nXMR_DB_PASSWORD="secret with spaces"\n',
                encoding="utf-8",
            )

            config = xmrdb.DatabaseConfig.from_env_file(path)

        self.assertEqual(config.user, "xmr")
        self.assertEqual(config.password, "secret with spaces")


if __name__ == "__main__":
    unittest.main()
