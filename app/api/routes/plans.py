from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_plan_repository
from app.domain.models.plan import Plan
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.interfaces.schemas import PlanCreate, PlanRead, PlanUpdate

router = APIRouter(prefix="/admin/plans", tags=["plans"])


@router.post("", response_model=PlanRead)
def create_plan(payload: PlanCreate, repo: PlanRepository = Depends(get_plan_repository)):
    plan = Plan(**payload.dict())
    try:
        repo.add(plan)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PlanRead.from_entity(plan)


@router.get("", response_model=list[PlanRead])
def list_plans(repo: PlanRepository = Depends(get_plan_repository)):
    return [PlanRead.from_entity(plan) for plan in repo.list()]


@router.get("/{name}", response_model=PlanRead)
def get_plan(name: str, repo: PlanRepository = Depends(get_plan_repository)):
    plan = repo.get(name)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return PlanRead.from_entity(plan)


@router.put("/{name}", response_model=PlanRead)
def update_plan(name: str, payload: PlanUpdate, repo: PlanRepository = Depends(get_plan_repository)):
    existing = repo.get(name)
    if not existing:
        raise HTTPException(status_code=404, detail="Plan not found")

    updated = Plan(
        name=name,
        vcpu=payload.vcpu if payload.vcpu is not None else existing.vcpu,
        memory_gb=payload.memory_gb if payload.memory_gb is not None else existing.memory_gb,
        disk_gb=payload.disk_gb if payload.disk_gb is not None else existing.disk_gb,
        default_node=payload.default_node or existing.default_node,
        default_storage_pool=payload.default_storage_pool or existing.default_storage_pool,
    )
    repo.update(updated)
    return PlanRead.from_entity(updated)


@router.delete("/{name}")
def delete_plan(name: str, repo: PlanRepository = Depends(get_plan_repository)):
    plan = repo.get(name)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    repo.delete(name)
    return {"status": "deleted", "name": name}
