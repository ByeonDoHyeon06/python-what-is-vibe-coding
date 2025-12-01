import secrets
from uuid import UUID

from app.infrastructure.clients.proxmox import ProxmoxClient
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.infrastructure.repositories.server_repository import ServerRepository
from app.domain.models.server import Server


class ResetServerPassword:
    """Regenerate a server login password and push it to Proxmox."""

    def __init__(
        self,
        server_repo: ServerRepository,
        proxmox_hosts: ProxmoxHostRepository,
        proxmox_client: ProxmoxClient,
    ):
        self.server_repo = server_repo
        self.proxmox_hosts = proxmox_hosts
        self.proxmox_client = proxmox_client

    def reset(self, server_id: UUID, user_id: UUID | None, allow_admin: bool = False) -> tuple[Server, str]:
        server = self.server_repo.get(server_id)
        if not server:
            raise ValueError("Server not found")
        if not allow_admin and server.owner_id != user_id:
            raise ValueError("User is not allowed to modify this server")
        if not server.external_id or not server.proxmox_host_id:
            raise ValueError("Server has no Proxmox mapping")

        host = self.proxmox_hosts.get(server.proxmox_host_id)
        if not host:
            raise ValueError("Proxmox host not found for server")

        node = server.proxmox_node or host.node
        if not node:
            raise ValueError("Proxmox node not available for server")

        new_password = self._generate_password()
        self.proxmox_client.set_admin_password(
            external_id=server.external_id,
            host=host,
            node=node,
            password=new_password,
        )

        server.vm_password = new_password
        return server, new_password

    @staticmethod
    def _generate_password(length: int = 16) -> str:
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#%*"
        return "".join(secrets.choice(alphabet) for _ in range(length))
