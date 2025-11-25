from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.models.plan import PlanSpec
from app.domain.models.server import Server, ServerStatus
from app.domain.models.proxmox_host import ProxmoxHostConfig
from app.domain.models.user import User


class UserCreate(BaseModel):
    email: EmailStr
    phone_number: str = Field(..., min_length=8)
    external_auth_id: str | None = Field(
        default=None, description="External auth provider user id to link with"
    )


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    phone_number: str
    external_auth_id: str | None

    @classmethod
    def from_entity(cls, user: User) -> "UserRead":
        return cls(
            id=user.id,
            email=user.email,
            phone_number=user.phone_number,
            external_auth_id=user.external_auth_id,
        )


class ServerCreate(BaseModel):
    user_id: UUID
    plan: str
    location: str
    expire_in_days: int | None = Field(
        default=None,
        description="Optional number of days until expiration",
        gt=0,
    )


class ServerRead(BaseModel):
    id: UUID
    owner_id: UUID
    plan: str
    location: str
    proxmox_host_id: str | None
    proxmox_node: str | None
    vcpu: int | None
    memory_mb: int | None
    disk_gb: int | None
    expire_in_days: int | None
    expire_at: str | None
    created_at: str
    status: ServerStatus
    external_id: str | None

    @classmethod
    def from_entity(cls, server: Server) -> "ServerRead":
        return cls(
            id=server.id,
            owner_id=server.owner_id,
            plan=server.plan,
            location=server.location,
            proxmox_host_id=server.proxmox_host_id,
            proxmox_node=server.proxmox_node,
            vcpu=server.vcpu,
            memory_mb=server.memory_mb,
            disk_gb=server.disk_gb,
            expire_in_days=server.expire_in_days,
            expire_at=server.expire_at.isoformat() if server.expire_at else None,
            created_at=server.created_at.isoformat(),
            status=server.status,
            external_id=server.external_id,
        )


class ServerExtendRequest(BaseModel):
    additional_days: int = Field(..., gt=0, description="Days to add to current expire_in_days")


class PlanCreate(BaseModel):
    name: str
    vcpu: int = Field(..., gt=0)
    memory_mb: int = Field(..., gt=256)
    disk_gb: int = Field(..., gt=5)
    location: str
    proxmox_host_id: str | None = None
    proxmox_node: str | None = None
    template_vmid: int | None = Field(
        default=None, description="Optional template VMID to clone when provisioning"
    )
    disk_storage: str | None = Field(
        default=None, description="Preferred storage target when creating/cloning"
    )
    description: str | None = None


class PlanRead(BaseModel):
    name: str
    vcpu: int
    memory_mb: int
    disk_gb: int
    location: str
    proxmox_host_id: str | None
    proxmox_node: str | None
    template_vmid: int | None
    disk_storage: str | None
    description: str | None

    @classmethod
    def from_entity(cls, plan: PlanSpec) -> "PlanRead":
        return cls(**plan.__dict__)


class ProxmoxHostCreate(BaseModel):
    id: str = Field(..., description="Internal identifier for referencing the host")
    api_url: str = Field(..., example="https://pve1.local")
    username: str
    password: str
    realm: str = Field("pam", description="Authentication realm, e.g. pam or pve")
    node: str | None = Field(None, description="Default node name to schedule on")
    location: str = Field("kr-central", description="Geographic/location tag")


class ProxmoxHostRead(BaseModel):
    id: str
    api_url: str
    username: str
    realm: str
    node: str | None
    location: str

    @classmethod
    def from_entity(cls, host: ProxmoxHostConfig) -> "ProxmoxHostRead":
        return cls(
            id=host.id,
            api_url=host.api_url,
            username=host.username,
            realm=host.realm,
            node=host.node,
            location=host.location,
        )
