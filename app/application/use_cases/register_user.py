from app.domain.models.user import User
from app.infrastructure.repositories.user_repository import UserRepository


class RegisterUser:
    """Create and persist a user entity."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, email: str, phone_number: str) -> User:
        user = User(email=email, phone_number=phone_number)
        self.repository.add(user)
        return user
