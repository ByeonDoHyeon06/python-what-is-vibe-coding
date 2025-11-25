from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_plan_repository,
    get_proxmox_host_repository,
    get_server_provisioning,
    get_server_repository,
)
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.infrastructure.repositories.server_repository import ServerRepository
from app.interfaces.schemas import ServerCreate, ServerRead

router = APIRouter(prefix="/servers", tags=["servers"])


@router.post("", response_model=ServerRead)
def provision_server(
    payload: ServerCreate,
    provision = Depends(get_server_provisioning),
):
    try:
        server = provision.execute(user_id=payload.user_id, plan=payload.plan, location=payload.location)
        return ServerRead.from_entity(server)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/user/{user_id}", response_model=list[ServerRead])
def list_user_servers(user_id: UUID, repo: ServerRepository = Depends(get_server_repository)):
    servers = repo.list_for_user(user_id=user_id)
    return [ServerRead.from_entity(server) for server in servers]


@router.get("/metadata/allowed", tags=["metadata"])
def get_allowed_plans_and_locations(
    plans: PlanRepository = Depends(get_plan_repository),
    hosts: ProxmoxHostRepository = Depends(get_proxmox_host_repository),
):
    """Expose discoverable provisioning metadata (plans + Proxmox locations)."""

    return {
        "plans": [
            {
                "name": plan.name,
                "location": plan.location,
                "vcpu": plan.vcpu,
                "memory_mb": plan.memory_mb,
                "disk_gb": plan.disk_gb,
                "proxmox_host_id": plan.proxmox_host_id,
                "proxmox_node": plan.proxmox_node,
                "template_vmid": plan.template_vmid,
                "disk_storage": plan.disk_storage,
                "description": plan.description,
            }
            for plan in plans.list()
        ],
        "locations": sorted({host.location for host in hosts.list()}),
    }


@router.get("/{server_id}", response_model=ServerRead)
def get_server(server_id: UUID, repo: ServerRepository = Depends(get_server_repository)):
    server = repo.get(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return ServerRead.from_entity(server)
