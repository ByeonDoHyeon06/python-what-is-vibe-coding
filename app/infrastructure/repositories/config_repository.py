from collections.abc import Iterable
from typing import Dict, Set

from app.domain.models.proxmox import ProxmoxHost


class ProvisioningConfigRepository:
    """Stores mutable provisioning configuration such as allowed plans and hosts."""

    def __init__(self):
        self._allowed_locations: Set[str] = {"kr-central", "jp-east"}
        self._allowed_plans: Set[str] = {"basic", "pro"}
        self._proxmox_hosts: Dict[str, ProxmoxHost] = {}

    def get_allowed_locations(self) -> Set[str]:
        return set(self._allowed_locations)

    def set_allowed_locations(self, locations: Iterable[str]) -> None:
        self._allowed_locations = {loc.strip() for loc in locations if loc and loc.strip()}

    def get_allowed_plans(self) -> Set[str]:
        return set(self._allowed_plans)

    def set_allowed_plans(self, plans: Iterable[str]) -> None:
        self._allowed_plans = {plan.strip() for plan in plans if plan and plan.strip()}

    def list_proxmox_hosts(self) -> list[ProxmoxHost]:
        return list(self._proxmox_hosts.values())

    def upsert_proxmox_host(self, name: str, nodes: Iterable[str]) -> ProxmoxHost:
        host = ProxmoxHost(name=name, nodes={node.strip() for node in nodes if node and node.strip()})
        self._proxmox_hosts[name] = host
        return host

    def delete_proxmox_host(self, name: str) -> bool:
        return self._proxmox_hosts.pop(name, None) is not None

