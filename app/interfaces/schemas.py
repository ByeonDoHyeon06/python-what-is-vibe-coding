from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.models.proxmox import ProxmoxHost
from app.domain.models.server import Server, ServerStatus
from app.domain.models.user import User


class UserCreate(BaseModel):
    email: EmailStr
    phone_number: str = Field(..., min_length=8)


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    phone_number: str

    @classmethod
    def from_entity(cls, user: User) -> "UserRead":
        return cls(id=user.id, email=user.email, phone_number=user.phone_number)


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


class AllowedSettings(BaseModel):
    allowed_locations: list[str]
    allowed_plans: list[str]


class AllowedSettingsUpdate(BaseModel):
    allowed_locations: list[str] | None = None
    allowed_plans: list[str] | None = None


class ProxmoxHostRead(BaseModel):
    name: str
    nodes: list[str]

    @classmethod
    def from_entity(cls, host: ProxmoxHost) -> "ProxmoxHostRead":
        return cls(name=host.name, nodes=sorted(host.nodes))


class ProxmoxHostUpdate(BaseModel):
    nodes: list[str]
