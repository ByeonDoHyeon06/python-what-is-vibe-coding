from datetime import datetime
from typing import Iterable

from app.domain.models.server import Server, ServerStatus
from app.infrastructure.clients.proxmox import ProxmoxClient
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.infrastructure.repositories.server_repository import ServerRepository


class StopExpiredServers:
    """Stops servers whose expiration has passed."""

    def __init__(
        self,
        server_repo: ServerRepository,
        proxmox_hosts: ProxmoxHostRepository,
        proxmox_client: ProxmoxClient,
    ):
        self.server_repo = server_repo
        self.proxmox_hosts = proxmox_hosts
        self.proxmox_client = proxmox_client

    def stop_expired(self, now: datetime | None = None) -> Iterable[Server]:
        now = now or datetime.utcnow()
        expired = self.server_repo.list_expired(now)
        updated: list[Server] = []

        for server in expired:
            updated.append(self._stop_server(server))

        return updated

    def _stop_server(self, server: Server) -> Server:
        try:
            if not server.proxmox_host_id or not server.external_id:
                server.status = ServerStatus.STOPPED
                self.server_repo.update(server)
                return server

            host = self.proxmox_hosts.get(server.proxmox_host_id)
            node = server.proxmox_node or (host.node if host else None)
            if not host or not node:
                server.status = ServerStatus.FAILED
                self.server_repo.update(server)
                return server

            self.proxmox_client.stop_server(server.external_id, host=host, node=node)
            server.status = ServerStatus.STOPPED
            self.server_repo.update(server)
            return server
        except Exception:
            server.status = ServerStatus.FAILED
            self.server_repo.update(server)
            return server
