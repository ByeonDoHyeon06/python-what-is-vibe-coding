from typing import Protocol, Set

from app.domain.models.server import Server


class ProvisioningConfig(Protocol):
    def get_allowed_locations(self) -> Set[str]:
        """Retrieve the set of locations allowed for provisioning."""

    def get_allowed_plans(self) -> Set[str]:
        """Retrieve the set of plans allowed for provisioning."""


class ProvisioningPolicy:
    """Domain rules for validating whether a server can be provisioned."""

    def __init__(self, config_repo: ProvisioningConfig):
        self.config_repo = config_repo

    def validate(self, server: Server) -> None:
        allowed_locations = self.config_repo.get_allowed_locations()
        allowed_plans = self.config_repo.get_allowed_plans()

        if server.location not in allowed_locations:
            raise ValueError(f"Unsupported location: {server.location}")
        if server.plan not in allowed_plans:
            raise ValueError(f"Unsupported plan: {server.plan}")
