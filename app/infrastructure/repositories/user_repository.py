from collections.abc import Iterable
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select

from app.domain.models.user import User
from app.infrastructure.storage.sqlite import SQLAlchemyDataStore, UserModel


class UserRepository:
    """SQLAlchemy-backed repository for users."""

    def __init__(self, db: SQLAlchemyDataStore):
        self.db = db

    def add(self, user: User) -> None:
        with self.db.session() as session:
            if user.external_auth_id:
                existing = session.scalar(
                    select(UserModel).where(UserModel.external_auth_id == user.external_auth_id)
                )
                if existing:
                    existing.email = user.email
                    existing.phone_number = user.phone_number
                    existing.id = str(user.id)
                    session.commit()
                    return

            existing_by_id = session.get(UserModel, str(user.id))
            if existing_by_id:
                existing_by_id.email = user.email
                existing_by_id.phone_number = user.phone_number
                existing_by_id.external_auth_id = user.external_auth_id
            else:
                session.add(
                    UserModel(
                        id=str(user.id),
                        email=user.email,
                        phone_number=user.phone_number,
                        external_auth_id=user.external_auth_id,
                        created_at=user.created_at,
                    )
                )
            session.commit()

    def get(self, user_id: UUID) -> Optional[User]:
        with self.db.session() as session:
            row = session.get(UserModel, str(user_id))
            return self._model_to_user(row) if row else None

    def get_by_external_auth(self, external_auth_id: str) -> Optional[User]:
        with self.db.session() as session:
            row = session.scalar(select(UserModel).where(UserModel.external_auth_id == external_auth_id))
            return self._model_to_user(row) if row else None

    def list(self) -> Iterable[User]:
        with self.db.session() as session:
            rows = session.scalars(select(UserModel)).all()
            return [self._model_to_user(row) for row in rows]

    @staticmethod
    def _model_to_user(row: UserModel) -> User:
        return User(
            id=UUID(row.id),
            email=row.email,
            phone_number=row.phone_number,
            external_auth_id=row.external_auth_id,
            created_at=row.created_at if isinstance(row.created_at, datetime) else datetime.fromisoformat(row.created_at),
        )
