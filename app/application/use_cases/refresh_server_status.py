from uuid import UUID

from app.domain.models.server import Server, ServerStatus
from app.infrastructure.clients.proxmox import ProxmoxClient
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.infrastructure.repositories.server_repository import ServerRepository


class RefreshServerStatus:
    """Sync server status from Proxmox when servers are retrieved."""

    def __init__(
        self,
        server_repo: ServerRepository,
        proxmox_hosts: ProxmoxHostRepository,
        proxmox_client: ProxmoxClient,
    ):
        self.server_repo = server_repo
        self.proxmox_hosts = proxmox_hosts
        self.proxmox_client = proxmox_client

    def refresh_by_id(self, server_id: UUID) -> Server | None:
        server = self.server_repo.get(server_id)
        if not server:
            return None
        return self._refresh(server)

    def refresh_for_user(self, user_id: UUID) -> list[Server]:
        servers = list(self.server_repo.list_for_user(user_id))
        return [self._refresh(server) for server in servers]

    def _refresh(self, server: Server) -> Server:
        if not server.external_id or not server.proxmox_host_id:
            return server

        host = self.proxmox_hosts.get(server.proxmox_host_id)
        if not host:
            return server

        node = server.proxmox_node or host.node
        if not node:
            return server

        try:
            proxmox_status = self.proxmox_client.get_server_status(
                external_id=server.external_id, host=host, node=node
            )
        except Exception:  # noqa: BLE001
            return server

        mapped = self._map_proxmox_status(proxmox_status)
        if mapped and mapped != server.status:
            server.status = mapped
            self.server_repo.update(server)
        return server

    @staticmethod
    def _map_proxmox_status(status: str | None) -> ServerStatus | None:
        if not status:
            return None

        normalized = status.lower()
        if normalized in {"running", "online", "started"}:
            return ServerStatus.ACTIVE
        if normalized in {"stopped", "shutdown", "off"}:
            return ServerStatus.STOPPED
        if normalized in {"paused", "suspended", "hibernated"}:
            return ServerStatus.STOPPED
        if normalized in {"booting", "starting", "init"}:
            return ServerStatus.PROVISIONING
        return ServerStatus.FAILED if normalized in {"failed", "error"} else None
