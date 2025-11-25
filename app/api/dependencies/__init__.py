from functools import lru_cache

from app.application.services.server_orchestrator import ServerProvisionOrchestrator
from app.application.use_cases.control_server_power import ControlServerPower
from app.application.use_cases.extend_server_expiry import ExtendServerExpiry
from app.application.use_cases.provision_server import ProvisionServer

from app.application.use_cases.refresh_server_status import RefreshServerStatus
from app.application.use_cases.stop_expired_servers import StopExpiredServers
from app.application.use_cases.notify_expiring_servers import NotifyExpiringServers
from app.application.use_cases.upgrade_server_resources import UpgradeServerResources
from app.application.use_cases.register_user import RegisterUser
from app.domain.models.plan import PlanSpec
from app.domain.models.proxmox_host import ProxmoxHostConfig
from app.domain.services.provisioning_policy import ProvisioningPolicy
from app.infrastructure.clients.proxmox import ProxmoxClient
from app.infrastructure.clients.solapi import SolapiClient
from app.infrastructure.config.settings import settings
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.infrastructure.repositories.server_repository import ServerRepository
from app.infrastructure.repositories.upgrade_repository import UpgradeRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.storage.sqlite import SQLiteDataStore


@lru_cache()
def get_datastore() -> SQLiteDataStore:
    return SQLiteDataStore(settings.database_path)


@lru_cache()
def get_user_repository() -> UserRepository:
    return UserRepository(get_datastore())


@lru_cache()
def get_server_repository() -> ServerRepository:
    return ServerRepository(get_datastore())


@lru_cache()
def get_plan_repository() -> PlanRepository:
    repo = PlanRepository(get_datastore())
    if not repo.get("basic"):
        repo.add(
            PlanSpec(
                name="basic",
                vcpu=1,
                memory_mb=1024,
                disk_gb=20,
                location="kr-central",
                description="Default starter plan",
                disk_storage="local-lvm",
                price=5_000,
                default_expire_days=30,
            )
        )
    if not repo.get("pro"):
        repo.add(
            PlanSpec(
                name="pro",
                vcpu=2,
                memory_mb=4096,
                disk_gb=80,
                location="kr-central",
                description="Larger VM for heavier workloads",
                disk_storage="local-lvm",
                price=12_000,
                default_expire_days=30,
            )
        )
    return repo


@lru_cache()
def get_upgrade_repository() -> UpgradeRepository:
    return UpgradeRepository(get_datastore())


@lru_cache()
def get_proxmox_host_repository() -> ProxmoxHostRepository:
    repo = ProxmoxHostRepository(get_datastore())
    if settings.proxmox_password:
        repo.add(
            ProxmoxHostConfig(
                id="default",
                api_url=settings.proxmox_host,
                username=settings.proxmox_username,
                password=settings.proxmox_password,
                realm=settings.proxmox_realm,
                node=None,
                location="kr-central",
            )
        )
    return repo


@lru_cache()
def get_provisioning_policy() -> ProvisioningPolicy:
    return ProvisioningPolicy(plans=get_plan_repository(), proxmox_hosts=get_proxmox_host_repository())


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
        proxmox_hosts=get_proxmox_host_repository(),
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
        proxmox_hosts=get_proxmox_host_repository(),
        policy=get_provisioning_policy(),
        orchestrator=get_server_orchestrator(),
    )


@lru_cache()
def get_server_upgrade() -> UpgradeServerResources:
    return UpgradeServerResources(
        server_repo=get_server_repository(),
        upgrade_repo=get_upgrade_repository(),
        proxmox_hosts=get_proxmox_host_repository(),
        proxmox_client=get_proxmox_client(),
    )


@lru_cache()
def get_server_power_control() -> ControlServerPower:
    return ControlServerPower(
        server_repo=get_server_repository(),
        proxmox_hosts=get_proxmox_host_repository(),
        proxmox_client=get_proxmox_client(),
    )


@lru_cache()
def get_server_status_refresher() -> RefreshServerStatus:
    return RefreshServerStatus(
        server_repo=get_server_repository(),
        proxmox_hosts=get_proxmox_host_repository(),
        proxmox_client=get_proxmox_client(),
    )


@lru_cache()
def get_server_expiry_extender() -> ExtendServerExpiry:
    return ExtendServerExpiry(server_repo=get_server_repository())


@lru_cache()
def get_expired_server_stopper() -> StopExpiredServers:
    return StopExpiredServers(
        server_repo=get_server_repository(),
        proxmox_hosts=get_proxmox_host_repository(),
        proxmox_client=get_proxmox_client(),
    )


@lru_cache()
def get_expiry_notifier() -> NotifyExpiringServers:
    return NotifyExpiringServers(
        server_repo=get_server_repository(),
        user_repo=get_user_repository(),
        solapi_client=get_solapi_client(),
        warning_days=settings.expiry_warning_days,
    )
