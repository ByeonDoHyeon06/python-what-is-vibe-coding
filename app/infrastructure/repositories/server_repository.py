from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select, String

from app.domain.models.server import Server, ServerStatus
from app.domain.models.upgrade import AppliedUpgrade
from app.infrastructure.storage.sqlite import (
    SQLAlchemyDataStore,
    ServerModel,
    ServerUpgradeModel,
)


class ServerRepository:
    """SQLAlchemy persistence for server entities."""

    def __init__(self, db: SQLAlchemyDataStore):
        self.db = db

    def add(self, server: Server) -> None:
        with self.db.session() as session:
            existing = session.get(ServerModel, str(server.id))
            if existing:
                self._apply_server(existing, server)
            else:
                model = ServerModel()
                self._apply_server(model, server)
                session.add(model)
            session.commit()

    def update(self, server: Server) -> None:
        self.add(server)

    def get(self, server_id: UUID) -> Optional[Server]:
        with self.db.session() as session:
            model = session.get(ServerModel, str(server_id))
            if not model:
                return None
            server = self._model_to_server(model)
            server.applied_upgrades = self.list_upgrades_for_server(server.id)
            return server

    def list_for_user(self, user_id: UUID) -> Iterable[Server]:
        with self.db.session() as session:
            rows = session.scalars(select(ServerModel).where(ServerModel.owner_id == str(user_id))).all()
            servers = [self._model_to_server(row) for row in rows]
            for server in servers:
                server.applied_upgrades = self.list_upgrades_for_server(server.id)
            return servers

    def list_all(
        self,
        owner_id: UUID | None = None,
        status: ServerStatus | None = None,
        plan: str | None = None,
        location: str | None = None,
    ) -> Iterable[Server]:
        with self.db.session() as session:
            conditions = []
            if owner_id:
                conditions.append(ServerModel.owner_id == str(owner_id))
            if status:
                conditions.append(ServerModel.status == status.value)
            if plan:
                conditions.append(ServerModel.plan == plan)
            if location:
                conditions.append(ServerModel.location == location)

            stmt = select(ServerModel)
            if conditions:
                stmt = stmt.where(and_(*conditions))

            rows = session.scalars(stmt).all()
            servers = [self._model_to_server(row) for row in rows]
            for server in servers:
                server.applied_upgrades = self.list_upgrades_for_server(server.id)
            return servers

    def list_expired(self, now: datetime) -> Iterable[Server]:
        with self.db.session() as session:
            expiry_expr = func.datetime(ServerModel.created_at, "+" + func.cast(ServerModel.expire_in_days, String) + " days")
            rows = session.scalars(
                select(ServerModel).where(
                    ServerModel.expire_in_days.isnot(None),
                    expiry_expr <= now,
                )
            ).all()
            servers = [self._model_to_server(row) for row in rows]
            for server in servers:
                server.applied_upgrades = self.list_upgrades_for_server(server.id)
            return servers

    def list_expiring_within(self, now: datetime, days: int) -> Iterable[Server]:
        with self.db.session() as session:
            expiry_expr = func.datetime(ServerModel.created_at, "+" + func.cast(ServerModel.expire_in_days, String) + " days")
            upper = now + timedelta(days=days)
            rows = session.scalars(
                select(ServerModel).where(
                    ServerModel.expire_in_days.isnot(None),
                    expiry_expr > now,
                    expiry_expr <= upper,
                )
            ).all()
            return [self._model_to_server(row) for row in rows]

    def record_upgrade(self, server_id: UUID, upgrade_name: str, price: float | None) -> None:
        with self.db.session() as session:
            session.add(
                ServerUpgradeModel(
                    server_id=str(server_id), upgrade_name=upgrade_name, price=price, applied_at=datetime.utcnow()
                )
            )
            session.commit()

    def list_upgrades_for_server(self, server_id: UUID) -> list[AppliedUpgrade]:
        with self.db.session() as session:
            rows = session.scalars(
                select(ServerUpgradeModel)
                .where(ServerUpgradeModel.server_id == str(server_id))
                .order_by(ServerUpgradeModel.applied_at)
            ).all()
            return [
                AppliedUpgrade(
                    name=row.upgrade_name,
                    applied_at=row.applied_at
                    if isinstance(row.applied_at, datetime)
                    else datetime.fromisoformat(row.applied_at),
                    price=row.price,
                )
                for row in rows
            ]

    @staticmethod
    def _apply_server(model: ServerModel, server: Server) -> None:
        model.id = str(server.id)
        model.owner_id = str(server.owner_id)
        model.plan = server.plan
        model.location = server.location
        model.proxmox_host_id = server.proxmox_host_id
        model.proxmox_node = server.proxmox_node
        model.vcpu = server.vcpu
        model.memory_mb = server.memory_mb
        model.disk_gb = server.disk_gb
        model.disk_storage = server.disk_storage
        model.primary_ip = server.primary_ip
        model.expire_in_days = server.expire_in_days
        model.status = server.status.value
        model.created_at = server.created_at
        model.external_id = server.external_id
        model.last_notified_at = server.last_notified_at

    @staticmethod
    def _model_to_server(row: ServerModel) -> Server:
        server = Server(
            id=UUID(row.id),
            owner_id=UUID(row.owner_id),
            plan=row.plan,
            location=row.location,
            proxmox_host_id=row.proxmox_host_id,
            proxmox_node=row.proxmox_node,
            vcpu=row.vcpu,
            memory_mb=row.memory_mb,
            disk_gb=row.disk_gb,
            disk_storage=row.disk_storage,
            primary_ip=row.primary_ip,
            expire_in_days=row.expire_in_days,
            status=ServerStatus(row.status),
            created_at=row.created_at if isinstance(row.created_at, datetime) else datetime.fromisoformat(row.created_at),
            external_id=row.external_id,
            last_notified_at=row.last_notified_at
            if isinstance(row.last_notified_at, datetime)
            else datetime.fromisoformat(row.last_notified_at)
            if row.last_notified_at
            else None,
        )
        server.applied_upgrades = []
        return server
