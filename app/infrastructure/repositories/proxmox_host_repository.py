from typing import Dict, Iterable, Optional

from app.domain.models.proxmox_host import ProxmoxHostConfig


class ProxmoxHostRepository:
    """In-memory metadata store for Proxmox hosts and nodes."""

    def __init__(self):
        self._hosts: Dict[str, ProxmoxHostConfig] = {}

    def add(self, host: ProxmoxHostConfig) -> None:
        self._hosts[host.id] = host

    def get(self, host_id: str) -> Optional[ProxmoxHostConfig]:
        return self._hosts.get(host_id)

    def list(self) -> Iterable[ProxmoxHostConfig]:
        return self._hosts.values()

    def first_for_location(self, location: str) -> Optional[ProxmoxHostConfig]:
        for host in self._hosts.values():
            if host.location == location:
                return host
        return None
