from dataclasses import dataclass


@dataclass
class UpgradeSpec:
    """Represents an upgrade bundle that can be applied to a server."""

    name: str
    add_vcpu: int = 0
    add_memory_mb: int = 0
    add_disk_gb: int = 0
    price: float | None = None
    description: str | None = None
