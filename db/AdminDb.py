"""Account-administration persistence backed by MariaDB."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .AppDb import DuplicateUserError, User, UserRole, UserStatus
from .DbMgr import DbMgr
from .XmrDb import DatabaseConfig, XmrDb


class AccountNotFoundError(LookupError):
    pass


class AdminDb:
    """Expose only the data operations required by account administration."""

    def __init__(self, database: DbMgr | None = None) -> None:
        self._database = database or XmrDb(
            DatabaseConfig.from_env(prefix="XMR_ADMIN_DB_")
        )

    def site_data_is_writable(self) -> bool:
        row = self._database.fetch_one("SELECT @@GLOBAL.read_only AS read_only")
        return row is not None and not bool(row["read_only"])

    def list_accounts(self) -> list[User]:
        rows = self._database.fetch_all(
            """
            SELECT id, username, wallet_address, role, status, created_at,
                   disabled_at
            FROM users
            ORDER BY id
            """
        )
        return [_user_from_row(row) for row in rows]

    def get_account(self, account_id: int) -> User:
        row = self._database.fetch_one(
            """
            SELECT id, username, wallet_address, role, status, created_at,
                   disabled_at
            FROM users
            WHERE id = ?
            """,
            (account_id,),
        )
        if row is None:
            raise AccountNotFoundError(f"account {account_id} does not exist")
        return _user_from_row(row)

    def update_account(
        self, account_id: int, username: str, wallet_address: str
    ) -> User:
        try:
            result = self._database.execute(
                """
                UPDATE users SET username = ?, wallet_address = ?
                WHERE id = ?
                """,
                (username, wallet_address, account_id),
            )
        except Exception as error:
            if getattr(error, "errno", None) == 1062:
                raise DuplicateUserError("username or wallet already exists") from error
            raise
        if result.affected_rows == 0:
            self.get_account(account_id)
        return self.get_account(account_id)

    def set_account_status(self, account_id: int, status: UserStatus) -> User:
        disabled_at = (
            datetime.now(UTC).replace(tzinfo=None) if status == "disabled" else None
        )
        with self._database.transaction() as session:
            result = session.execute(
                """
                UPDATE users SET status = ?, disabled_at = ?
                WHERE id = ?
                """,
                (status, disabled_at, account_id),
            )
            if result.affected_rows == 0:
                row = session.fetch_one(
                    "SELECT id FROM users WHERE id = ?", (account_id,)
                )
                if row is None:
                    raise AccountNotFoundError(f"account {account_id} does not exist")
            if status == "disabled":
                session.execute(
                    """
                    UPDATE sessions SET revoked_at = ?
                    WHERE account_id = ? AND revoked_at IS NULL
                    """,
                    (disabled_at, account_id),
                )
        return self.get_account(account_id)


def _user_from_row(row: dict[str, Any]) -> User:
    return User(
        int(row["id"]),
        str(row["username"]),
        str(row["wallet_address"]),
        _role(row["role"]),
        _status(row["status"]),
        row["created_at"],
        row["disabled_at"],
    )


def _role(value: object) -> UserRole:
    if value not in {"user", "admin"}:
        raise ValueError("database returned an invalid user role")
    return value  # type: ignore[return-value]


def _status(value: object) -> UserStatus:
    if value not in {"active", "disabled"}:
        raise ValueError("database returned an invalid user status")
    return value  # type: ignore[return-value]
