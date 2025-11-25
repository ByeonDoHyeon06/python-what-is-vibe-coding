from uuid import UUID

from app.domain.models.server import Server
from app.infrastructure.repositories.server_repository import ServerRepository


class ExtendServerExpiry:
    """Handles extending a server's lifetime by increasing expire_in_days."""

    def __init__(self, server_repo: ServerRepository):
        self.server_repo = server_repo

    def extend(self, server_id: UUID, additional_days: int) -> Server:
        if additional_days <= 0:
            raise ValueError("additional_days must be positive")

        server = self.server_repo.get(server_id)
        if not server:
            raise ValueError("Server not found")

        server.expire_in_days = (server.expire_in_days or 0) + additional_days
        self.server_repo.update(server)
        return server
