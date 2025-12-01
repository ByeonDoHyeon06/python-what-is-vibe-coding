from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_plan_repository,
    get_proxmox_host_repository,
    get_upgrade_repository,
    get_server_repository,
    get_server_status_refresher,
    require_admin,
)
from app.domain.models.server import ServerStatus
from app.domain.models.plan import PlanSpec
from app.domain.models.proxmox_host import ProxmoxHostConfig
from app.domain.models.upgrade import UpgradeSpec
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.infrastructure.repositories.upgrade_repository import UpgradeRepository
from app.infrastructure.repositories.server_repository import ServerRepository
from app.application.use_cases.refresh_server_status import RefreshServerStatus
from app.interfaces.schemas import (
    PlanCreate,
    PlanRead,
    ProxmoxHostCreate,
    ProxmoxHostRead,
    UpgradeCreate,
    UpgradeRead,
    ServerRead,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/plans", response_model=PlanRead)
def create_plan(payload: PlanCreate, repo: PlanRepository = Depends(get_plan_repository)):
    plan = PlanSpec(**payload.dict(use_enum_values=True))
    repo.add(plan)
    return PlanRead.from_entity(plan)


@router.get("/plans", response_model=list[PlanRead])
def list_plans(repo: PlanRepository = Depends(get_plan_repository)):
    return [PlanRead.from_entity(plan) for plan in repo.list()]


@router.delete("/plans/{name}", status_code=204)
def delete_plan(name: str, repo: PlanRepository = Depends(get_plan_repository)):
    repo.delete(name)


@router.post("/proxmox/hosts", response_model=ProxmoxHostRead)
def add_proxmox_host(payload: ProxmoxHostCreate, repo: ProxmoxHostRepository = Depends(get_proxmox_host_repository)):
    host = ProxmoxHostConfig(**payload.dict())
    repo.add(host)
    return ProxmoxHostRead.from_entity(host)


@router.get("/proxmox/hosts", response_model=list[ProxmoxHostRead])
def list_proxmox_hosts(repo: ProxmoxHostRepository = Depends(get_proxmox_host_repository)):
    return [ProxmoxHostRead.from_entity(host) for host in repo.list()]


@router.delete("/proxmox/hosts/{host_id}", status_code=204)
def delete_proxmox_host(host_id: str, repo: ProxmoxHostRepository = Depends(get_proxmox_host_repository)):
    repo.delete(host_id)


@router.post("/upgrades", response_model=UpgradeRead)
def create_upgrade(
    payload: UpgradeCreate, repo: UpgradeRepository = Depends(get_upgrade_repository)
):
    upgrade = UpgradeSpec(**payload.dict())
    repo.add(upgrade)
    return UpgradeRead.from_entity(upgrade)


@router.get("/upgrades", response_model=list[UpgradeRead])
def list_upgrades(repo: UpgradeRepository = Depends(get_upgrade_repository)):
    return [UpgradeRead.from_entity(upgrade) for upgrade in repo.list()]


@router.delete("/upgrades/{name}", status_code=204)
def delete_upgrade(name: str, repo: UpgradeRepository = Depends(get_upgrade_repository)):
    repo.delete(name)


@router.get("/servers", response_model=list[ServerRead])
def list_servers(
    owner_id: UUID | None = None,
    status: ServerStatus | None = None,
    plan: str | None = None,
    location: str | None = None,
    repo: ServerRepository = Depends(get_server_repository),
    refresher: RefreshServerStatus = Depends(get_server_status_refresher),
):
    servers = repo.list_all(owner_id=owner_id, status=status, plan=plan, location=location)
    return [ServerRead.from_entity(refresher.refresh_entity(server)) for server in servers]
