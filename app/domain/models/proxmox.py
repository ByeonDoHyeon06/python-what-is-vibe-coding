from dataclasses import dataclass, field
from typing import Set


@dataclass
class ProxmoxHost:
    """Metadata about a Proxmox host and its available nodes."""

    name: str
    nodes: Set[str] = field(default_factory=set)

