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
            INSERT INTO servers (id, owner_id, plan, location, proxmox_host_id, proxmox_node, vcpu, memory_mb, disk_gb, disk_storage, expire_in_days, status, created_at, external_id, last_notified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                owner_id=excluded.owner_id,
                plan=excluded.plan,
                location=excluded.location,
                proxmox_host_id=excluded.proxmox_host_id,
                proxmox_node=excluded.proxmox_node,
                vcpu=excluded.vcpu,
                memory_mb=excluded.memory_mb,
                disk_gb=excluded.disk_gb,
                disk_storage=excluded.disk_storage,
                expire_in_days=excluded.expire_in_days,
                status=excluded.status,
                external_id=excluded.external_id,
                last_notified_at=excluded.last_notified_at
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
                server.disk_storage,
                server.expire_in_days,
                server.status.value,
                server.created_at.isoformat(),
                server.external_id,
                server.last_notified_at.isoformat() if server.last_notified_at else None,
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

    def list_expired(self, now: datetime) -> Iterable[Server]:
        rows = self.db.fetch_all(
            """
            SELECT * FROM servers
            WHERE expire_in_days IS NOT NULL
              AND datetime(created_at, '+' || expire_in_days || ' days') <= ?
            """,
            (now.isoformat(),),
        )
        return [self._row_to_server(row) for row in rows]

    def list_expiring_within(self, now: datetime, days: int) -> Iterable[Server]:
        rows = self.db.fetch_all(
            """
            SELECT * FROM servers
            WHERE expire_in_days IS NOT NULL
              AND datetime(created_at, '+' || expire_in_days || ' days') > ?
              AND datetime(created_at, '+' || expire_in_days || ' days') <= datetime(?, '+' || ? || ' days')
            """,
            (now.isoformat(), now.isoformat(), days),
        )
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
            disk_storage=row["disk_storage"],
            expire_in_days=row["expire_in_days"],
            status=ServerStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            external_id=row["external_id"],
            last_notified_at=datetime.fromisoformat(row["last_notified_at"]) if row["last_notified_at"] else None,
        )
