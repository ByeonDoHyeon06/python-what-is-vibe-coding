from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.models.plan import Plan
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


class PlanBase(BaseModel):
    name: str
    vcpu: int = Field(..., gt=0)
    memory_gb: int = Field(..., gt=0)
    disk_gb: int = Field(..., gt=0)
    default_node: str
    default_storage_pool: str


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    vcpu: int | None = Field(None, gt=0)
    memory_gb: int | None = Field(None, gt=0)
    disk_gb: int | None = Field(None, gt=0)
    default_node: str | None = None
    default_storage_pool: str | None = None


class PlanRead(PlanBase):
    @classmethod
    def from_entity(cls, plan: Plan) -> "PlanRead":
        return cls(
            name=plan.name,
            vcpu=plan.vcpu,
            memory_gb=plan.memory_gb,
            disk_gb=plan.disk_gb,
            default_node=plan.default_node,
            default_storage_pool=plan.default_storage_pool,
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
    vcpu: int
    memory_gb: int
    disk_gb: int
    node: str
    storage_pool: str
    status: ServerStatus
    external_id: str | None

    @classmethod
    def from_entity(cls, server: Server) -> "ServerRead":
        return cls(
            id=server.id,
            owner_id=server.owner_id,
            plan=server.plan,
            location=server.location,
            vcpu=server.vcpu,
            memory_gb=server.memory_gb,
            disk_gb=server.disk_gb,
            node=server.node,
            storage_pool=server.storage_pool,
            status=server.status,
            external_id=server.external_id,
        )
