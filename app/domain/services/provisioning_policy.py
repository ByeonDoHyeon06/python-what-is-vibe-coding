from typing import Iterable

from app.domain.models.server import Server
from app.infrastructure.repositories.plan_repository import PlanRepository


class ProvisioningPolicy:
    """Domain rules for validating whether a server can be provisioned."""

    def __init__(self, allowed_locations: Iterable[str], plan_repo: PlanRepository):
        self.allowed_locations = set(allowed_locations)
        self.plan_repo = plan_repo

    def validate(self, server: Server) -> None:
        if server.location not in self.allowed_locations:
            raise ValueError(f"Unsupported location: {server.location}")

        if not self.plan_repo.get(server.plan):
            raise ValueError(f"Unsupported plan: {server.plan}")
