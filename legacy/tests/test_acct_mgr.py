"""Tests for account-management workflows."""

import unittest

from db.AppDb import DuplicateUserError, User
from mgr.AcctMgr import (
    AccountAlreadyExistsError,
    AccountValidationError,
    AcctMgr,
)

VALID_WALLET = "4" + ("1" * 94)


class FakeHasher:
    def hash(self, password):
        return f"hashed:{password}"

    def verify(self, password_hash, password):
        return password_hash == f"hashed:{password}"


class FakeDatabase:
    def __init__(self, *, duplicate=False):
        self.duplicate = duplicate
        self.arguments = None

    def create_user(self, username, password_hash, wallet_address, *, role="user"):
        self.arguments = (username, password_hash, wallet_address)
        if self.duplicate:
            raise DuplicateUserError("duplicate")
        return User(7, username, wallet_address, role)

    def find_login_account(self, username):
        return None


class AcctMgrTest(unittest.TestCase):
    def test_validates_before_hashing(self):
        accounts = AcctMgr(FakeDatabase(), password_hasher=FakeHasher())

        with self.assertRaises(AccountValidationError) as raised:
            accounts.create_user("bad username!", "short", "invalid")

        self.assertEqual(
            set(raised.exception.errors), {"username", "password", "wallet"}
        )

    def test_hashes_password_and_creates_user(self):
        database = FakeDatabase()
        accounts = AcctMgr(database, password_hasher=FakeHasher())

        user = accounts.create_user(" miner ", "long-secure-password", VALID_WALLET)

        self.assertEqual(user.user_id, 7)
        self.assertEqual(
            database.arguments,
            ("miner", "hashed:long-secure-password", VALID_WALLET),
        )

    def test_translates_duplicate_account_error(self):
        accounts = AcctMgr(FakeDatabase(duplicate=True), password_hasher=FakeHasher())

        with self.assertRaises(AccountAlreadyExistsError):
            accounts.create_user("miner", "long-secure-password", VALID_WALLET)


if __name__ == "__main__":
    unittest.main()
