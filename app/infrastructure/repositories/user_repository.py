from collections.abc import Iterable
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.models.user import User
from app.infrastructure.storage.sqlite import SQLiteDataStore


class UserRepository:
    """SQLite-backed repository for users."""

    def __init__(self, db: SQLiteDataStore):
        self.db = db

    def add(self, user: User) -> None:
        self.db.execute(
            """
            INSERT INTO users (id, email, phone_number, external_auth_id, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                email=excluded.email,
                phone_number=excluded.phone_number,
                external_auth_id=excluded.external_auth_id
            """,
            (
                str(user.id),
                user.email,
                user.phone_number,
                user.external_auth_id,
                user.created_at.isoformat(),
            ),
        )

    def get(self, user_id: UUID) -> Optional[User]:
        row = self.db.fetch_one("SELECT * FROM users WHERE id = ?", (str(user_id),))
        return self._row_to_user(row) if row else None

    def list(self) -> Iterable[User]:
        rows = self.db.fetch_all("SELECT * FROM users")
        return [self._row_to_user(row) for row in rows]

    @staticmethod
    def _row_to_user(row) -> User:
        return User(
            id=UUID(row["id"]),
            email=row["email"],
            phone_number=row["phone_number"],
            external_auth_id=row["external_auth_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
