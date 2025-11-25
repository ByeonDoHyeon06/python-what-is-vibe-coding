from collections.abc import Iterable
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.models.server import Server, ServerStatus
from app.infrastructure.storage.sqlite import SQLiteDataStore


class ServerRepository:
    """SQLite persistence for server entities."""

    def __init__(self, db: SQLiteDataStore):
        self.db = db

    def add(self, server: Server) -> None:
        self.db.execute(
            """
            INSERT INTO servers (id, owner_id, plan, location, proxmox_host_id, proxmox_node, vcpu, memory_mb, disk_gb, status, created_at, expire_in, external_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                owner_id=excluded.owner_id,
                plan=excluded.plan,
                location=excluded.location,
                proxmox_host_id=excluded.proxmox_host_id,
                proxmox_node=excluded.proxmox_node,
                vcpu=excluded.vcpu,
                memory_mb=excluded.memory_mb,
                disk_gb=excluded.disk_gb,
                status=excluded.status,
                expire_in=excluded.expire_in,
                external_id=excluded.external_id
            """,
            (
                str(server.id),
                str(server.owner_id),
                server.plan,
                server.location,
                server.proxmox_host_id,
                server.proxmox_node,
                server.vcpu,
                server.memory_mb,
                server.disk_gb,
                server.status.value,
                server.created_at.isoformat(),
                server.expire_in,
                server.external_id,
            ),
        )

    def update(self, server: Server) -> None:
        self.add(server)

    def get(self, server_id: UUID) -> Optional[Server]:
        row = self.db.fetch_one("SELECT * FROM servers WHERE id = ?", (str(server_id),))
        return self._row_to_server(row) if row else None

    def list_for_user(self, user_id: UUID) -> Iterable[Server]:
        rows = self.db.fetch_all("SELECT * FROM servers WHERE owner_id = ?", (str(user_id),))
        return [self._row_to_server(row) for row in rows]

    @staticmethod
    def _row_to_server(row) -> Server:
        return Server(
            id=UUID(row["id"]),
            owner_id=UUID(row["owner_id"]),
            plan=row["plan"],
            location=row["location"],
            proxmox_host_id=row["proxmox_host_id"],
            proxmox_node=row["proxmox_node"],
            vcpu=row["vcpu"],
            memory_mb=row["memory_mb"],
            disk_gb=row["disk_gb"],
            status=ServerStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            expire_in=row["expire_in"],
            external_id=row["external_id"],
        )
