from app.domain.models.user import User
from app.infrastructure.repositories.user_repository import UserRepository


class RegisterUser:
    """Create and persist a user entity."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(
        self,
        *,
        email: str,
        phone_number: str,
        external_provider: str,
        external_id: str,
        external_claims: dict[str, str] | None = None,
    ) -> User:
        return self.repository.upsert_from_external(
            email=email,
            phone_number=phone_number,
            external_provider=external_provider,
            external_id=external_id,
            external_claims=external_claims,
        )
