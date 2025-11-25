from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_plan_repository,
    get_proxmox_host_repository,
    get_upgrade_repository,
)
from app.domain.models.plan import PlanSpec
from app.domain.models.proxmox_host import ProxmoxHostConfig
from app.domain.models.upgrade import UpgradeSpec
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.infrastructure.repositories.upgrade_repository import UpgradeRepository
from app.interfaces.schemas import (
    PlanCreate,
    PlanRead,
    ProxmoxHostCreate,
    ProxmoxHostRead,
    UpgradeCreate,
    UpgradeRead,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/plans", response_model=PlanRead)
def create_plan(payload: PlanCreate, repo: PlanRepository = Depends(get_plan_repository)):
    plan = PlanSpec(**payload.dict(use_enum_values=True))
    repo.add(plan)
    return PlanRead.from_entity(plan)


@router.get("/plans", response_model=list[PlanRead])
def list_plans(repo: PlanRepository = Depends(get_plan_repository)):
    return [PlanRead.from_entity(plan) for plan in repo.list()]


@router.post("/proxmox/hosts", response_model=ProxmoxHostRead)
def add_proxmox_host(payload: ProxmoxHostCreate, repo: ProxmoxHostRepository = Depends(get_proxmox_host_repository)):
    host = ProxmoxHostConfig(**payload.dict())
    repo.add(host)
    return ProxmoxHostRead.from_entity(host)


@router.get("/proxmox/hosts", response_model=list[ProxmoxHostRead])
def list_proxmox_hosts(repo: ProxmoxHostRepository = Depends(get_proxmox_host_repository)):
    return [ProxmoxHostRead.from_entity(host) for host in repo.list()]


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
