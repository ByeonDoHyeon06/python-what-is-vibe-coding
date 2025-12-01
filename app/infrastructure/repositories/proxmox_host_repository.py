from typing import Iterable, Optional

from sqlalchemy import select

from app.domain.models.proxmox_host import ProxmoxHostConfig
from app.infrastructure.storage.sqlite import ProxmoxHostModel, SQLAlchemyDataStore


class ProxmoxHostRepository:
    """SQLAlchemy persistence for Proxmox host definitions."""

    def __init__(self, db: SQLAlchemyDataStore):
        self.db = db

    def add(self, host: ProxmoxHostConfig) -> None:
        with self.db.session() as session:
            existing = session.get(ProxmoxHostModel, host.id)
            if existing:
                existing.api_url = host.api_url
                existing.username = host.username
                existing.password = host.password
                existing.realm = host.realm
                existing.node = host.node
                existing.location = host.location
            else:
                session.add(
                    ProxmoxHostModel(
                        id=host.id,
                        api_url=host.api_url,
                        username=host.username,
                        password=host.password,
                        realm=host.realm,
                        node=host.node,
                        location=host.location,
                    )
                )
            session.commit()

    def get(self, host_id: str) -> Optional[ProxmoxHostConfig]:
        with self.db.session() as session:
            row = session.get(ProxmoxHostModel, host_id)
            return self._model_to_host(row) if row else None

    def list(self) -> Iterable[ProxmoxHostConfig]:
        with self.db.session() as session:
            rows = session.scalars(select(ProxmoxHostModel)).all()
            return [self._model_to_host(row) for row in rows]

    def delete(self, host_id: str) -> None:
        with self.db.session() as session:
            row = session.get(ProxmoxHostModel, host_id)
            if row:
                session.delete(row)
                session.commit()

    @staticmethod
    def _model_to_host(row: ProxmoxHostModel) -> ProxmoxHostConfig:
        return ProxmoxHostConfig(
            id=row.id,
            api_url=row.api_url,
            username=row.username,
            password=row.password,
            realm=row.realm,
            node=row.node,
            location=row.location,
        )
