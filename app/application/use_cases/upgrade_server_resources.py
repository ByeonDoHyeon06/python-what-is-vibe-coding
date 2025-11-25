from uuid import UUID

from app.infrastructure.clients.proxmox import ProxmoxClient
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.infrastructure.repositories.server_repository import ServerRepository
from app.infrastructure.repositories.upgrade_repository import UpgradeRepository


class UpgradeServerResources:
    """Apply an upgrade bundle to an existing server and push changes to Proxmox."""

    def __init__(
        self,
        server_repo: ServerRepository,
        upgrade_repo: UpgradeRepository,
        proxmox_hosts: ProxmoxHostRepository,
        proxmox_client: ProxmoxClient,
    ):
        self.server_repo = server_repo
        self.upgrade_repo = upgrade_repo
        self.proxmox_hosts = proxmox_hosts
        self.proxmox_client = proxmox_client

    def apply(self, server_id: UUID, upgrade_name: str, user_id: UUID) -> "Server":
        server = self.server_repo.get(server_id)
        if not server:
            raise ValueError("Server not found")

        if server.owner_id != user_id:
            raise ValueError("User is not allowed to upgrade this server")

        upgrade = self.upgrade_repo.get(upgrade_name)
        if not upgrade:
            raise ValueError("Upgrade bundle not found")

        if not server.external_id:
            raise ValueError("Server has no Proxmox external_id; cannot upgrade")
        if not server.proxmox_host_id:
            raise ValueError("Server is missing Proxmox host mapping")

        host = self.proxmox_hosts.get(server.proxmox_host_id)
        if not host:
            raise ValueError("Proxmox host not found for server")

        node = server.proxmox_node or host.node
        if not node:
            raise ValueError("Proxmox node not available for server")

        new_vcpu = (server.vcpu or 0) + upgrade.add_vcpu
        new_memory = (server.memory_mb or 0) + upgrade.add_memory_mb
        new_disk = (server.disk_gb or 0) + upgrade.add_disk_gb

        disk_volume = (
            f"{server.disk_storage or 'local-lvm'}:{int(new_disk)}" if new_disk else None
        )

        self.proxmox_client.update_resources(
            server.external_id,
            host=host,
            node=node,
            cores=new_vcpu,
            memory_mb=new_memory,
            disk_volume=disk_volume,
        )

        if upgrade.add_disk_gb:
            self.proxmox_client.resize_disk(
                server.external_id,
                host=host,
                node=node,
                add_disk_gb=upgrade.add_disk_gb,
            )

        server.vcpu = new_vcpu
        server.memory_mb = new_memory
        server.disk_gb = new_disk
        self.server_repo.update(server)
        return server
