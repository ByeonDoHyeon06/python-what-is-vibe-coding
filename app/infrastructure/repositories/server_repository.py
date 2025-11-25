from collections.abc import Iterable
from typing import Dict, Optional
from uuid import UUID

from app.domain.models.server import Server


class ServerRepository:
    """Simple in-memory persistence for server entities."""

    def __init__(self):
        self._servers: Dict[UUID, Server] = {}

    def add(self, server: Server) -> None:
        self._servers[server.id] = server

    def update(self, server: Server) -> None:
        self._servers[server.id] = server

    def get(self, server_id: UUID) -> Optional[Server]:
        return self._servers.get(server_id)

    def list_for_user(self, user_id: UUID) -> Iterable[Server]:
        return [srv for srv in self._servers.values() if srv.owner_id == user_id]
