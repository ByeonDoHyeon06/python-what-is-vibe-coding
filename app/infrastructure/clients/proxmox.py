from app.domain.models.server import Server
from app.infrastructure.config.settings import settings


class ProxmoxClient:
    """Thin wrapper around Proxmox HTTP API (see https://pve.proxmox.com/pve-docs/api-viewer/)."""

    def __init__(self):
        self.base_url = settings.proxmox_host
        self.token_id = settings.proxmox_token_id
        self.token_secret = settings.proxmox_token_secret

    def provision_server(self, server: Server) -> str:
        """Provision a server and return the external identifier.

        In production this would call the Proxmox cluster API to create a VM or LXC.
        """

        payload = server.proxmox_params()
        payload.update({"plan": server.plan})

        # Placeholder that simulates the call; integrate python-proxmoxer or requests here.
        return f"vm-{server.id}"  # would use payload in a real call

    def destroy_server(self, external_id: str) -> None:
        """Rollback helper to clean up failed provisioning attempts."""

        # Placeholder: perform DELETE on /nodes/<node>/qemu/<vmid>
        return None
