from typing import Iterable, Optional

from sqlalchemy import select

from app.domain.models.plan import PlanSpec
from app.infrastructure.storage.sqlite import PlanModel, SQLAlchemyDataStore


class PlanRepository:
    """SQLAlchemy-backed store for admin-defined hosting plans."""

    def __init__(self, db: SQLAlchemyDataStore):
        self.db = db

    def add(self, plan: PlanSpec) -> None:
        with self.db.session() as session:
            existing = session.get(PlanModel, plan.name)
            if existing:
                existing.vcpu = plan.vcpu
                existing.memory_mb = plan.memory_mb
                existing.disk_gb = plan.disk_gb
                existing.location = plan.location
                existing.proxmox_host_id = plan.proxmox_host_id
                existing.proxmox_node = plan.proxmox_node
                existing.description = plan.description
                existing.template_vmid = plan.template_vmid
                existing.disk_storage = plan.disk_storage
                existing.clone_mode = plan.clone_mode
                existing.price = plan.price
                existing.default_expire_days = plan.default_expire_days
            else:
                session.add(
                    PlanModel(
                        name=plan.name,
                        vcpu=plan.vcpu,
                        memory_mb=plan.memory_mb,
                        disk_gb=plan.disk_gb,
                        location=plan.location,
                        proxmox_host_id=plan.proxmox_host_id,
                        proxmox_node=plan.proxmox_node,
                        description=plan.description,
                        template_vmid=plan.template_vmid,
                        disk_storage=plan.disk_storage,
                        clone_mode=plan.clone_mode,
                        price=plan.price,
                        default_expire_days=plan.default_expire_days,
                    )
                )
            session.commit()

    def get(self, name: str) -> Optional[PlanSpec]:
        with self.db.session() as session:
            row = session.get(PlanModel, name)
            return self._model_to_plan(row) if row else None

    def list(self) -> Iterable[PlanSpec]:
        with self.db.session() as session:
            rows = session.scalars(select(PlanModel)).all()
            return [self._model_to_plan(row) for row in rows]

    def delete(self, name: str) -> None:
        with self.db.session() as session:
            row = session.get(PlanModel, name)
            if row:
                session.delete(row)
                session.commit()

    @staticmethod
    def _model_to_plan(row: PlanModel) -> PlanSpec:
        return PlanSpec(
            name=row.name,
            vcpu=row.vcpu,
            memory_mb=row.memory_mb,
            disk_gb=row.disk_gb,
            location=row.location,
            proxmox_host_id=row.proxmox_host_id,
            proxmox_node=row.proxmox_node,
            description=row.description,
            template_vmid=row.template_vmid,
            disk_storage=row.disk_storage,
            clone_mode=row.clone_mode,
            price=row.price,
            default_expire_days=row.default_expire_days,
        )
