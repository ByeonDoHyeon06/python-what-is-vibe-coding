from typing import Iterable, Optional

from app.domain.models.proxmox_host import ProxmoxHostConfig
from app.infrastructure.storage.sqlite import SQLiteDataStore


class ProxmoxHostRepository:
    """SQLite-backed metadata store for Proxmox hosts and nodes."""

    def __init__(self, db: SQLiteDataStore):
        self.db = db

    def add(self, host: ProxmoxHostConfig) -> None:
        self.db.execute(
            """
            INSERT INTO proxmox_hosts (id, api_url, username, password, realm, node, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                api_url=excluded.api_url,
                username=excluded.username,
                password=excluded.password,
                realm=excluded.realm,
                node=excluded.node,
                location=excluded.location
            """,
            (
                host.id,
                host.api_url,
                host.username,
                host.password,
                host.realm,
                host.node,
                host.location,
            ),
        )

    def get(self, host_id: str) -> Optional[ProxmoxHostConfig]:
        row = self.db.fetch_one("SELECT * FROM proxmox_hosts WHERE id = ?", (host_id,))
        return self._row_to_host(row) if row else None

    def list(self) -> Iterable[ProxmoxHostConfig]:
        rows = self.db.fetch_all("SELECT * FROM proxmox_hosts")
        return [self._row_to_host(row) for row in rows]

    def first_for_location(self, location: str) -> Optional[ProxmoxHostConfig]:
        row = self.db.fetch_one("SELECT * FROM proxmox_hosts WHERE location = ?", (location,))
        return self._row_to_host(row) if row else None

    @staticmethod
    def _row_to_host(row) -> ProxmoxHostConfig:
        return ProxmoxHostConfig(
            id=row["id"],
            api_url=row["api_url"],
            username=row["username"],
            password=row["password"],
            realm=row["realm"],
            node=row["node"],
            location=row["location"],
        )
