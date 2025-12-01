from collections.abc import Iterable
from typing import Optional

from sqlalchemy import select

from app.domain.models.upgrade import UpgradeSpec
from app.infrastructure.storage.sqlite import SQLAlchemyDataStore, UpgradeModel


class UpgradeRepository:
    """SQLAlchemy-backed repository for resource upgrade bundles."""

    def __init__(self, db: SQLAlchemyDataStore):
        self.db = db

    def add(self, upgrade: UpgradeSpec) -> None:
        with self.db.session() as session:
            existing = session.get(UpgradeModel, upgrade.name)
            if existing:
                existing.add_vcpu = upgrade.add_vcpu
                existing.add_memory_mb = upgrade.add_memory_mb
                existing.add_disk_gb = upgrade.add_disk_gb
                existing.price = upgrade.price
                existing.description = upgrade.description
            else:
                session.add(
                    UpgradeModel(
                        name=upgrade.name,
                        add_vcpu=upgrade.add_vcpu,
                        add_memory_mb=upgrade.add_memory_mb,
                        add_disk_gb=upgrade.add_disk_gb,
                        price=upgrade.price,
                        description=upgrade.description,
                    )
                )
            session.commit()

    def get(self, name: str) -> Optional[UpgradeSpec]:
        with self.db.session() as session:
            row = session.get(UpgradeModel, name)
            return self._model_to_upgrade(row) if row else None

    def list(self) -> Iterable[UpgradeSpec]:
        with self.db.session() as session:
            rows = session.scalars(select(UpgradeModel)).all()
            return [self._model_to_upgrade(row) for row in rows]

    def delete(self, name: str) -> None:
        with self.db.session() as session:
            row = session.get(UpgradeModel, name)
            if row:
                session.delete(row)
                session.commit()

    @staticmethod
    def _model_to_upgrade(row: UpgradeModel) -> UpgradeSpec:
        return UpgradeSpec(
            name=row.name,
            add_vcpu=row.add_vcpu,
            add_memory_mb=row.add_memory_mb,
            add_disk_gb=row.add_disk_gb,
            price=row.price,
            description=row.description,
        )
