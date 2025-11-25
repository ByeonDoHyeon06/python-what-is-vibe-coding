from typing import Iterable, Optional

from app.domain.models.upgrade import UpgradeSpec
from app.infrastructure.storage.sqlite import SQLiteDataStore


class UpgradeRepository:
    """SQLite-backed catalog of upgrade bundles."""

    def __init__(self, db: SQLiteDataStore):
        self.db = db

    def add(self, upgrade: UpgradeSpec) -> None:
        self.db.execute(
            """
            INSERT INTO upgrades (name, add_vcpu, add_memory_mb, add_disk_gb, price, description)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                add_vcpu=excluded.add_vcpu,
                add_memory_mb=excluded.add_memory_mb,
                add_disk_gb=excluded.add_disk_gb,
                price=excluded.price,
                description=excluded.description
            """,
            (
                upgrade.name,
                upgrade.add_vcpu,
                upgrade.add_memory_mb,
                upgrade.add_disk_gb,
                upgrade.price,
                upgrade.description,
            ),
        )

    def get(self, name: str) -> Optional[UpgradeSpec]:
        row = self.db.fetch_one("SELECT * FROM upgrades WHERE name = ?", (name,))
        return self._row_to_upgrade(row) if row else None

    def list(self) -> Iterable[UpgradeSpec]:
        rows = self.db.fetch_all("SELECT * FROM upgrades")
        return [self._row_to_upgrade(row) for row in rows]

    @staticmethod
    def _row_to_upgrade(row) -> UpgradeSpec:
        return UpgradeSpec(
            name=row["name"],
            add_vcpu=row["add_vcpu"],
            add_memory_mb=row["add_memory_mb"],
            add_disk_gb=row["add_disk_gb"],
            price=row["price"],
            description=row["description"],
        )
