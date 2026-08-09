"""Tests for MariaDB configuration and transaction management."""

import tempfile
import unittest
from pathlib import Path

from db.XmrDb import DatabaseConfig, DatabaseConfigurationError, XmrDb


class Cursor:
    def __init__(self, rows=()):
        self.description = (("id",), ("name",))
        self.lastrowid = 9
        self.rowcount = 1
        self.rows = list(rows)
        self.executed = []
        self.closed = False

    def execute(self, statement, parameters=()):
        self.executed.append((statement, parameters))

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


class Connection:
    def __init__(self, cursor=None):
        self.current_cursor = cursor or Cursor()
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.current_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class XmrDbTest(unittest.TestCase):
    def test_reads_defaults_and_required_password(self):
        config = DatabaseConfig.from_env({"XMR_DB_PASSWORD": "secret"})
        self.assertEqual(
            (config.host, config.port, config.database, config.user),
            ("localhost", 3306, "xmr", "xmr"),
        )
        with self.assertRaisesRegex(DatabaseConfigurationError, "PASSWORD is required"):
            DatabaseConfig.from_env({})

    def test_validates_numeric_configuration(self):
        with self.assertRaisesRegex(DatabaseConfigurationError, "must be an integer"):
            DatabaseConfig.from_env(
                {"XMR_DB_PASSWORD": "secret", "XMR_DB_PORT": "not-a-port"}
            )
        with self.assertRaisesRegex(DatabaseConfigurationError, "valid range"):
            DatabaseConfig.from_env(
                {"XMR_DB_PASSWORD": "secret", "XMR_DB_PORT": "65536"}
            )

    def test_reads_restricted_environment_file_syntax(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "xmr.env"
            path.write_text(
                "# comment\nXMR_DB_PASSWORD='secret value'\nXMR_DB_PORT=3307\n",
                encoding="utf-8",
            )
            config = DatabaseConfig.from_env_file(path)
            self.assertEqual((config.password, config.port), ("secret value", 3307))
            path.write_text("UNRELATED=value\n", encoding="utf-8")
            with self.assertRaisesRegex(DatabaseConfigurationError, "unexpected"):
                DatabaseConfig.from_env_file(path)

    def test_execute_commits_and_closes_resources(self):
        connection = Connection()
        options = []

        def connector(**values):
            options.append(values)
            return connection

        config = DatabaseConfig("db", 3307, "xmr", "user", "secret", 4)
        result = XmrDb(config, connector=connector).execute("UPDATE t SET n = ?", (2,))
        self.assertEqual((result.affected_rows, result.last_insert_id), (1, 9))
        self.assertEqual(options[0]["connect_timeout"], 4)
        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)
        self.assertTrue(connection.current_cursor.closed)

    def test_transaction_rolls_back_and_closes_on_error(self):
        connection = Connection()
        database = XmrDb(
            DatabaseConfig("db", 3306, "xmr", "user", "secret"),
            connector=lambda **unused: connection,
        )
        with self.assertRaisesRegex(RuntimeError, "failure"):
            with database.transaction():
                raise RuntimeError("failure")
        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)
        self.assertTrue(connection.closed)

    def test_fetches_rows_as_named_dictionaries(self):
        connection = Connection(Cursor(((7, "miner"),)))
        database = XmrDb(
            DatabaseConfig("db", 3306, "xmr", "user", "secret"),
            connector=lambda **unused: connection,
        )
        self.assertEqual(
            database.fetch_one("SELECT id, name"), {"id": 7, "name": "miner"}
        )


if __name__ == "__main__":
    unittest.main()
