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
    template_vmid: int | None = None
    disk_storage: str | None = None
    clone_mode: str = "full"
    price: float | None = None
    default_expire_days: int | None = None
    description: str | None = None
