from fastapi import APIRouter, Depends

from app.api.dependencies import get_plan_repository, get_proxmox_host_repository
from app.domain.models.plan import PlanSpec
from app.domain.models.proxmox_host import ProxmoxHostConfig
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.interfaces.schemas import (
    PlanCreate,
    PlanRead,
    ProxmoxHostCreate,
    ProxmoxHostRead,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/plans", response_model=PlanRead)
def create_plan(payload: PlanCreate, repo: PlanRepository = Depends(get_plan_repository)):
    plan = PlanSpec(**payload.dict())
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
