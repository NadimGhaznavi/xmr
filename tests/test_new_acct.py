import sys
import types
import unittest
from pathlib import Path


WEB_DIR = Path(__file__).parents[1] / "web"
sys.path.insert(0, str(WEB_DIR))

argon2_stub = types.ModuleType("argon2")
argon2_stub.PasswordHasher = object
sys.modules.setdefault("argon2", argon2_stub)

from methods.new_acct import (  # noqa: E402
    AccountAlreadyExistsError,
    AccountValidationError,
    NewAccount,
)
from xmrdb import CreatedMinerAccount, DuplicateAccountError  # noqa: E402


VALID_WALLET = "4" + ("1" * 94)


class FakeHasher:
    def hash(self, password):
        return f"hashed:{password}"


class FakeDatabase:
    def __init__(self, *, duplicate=False):
        self.duplicate = duplicate
        self.arguments = None

    def create_miner_account(self, username, password_hash, wallet_address):
        self.arguments = (username, password_hash, wallet_address)
        if self.duplicate:
            raise DuplicateAccountError("duplicate")
        return CreatedMinerAccount(7, username, wallet_address, 20000)


class NewAccountTest(unittest.TestCase):
    def test_validates_before_hashing(self):
        use_case = NewAccount(FakeDatabase(), password_hasher=FakeHasher())

        with self.assertRaises(AccountValidationError) as raised:
            use_case.execute("bad username!", "short", "invalid")

        self.assertEqual(
            set(raised.exception.errors), {"username", "password", "wallet"}
        )

    def test_hashes_password_and_creates_miner(self):
        database = FakeDatabase()
        use_case = NewAccount(database, password_hasher=FakeHasher())

        account = use_case.execute(" miner ", "long-secure-password", VALID_WALLET)

        self.assertEqual(account.p2pool_port, 20000)
        self.assertEqual(
            database.arguments,
            ("miner", "hashed:long-secure-password", VALID_WALLET),
        )

    def test_translates_duplicate_account_error(self):
        use_case = NewAccount(
            FakeDatabase(duplicate=True), password_hasher=FakeHasher()
        )

        with self.assertRaises(AccountAlreadyExistsError):
            use_case.execute("miner", "long-secure-password", VALID_WALLET)


if __name__ == "__main__":
    unittest.main()
