"""Authentication cases added after the original account-creation tests."""

import unittest

from db.AppDb import LoginAccount, User
from mgr.AcctMgr import AcctMgr, InvalidCredentialsError

WALLET = "4" + "1" * 94


class Hasher:
    def __init__(self, valid=True, error=False):
        self.valid = valid
        self.error = error
        self.verified = []

    def hash(self, password):
        return f"hashed:{password}"

    def verify(self, password_hash, password):
        self.verified.append((password_hash, password))
        if self.error:
            raise ValueError("bad hash")
        return self.valid


class Accounts:
    def __init__(self, account=None):
        self.account = account
        self.usernames = []

    def create_user(self, username, password_hash, wallet_address, *, role="user"):
        return User(7, username, wallet_address, role)

    def find_login_account(self, username):
        self.usernames.append(username)
        return self.account


class AuthenticateTest(unittest.TestCase):
    def test_authenticates_active_account_and_strips_username(self):
        user = User(7, "miner", WALLET, "user")
        database = Accounts(LoginAccount(user, "stored-hash"))
        hasher = Hasher()

        result = AcctMgr(database, password_hasher=hasher).authenticate(
            " miner ", "correct"
        )

        self.assertEqual(result, user)
        self.assertEqual(database.usernames, ["miner"])
        self.assertEqual(hasher.verified, [("stored-hash", "correct")])

    def test_missing_account_uses_generic_error(self):
        with self.assertRaisesRegex(InvalidCredentialsError, "invalid credentials"):
            AcctMgr(Accounts(), password_hasher=Hasher()).authenticate("none", "x")

    def test_wrong_password_uses_generic_error(self):
        user = User(7, "miner", WALLET, "user")
        account = LoginAccount(user, "stored-hash")
        with self.assertRaisesRegex(InvalidCredentialsError, "invalid credentials"):
            AcctMgr(
                Accounts(account), password_hasher=Hasher(valid=False)
            ).authenticate("miner", "wrong")

    def test_disabled_account_uses_generic_error(self):
        user = User(7, "miner", WALLET, "user", status="disabled")
        account = LoginAccount(user, "stored-hash")
        with self.assertRaisesRegex(InvalidCredentialsError, "invalid credentials"):
            AcctMgr(Accounts(account), password_hasher=Hasher()).authenticate(
                "miner", "correct"
            )

    def test_invalid_stored_hash_uses_generic_error(self):
        user = User(7, "miner", WALLET, "user")
        account = LoginAccount(user, "broken")
        with self.assertRaises(InvalidCredentialsError):
            AcctMgr(Accounts(account), password_hasher=Hasher(error=True)).authenticate(
                "miner", "correct"
            )


if __name__ == "__main__":
    unittest.main()
