"""Tests for account-management workflows."""

import unittest

from mgr.AcctMgr import (
    AccountAlreadyExistsError,
    AccountValidationError,
    AcctMgr,
)
from db.AcctDb import CreatedMinerAccount, DuplicateAccountError


VALID_WALLET = "4" + ("1" * 94)


class FakeHasher:
    def hash(self, password):
        return f"hashed:{password}"


class FakeDatabase:
    def __init__(self, *, duplicate=False):
        self.duplicate = duplicate
        self.arguments = None

    def create_account(self, username, password_hash, *, role="user"):
        raise NotImplementedError

    def create_miner_account(self, username, password_hash, wallet_address):
        self.arguments = (username, password_hash, wallet_address)
        if self.duplicate:
            raise DuplicateAccountError("duplicate")
        return CreatedMinerAccount(7, username, wallet_address, 20000)


class AcctMgrTest(unittest.TestCase):
    def test_validates_before_hashing(self):
        accounts = AcctMgr(FakeDatabase(), password_hasher=FakeHasher())

        with self.assertRaises(AccountValidationError) as raised:
            accounts.create_miner_account("bad username!", "short", "invalid")

        self.assertEqual(
            set(raised.exception.errors), {"username", "password", "wallet"}
        )

    def test_hashes_password_and_creates_miner(self):
        database = FakeDatabase()
        accounts = AcctMgr(database, password_hasher=FakeHasher())

        account = accounts.create_miner_account(
            " miner ", "long-secure-password", VALID_WALLET
        )

        self.assertEqual(account.p2pool_port, 20000)
        self.assertEqual(
            database.arguments,
            ("miner", "hashed:long-secure-password", VALID_WALLET),
        )

    def test_translates_duplicate_account_error(self):
        accounts = AcctMgr(FakeDatabase(duplicate=True), password_hasher=FakeHasher())

        with self.assertRaises(AccountAlreadyExistsError):
            accounts.create_miner_account("miner", "long-secure-password", VALID_WALLET)


if __name__ == "__main__":
    unittest.main()
