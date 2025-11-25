from collections.abc import Iterable
from typing import Dict, Optional
from uuid import UUID

from app.domain.models.user import User


class UserRepository:
    """Simple in-memory repository. Swap with DB implementation later."""

    def __init__(self):
        self._users: Dict[UUID, User] = {}

    def add(self, user: User) -> None:
        self._users[user.id] = user

    def get(self, user_id: UUID) -> Optional[User]:
        return self._users.get(user_id)

    def list(self) -> Iterable[User]:
        return self._users.values()
