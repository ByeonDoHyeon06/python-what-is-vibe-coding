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

    def refresh_owned(self, server_id: UUID, user_id: UUID) -> Server | None:
        server = self.server_repo.get(server_id)
        if not server or server.owner_id != user_id:
            return None
        return self._refresh(server)

    def refresh_for_user(self, user_id: UUID) -> list[Server]:
        servers = list(self.server_repo.list_for_user(user_id))
        return [self._refresh(server) for server in servers]

    def refresh_entity(self, server: Server) -> Server:
        return self._refresh(server)

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
            proxmox_config = self.proxmox_client.get_server_config(
                external_id=server.external_id, host=host, node=node
            )
        except Exception:  # noqa: BLE001
            return server

        mapped = self._map_proxmox_status(proxmox_status)
        updated = False
        if mapped and mapped != server.status:
            server.status = mapped
            updated = True

        if proxmox_config:
            updated = self._sync_config(server, proxmox_config) or updated

        try:
            primary_ip = self.proxmox_client.get_primary_ip(
                external_id=server.external_id, host=host, node=node
            )
            if not primary_ip:
                primary_ip = self._parse_ip_from_config(proxmox_config)
            if primary_ip and primary_ip != server.primary_ip:
                server.primary_ip = primary_ip
                updated = True
        except Exception:  # noqa: BLE001
            pass

        if updated:
            self.server_repo.update(server)
            server.applied_upgrades = self.server_repo.list_upgrades_for_server(server.id)
        return server

    @staticmethod
    def _sync_config(server: Server, config: dict) -> bool:
        """Reconcile resource config differences back into persistence."""

        changed = False
        cores = config.get("cores") or config.get("sockets")
        memory = config.get("memory") or config.get("mem")
        disk = config.get("virtio0")

        if isinstance(cores, int) and cores != server.vcpu:
            server.vcpu = cores
            changed = True
        if isinstance(memory, int) and memory != server.memory_mb:
            server.memory_mb = memory
            changed = True

        if isinstance(disk, str):
            storage, size = RefreshServerStatus._parse_disk(disk)
            if storage and storage != server.disk_storage:
                server.disk_storage = storage
                changed = True
            if size is not None and size != server.disk_gb:
                server.disk_gb = size
                changed = True
        return changed

    @staticmethod
    def _parse_disk(disk: str) -> tuple[str | None, int | None]:
        parts = disk.split(",")
        storage_part = parts[0]
        storage = None
        size = None
        if ":" in storage_part:
            storage = storage_part.split(":", 1)[0]
            remainder = storage_part.split(":", 1)[1]
            if remainder.isdigit():
                size = int(remainder)
        for part in parts[1:]:
            if part.strip().startswith("size="):
                val = part.split("=", 1)[1]
                if val.lower().endswith("g"):
                    val = val[:-1]
                if val.isdigit():
                    size = int(val)
        return storage, size

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

    @staticmethod
    def _parse_ip_from_config(config: dict | None) -> str | None:
        if not config:
            return None
        ipconfig = config.get("ipconfig0")
        if isinstance(ipconfig, str):
            parts = ipconfig.split(",")
            for part in parts:
                if part.strip().startswith("ip="):
                    ip_val = part.split("=", 1)[1]
                    if "/" in ip_val:
                        return ip_val.split("/", 1)[0]
                    return ip_val
        return None
