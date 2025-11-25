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
    vcpu: int
    memory_gb: int
    disk_gb: int
    node: str
    storage_pool: str
    status: ServerStatus = ServerStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    external_id: str | None = None

    def proxmox_params(self) -> dict[str, str | int]:
        """Translate selected specs to Proxmox creation parameters."""

        return {
            "node": self.node,
            "cores": self.vcpu,
            "memory_mb": self.memory_gb * 1024,
            "disk_gb": self.disk_gb,
            "storage_pool": self.storage_pool,
        }
