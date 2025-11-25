from functools import lru_cache

from app.application.services.server_orchestrator import ServerProvisionOrchestrator
from app.application.use_cases.provision_server import ProvisionServer
from app.application.use_cases.register_user import RegisterUser
from app.domain.services.provisioning_policy import ProvisioningPolicy
from app.infrastructure.clients.proxmox import ProxmoxClient
from app.infrastructure.clients.solapi import SolapiClient
from app.infrastructure.repositories.config_repository import ProvisioningConfigRepository
from app.infrastructure.repositories.server_repository import ServerRepository
from app.infrastructure.repositories.user_repository import UserRepository


@lru_cache()
def get_user_repository() -> UserRepository:
    return UserRepository()


@lru_cache()
def get_server_repository() -> ServerRepository:
    return ServerRepository()


@lru_cache()
def get_config_repository() -> ProvisioningConfigRepository:
    return ProvisioningConfigRepository()


@lru_cache()
def get_provisioning_policy() -> ProvisioningPolicy:
    return ProvisioningPolicy(config_repo=get_config_repository())


@lru_cache()
def get_proxmox_client() -> ProxmoxClient:
    return ProxmoxClient()


@lru_cache()
def get_solapi_client() -> SolapiClient:
    return SolapiClient()


@lru_cache()
def get_server_orchestrator() -> ServerProvisionOrchestrator:
    return ServerProvisionOrchestrator(
        server_repo=get_server_repository(),
        proxmox_client=get_proxmox_client(),
        solapi_client=get_solapi_client(),
    )


@lru_cache()
def get_user_registration() -> RegisterUser:
    return RegisterUser(repository=get_user_repository())


@lru_cache()
def get_server_provisioning() -> ProvisionServer:
    return ProvisionServer(
        server_repo=get_server_repository(),
        user_repo=get_user_repository(),
        policy=get_provisioning_policy(),
        orchestrator=get_server_orchestrator(),
    )
