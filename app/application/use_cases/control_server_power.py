from uuid import UUID

from app.domain.models.server import Server, ServerStatus
from app.infrastructure.clients.proxmox import ProxmoxClient
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.infrastructure.repositories.server_repository import ServerRepository


class ControlServerPower:
    """Allows operators to start/stop VMs using the backend-issued server ID."""

    def __init__(
        self,
        server_repo: ServerRepository,
        proxmox_hosts: ProxmoxHostRepository,
        proxmox_client: ProxmoxClient,
    ):
        self.server_repo = server_repo
        self.proxmox_hosts = proxmox_hosts
        self.proxmox_client = proxmox_client

    def start(self, server_id: UUID, user_id: UUID | None = None) -> Server:
        server, host, node = self._resolve_server(server_id, user_id=user_id)
        if not server.external_id:
            raise ValueError("Server has no Proxmox external_id; cannot start")

        self.proxmox_client.start_server(server.external_id, host=host, node=node)
        server.status = ServerStatus.ACTIVE
        self.server_repo.update(server)
        return server

    def stop(self, server_id: UUID, user_id: UUID | None = None) -> Server:
        server, host, node = self._resolve_server(server_id, user_id=user_id)
        if not server.external_id:
            raise ValueError("Server has no Proxmox external_id; cannot stop")

        self.proxmox_client.stop_server(server.external_id, host=host, node=node)
        server.status = ServerStatus.STOPPED
        self.server_repo.update(server)
        return server

    def reboot(self, server_id: UUID, user_id: UUID | None = None) -> Server:
        server, host, node = self._resolve_server(server_id, user_id=user_id)
        if not server.external_id:
            raise ValueError("Server has no Proxmox external_id; cannot reboot")

        self.proxmox_client.reboot_server(server.external_id, host=host, node=node)
        server.status = ServerStatus.ACTIVE
        self.server_repo.update(server)
        return server

    def reset(self, server_id: UUID, user_id: UUID | None = None) -> Server:
        server, host, node = self._resolve_server(server_id, user_id=user_id)
        if not server.external_id:
            raise ValueError("Server has no Proxmox external_id; cannot reset")

        self.proxmox_client.reset_server(server.external_id, host=host, node=node)
        server.status = ServerStatus.ACTIVE
        self.server_repo.update(server)
        return server

    def shutdown(self, server_id: UUID, user_id: UUID | None = None) -> Server:
        server, host, node = self._resolve_server(server_id, user_id=user_id)
        if not server.external_id:
            raise ValueError("Server has no Proxmox external_id; cannot shutdown")

        self.proxmox_client.shutdown_server(server.external_id, host=host, node=node)
        server.status = ServerStatus.STOPPED
        self.server_repo.update(server)
        return server

    def suspend(self, server_id: UUID, user_id: UUID | None = None) -> Server:
        server, host, node = self._resolve_server(server_id, user_id=user_id)
        if not server.external_id:
            raise ValueError("Server has no Proxmox external_id; cannot suspend")

        self.proxmox_client.suspend_server(server.external_id, host=host, node=node)
        server.status = ServerStatus.STOPPED
        self.server_repo.update(server)
        return server

    def resume(self, server_id: UUID, user_id: UUID | None = None) -> Server:
        server, host, node = self._resolve_server(server_id, user_id=user_id)
        if not server.external_id:
            raise ValueError("Server has no Proxmox external_id; cannot resume")

        self.proxmox_client.resume_server(server.external_id, host=host, node=node)
        server.status = ServerStatus.ACTIVE
        self.server_repo.update(server)
        return server

    def _resolve_server(self, server_id: UUID, user_id: UUID | None = None) -> tuple[Server, "ProxmoxHostConfig", str]:
        if user_id is None:
            raise ValueError("User id is required for power controls")

        server = self.server_repo.get(server_id)
        if not server:
            raise ValueError("Server not found")

        if user_id and server.owner_id != user_id:
            raise ValueError("User is not allowed to control this server")

        if not server.proxmox_host_id:
            raise ValueError("Server is missing Proxmox host mapping")

        host = self.proxmox_hosts.get(server.proxmox_host_id)
        if not host:
            raise ValueError("Proxmox host not found for server")

        node = server.proxmox_node or host.node
        if not node:
            raise ValueError("Proxmox node not available for server")

        return server, host, node
