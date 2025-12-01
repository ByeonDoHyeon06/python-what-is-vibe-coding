from uuid import UUID

from app.domain.models.server import ServerStatus
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

    def apply(
        self, server_id: UUID, upgrade_name: str, user_id: UUID | None, allow_admin: bool = False
    ) -> "Server":
        server = self.server_repo.get(server_id)
        if not server:
            raise ValueError("Server not found")

        if not allow_admin and server.owner_id != user_id:
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

        # upgrades are only allowed while the VM is stopped for safety
        current_status = server.status
        if server.external_id:
            try:
                proxmox_status = self.proxmox_client.get_server_status(
                    external_id=server.external_id, host=host, node=node
                )
                if proxmox_status:
                    current_status = self._map_status(proxmox_status) or current_status
                    server.status = current_status
            except Exception:  # noqa: BLE001
                # fall back to persisted status if Proxmox cannot be reached
                pass

        if current_status != ServerStatus.STOPPED:
            raise ValueError("Upgrade requires the server to be stopped")

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
        self.server_repo.record_upgrade(server.id, upgrade_name=upgrade.name, price=upgrade.price)
        server.applied_upgrades = self.server_repo.list_upgrades_for_server(server.id)
        return server

    @staticmethod
    def _map_status(status: str | None):
        if not status:
            return None
        normalized = status.lower()
        if normalized in {"running", "online", "started"}:
            return ServerStatus.ACTIVE
        if normalized in {"stopped", "shutdown", "off"}:
            return ServerStatus.STOPPED
        return None
