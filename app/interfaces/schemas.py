from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.models.server import Server, ServerStatus
from app.domain.models.user import User


class UserCreate(BaseModel):
    email: EmailStr
    phone_number: str = Field(..., min_length=8)
    external_provider: str = Field(..., min_length=1)
    external_id: str = Field(..., min_length=1)
    external_claims: dict[str, str] = Field(default_factory=dict)


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    phone_number: str
    external_provider: str
    external_id: str
    external_claims: dict[str, str]

    @classmethod
    def from_entity(cls, user: User) -> "UserRead":
        return cls(
            id=user.id,
            email=user.email,
            phone_number=user.phone_number,
            external_provider=user.external_provider,
            external_id=user.external_id,
            external_claims=user.external_claims,
        )


class ServerCreate(BaseModel):
    user_id: UUID
    plan: str
    location: str


class ServerRead(BaseModel):
    id: UUID
    owner_id: UUID
    plan: str
    location: str
    status: ServerStatus
    external_id: str | None

    @classmethod
    def from_entity(cls, server: Server) -> "ServerRead":
        return cls(
            id=server.id,
            owner_id=server.owner_id,
            plan=server.plan,
            location=server.location,
            status=server.status,
            external_id=server.external_id,
        )
