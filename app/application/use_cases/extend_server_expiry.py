from uuid import UUID

from uuid import UUID

from app.domain.models.server import Server
from app.infrastructure.repositories.server_repository import ServerRepository


class ExtendServerExpiry:
    """Handles extending a server's lifetime by increasing expire_in_days."""

    def __init__(self, server_repo: ServerRepository):
        self.server_repo = server_repo

    def extend(self, server_id: UUID, additional_days: int, user_id: UUID | None = None) -> Server:
        if additional_days <= 0:
            raise ValueError("additional_days must be positive")

        if user_id is None:
            raise ValueError("User id is required to extend server expiry")

        server = self.server_repo.get(server_id)
        if not server:
            raise ValueError("Server not found")

        if user_id and server.owner_id != user_id:
            raise ValueError("User is not allowed to extend this server")

        server.expire_in_days = (server.expire_in_days or 0) + additional_days
        self.server_repo.update(server)
        return server
