from uuid import UUID

from app.domain.models.server import Server
from app.domain.services.provisioning_policy import ProvisioningPolicy
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.infrastructure.repositories.server_repository import ServerRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.application.services.server_orchestrator import ServerProvisionOrchestrator


class ProvisionServer:
    """Entry point to kick off provisioning for a user purchase."""

    def __init__(
        self,
        server_repo: ServerRepository,
        user_repo: UserRepository,
        proxmox_hosts: ProxmoxHostRepository,
        policy: ProvisioningPolicy,
        orchestrator: ServerProvisionOrchestrator,
    ):
        self.server_repo = server_repo
        self.user_repo = user_repo
        self.proxmox_hosts = proxmox_hosts
        self.policy = policy
        self.orchestrator = orchestrator

    def execute(self, user_id: UUID, plan: str, location: str) -> Server:
        user = self.user_repo.get(user_id)
        if not user:
            raise ValueError("User not found")

        plan_spec = self.policy.resolve_plan(plan)
        host = self.policy.resolve_host(location, plan_spec)

        server = Server(
            owner_id=user_id,
            plan=plan_spec.name,
            location=location,
            proxmox_host_id=plan_spec.proxmox_host_id or host.id,
            proxmox_node=plan_spec.proxmox_node or host.node,
            vcpu=plan_spec.vcpu,
            memory_mb=plan_spec.memory_mb,
            disk_gb=plan_spec.disk_gb,
        )
        self.server_repo.add(server)
        self.orchestrator.provision(server, user, plan_spec, host)
        return server
