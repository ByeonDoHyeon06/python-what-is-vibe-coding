from typing import Iterable, Optional

from app.domain.models.plan import PlanSpec
from app.infrastructure.storage.sqlite import SQLiteDataStore


class PlanRepository:
    """SQLite-backed store for admin-defined hosting plans."""

    def __init__(self, db: SQLiteDataStore):
        self.db = db

    def add(self, plan: PlanSpec) -> None:
        self.db.execute(
            """
            INSERT INTO plans (name, vcpu, memory_mb, disk_gb, location, proxmox_host_id, proxmox_node, description, template_vmid, disk_storage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                vcpu=excluded.vcpu,
                memory_mb=excluded.memory_mb,
                disk_gb=excluded.disk_gb,
                location=excluded.location,
                proxmox_host_id=excluded.proxmox_host_id,
                proxmox_node=excluded.proxmox_node,
                description=excluded.description,
                template_vmid=excluded.template_vmid,
                disk_storage=excluded.disk_storage
            """,
            (
                plan.name,
                plan.vcpu,
                plan.memory_mb,
                plan.disk_gb,
                plan.location,
                plan.proxmox_host_id,
                plan.proxmox_node,
                plan.description,
                plan.template_vmid,
                plan.disk_storage,
            ),
        )

    def get(self, name: str) -> Optional[PlanSpec]:
        row = self.db.fetch_one("SELECT * FROM plans WHERE name = ?", (name,))
        return self._row_to_plan(row) if row else None

    def list(self) -> Iterable[PlanSpec]:
        rows = self.db.fetch_all("SELECT * FROM plans")
        return [self._row_to_plan(row) for row in rows]

    @staticmethod
    def _row_to_plan(row) -> PlanSpec:
        return PlanSpec(
            name=row["name"],
            vcpu=row["vcpu"],
            memory_mb=row["memory_mb"],
            disk_gb=row["disk_gb"],
            location=row["location"],
            proxmox_host_id=row["proxmox_host_id"],
            proxmox_node=row["proxmox_node"],
            description=row["description"],
            template_vmid=row["template_vmid"],
            disk_storage=row["disk_storage"],
        )
