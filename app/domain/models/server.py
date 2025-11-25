from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ServerStatus(str, Enum):
    PENDING = "pending"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Server:
    """Server entity tracked in the domain."""

    owner_id: UUID
    plan: str
    location: str
    proxmox_host_id: str | None = None
    proxmox_node: str | None = None
    vcpu: int | None = None
    memory_mb: int | None = None
    disk_gb: int | None = None
    status: ServerStatus = ServerStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    external_id: str | None = None
