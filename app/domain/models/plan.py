from dataclasses import dataclass


@dataclass
class PlanSpec:
    """Represents an admin-defined hosting plan with performance presets."""

    name: str
    vcpu: int
    memory_mb: int
    disk_gb: int
    location: str
    proxmox_host_id: str | None = None
    proxmox_node: str | None = None
    description: str | None = None
