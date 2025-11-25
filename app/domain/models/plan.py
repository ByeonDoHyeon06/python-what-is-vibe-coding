from dataclasses import dataclass


@dataclass
class Plan:
    """Catalog entry describing a provisionable plan."""

    name: str
    vcpu: int
    memory_gb: int
    disk_gb: int
    default_node: str
    default_storage_pool: str
