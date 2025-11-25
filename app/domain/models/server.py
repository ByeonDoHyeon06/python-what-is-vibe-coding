from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4


class ServerStatus(str, Enum):
    PENDING = "pending"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    STOPPED = "stopped"
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
    disk_storage: str | None = None
    expire_in_days: int | None = None
    status: ServerStatus = ServerStatus.PENDING
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    external_id: str | None = None
    last_notified_at: datetime | None = None

    @property
    def expire_at(self) -> datetime | None:
        if self.expire_in_days is None:
            return None
        return self.created_at + timedelta(days=self.expire_in_days)
