"""Account application workflows."""

from __future__ import annotations

from db.AcctDb import (
    AccountRole,
    AcctDb,
    CreatedAccount,
    CreatedMinerAccount,
)


class AcctMgr:
    """Validate account requests and pass persistence work to ``AcctDb``."""

    def __init__(self, database: AcctDb | None = None) -> None:
        self._database = database or AcctDb()

    def create_account(
        self, username: str, password_hash: str, *, role: AccountRole = "user"
    ) -> CreatedAccount:
        self._validate_account(username, password_hash, role)
        return self._database.create_account(username, password_hash, role=role)

    def create_miner_account(
        self, username: str, password_hash: str, wallet_address: str
    ) -> CreatedMinerAccount:
        self._validate_account(username, password_hash, "user")
        if not wallet_address or len(wallet_address) > 106:
            raise ValueError("wallet address must contain 1 to 106 characters")
        return self._database.create_miner_account(
            username, password_hash, wallet_address
        )

    @staticmethod
    def _validate_account(
        username: str, password_hash: str, role: AccountRole
    ) -> None:
        if not username or len(username) > 64:
            raise ValueError("username must contain 1 to 64 characters")
        if not password_hash or len(password_hash) > 255:
            raise ValueError("password hash must contain 1 to 255 characters")
        if role not in {"user", "admin"}:
            raise ValueError("role must be 'user' or 'admin'")
