from typing import Iterable

from app.domain.models.server import Server


class ProvisioningPolicy:
    """Domain rules for validating whether a server can be provisioned."""

    def __init__(self, allowed_locations: Iterable[str], allowed_plans: Iterable[str]):
        self.allowed_locations = set(allowed_locations)
        self.allowed_plans = set(allowed_plans)

    def validate(self, server: Server) -> None:
        if server.location not in self.allowed_locations:
            raise ValueError(f"Unsupported location: {server.location}")
        if server.plan not in self.allowed_plans:
            raise ValueError(f"Unsupported plan: {server.plan}")
