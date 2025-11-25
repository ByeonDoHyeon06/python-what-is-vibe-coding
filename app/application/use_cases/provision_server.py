from uuid import UUID

from app.domain.models.server import Server
from app.domain.services.provisioning_policy import ProvisioningPolicy
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.infrastructure.repositories.server_repository import ServerRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.application.services.server_orchestrator import ServerProvisionOrchestrator


class ProvisionServer:
    """Entry point to kick off provisioning for a user purchase."""

    def __init__(
        self,
        server_repo: ServerRepository,
        user_repo: UserRepository,
        plan_repo: PlanRepository,
        policy: ProvisioningPolicy,
        orchestrator: ServerProvisionOrchestrator,
    ):
        self.server_repo = server_repo
        self.user_repo = user_repo
        self.plan_repo = plan_repo
        self.policy = policy
        self.orchestrator = orchestrator

    def execute(self, user_id: UUID, plan: str, location: str) -> Server:
        user = self.user_repo.get(user_id)
        if not user:
            raise ValueError("User not found")

        plan_entity = self.plan_repo.get(plan)
        if not plan_entity:
            raise ValueError("Plan not found")

        server = Server(
            owner_id=user_id,
            plan=plan_entity.name,
            location=location,
            vcpu=plan_entity.vcpu,
            memory_gb=plan_entity.memory_gb,
            disk_gb=plan_entity.disk_gb,
            node=plan_entity.default_node,
            storage_pool=plan_entity.default_storage_pool,
        )
        self.policy.validate(server)
        self.server_repo.add(server)
        self.orchestrator.provision(server, user)
        return server
