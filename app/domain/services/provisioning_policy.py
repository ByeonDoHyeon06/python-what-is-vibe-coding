from app.domain.models.plan import PlanSpec
from app.domain.models.proxmox_host import ProxmoxHostConfig
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository


class ProvisioningPolicy:
    """Domain rules for validating whether a server can be provisioned."""

    def __init__(self, plans: PlanRepository, proxmox_hosts: ProxmoxHostRepository):
        self.plans = plans
        self.proxmox_hosts = proxmox_hosts

    def resolve_plan(self, plan_name: str) -> PlanSpec:
        plan = self.plans.get(plan_name)
        if not plan:
            raise ValueError(f"Unsupported plan: {plan_name}")
        return plan

    def resolve_host(self, location: str, plan: PlanSpec) -> ProxmoxHostConfig:
        if plan.location != location:
            raise ValueError(
                f"Plan '{plan.name}' is only available in {plan.location}, requested {location}"
            )

        if plan.proxmox_host_id:
            host = self.proxmox_hosts.get(plan.proxmox_host_id)
            if not host:
                raise ValueError(f"No Proxmox host configured with id '{plan.proxmox_host_id}'")
            return host

        host = self.proxmox_hosts.first_for_location(location)
        if not host:
            raise ValueError(f"No Proxmox host available for location {location}")
        return host
