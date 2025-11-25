import json
import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from app.domain.models.user import User


class UserRepository:
    """SQLite-backed persistence for user entities."""

    def __init__(self, db_path: str | Path = Path("data/users.db")):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                external_provider TEXT NOT NULL,
                external_id TEXT NOT NULL,
                external_claims TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(external_provider, external_id)
            )
            """
        )
        self._conn.commit()

    def _row_to_user(self, row: sqlite3.Row) -> User:
        return User(
            id=UUID(row["id"]),
            email=row["email"],
            phone_number=row["phone_number"],
            external_provider=row["external_provider"],
            external_id=row["external_id"],
            external_claims=json.loads(row["external_claims"]) if row["external_claims"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def add(self, user: User) -> None:
        self._conn.execute(
            """
            INSERT INTO users (id, email, phone_number, external_provider, external_id, external_claims, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(user.id),
                user.email,
                user.phone_number,
                user.external_provider,
                user.external_id,
                json.dumps(user.external_claims),
                user.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def update(self, user: User) -> None:
        self._conn.execute(
            """
            UPDATE users
            SET email = ?, phone_number = ?, external_claims = ?
            WHERE id = ?
            """,
            (user.email, user.phone_number, json.dumps(user.external_claims), str(user.id)),
        )
        self._conn.commit()

    def get(self, user_id: UUID) -> Optional[User]:
        row = self._conn.execute("SELECT * FROM users WHERE id = ?", (str(user_id),)).fetchone()
        return self._row_to_user(row) if row else None

    def get_by_external(self, provider: str, external_id: str) -> Optional[User]:
        row = self._conn.execute(
            "SELECT * FROM users WHERE external_provider = ? AND external_id = ?",
            (provider, external_id),
        ).fetchone()
        return self._row_to_user(row) if row else None

    def list(self) -> Iterable[User]:
        rows = self._conn.execute("SELECT * FROM users").fetchall()
        return [self._row_to_user(row) for row in rows]

    def upsert_from_external(
        self,
        *,
        email: str,
        phone_number: str,
        external_provider: str,
        external_id: str,
        external_claims: dict[str, str] | None = None,
    ) -> User:
        existing = self.get_by_external(external_provider, external_id)
        claims = external_claims or {}
        if existing:
            existing.email = email
            existing.phone_number = phone_number
            existing.external_claims = claims
            self.update(existing)
            return existing

        user = User(
            email=email,
            phone_number=phone_number,
            external_provider=external_provider,
            external_id=external_id,
            external_claims=claims,
        )
        self.add(user)
        return user
