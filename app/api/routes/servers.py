from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_current_user,
    get_plan_repository,
    get_proxmox_host_repository,
    get_server_expiry_extender,
    get_server_power_control,
    get_server_provisioning,
    get_server_status_refresher,
    get_server_upgrade,
    get_upgrade_repository,
    get_password_resetter,
)
from app.application.use_cases.control_server_power import ControlServerPower
from app.application.use_cases.extend_server_expiry import ExtendServerExpiry
from app.application.use_cases.refresh_server_status import RefreshServerStatus
from app.application.use_cases.reset_server_password import ResetServerPassword
from app.infrastructure.repositories.plan_repository import PlanRepository
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.interfaces.schemas import ServerCreate, ServerExtendRequest, ServerRead, ServerUpgradeRequest

router = APIRouter(prefix="/servers", tags=["servers"])


@router.post("", response_model=ServerRead)
def provision_server(
    payload: ServerCreate,
    current_user = Depends(get_current_user),
    provision = Depends(get_server_provisioning),
):
    try:
        server, password = provision.execute(
            user_id=current_user.id,
            plan=payload.plan,
            location=payload.location,
            expire_in_days=payload.expire_in_days,
        )
        return ServerRead.from_entity(server, vm_password=password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/user/{user_id}", response_model=list[ServerRead])
def list_user_servers(
    user_id: UUID,
    current_user = Depends(get_current_user),
    refresher: RefreshServerStatus = Depends(get_server_status_refresher),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to view these servers")
    servers = refresher.refresh_for_user(user_id=user_id)
    return [ServerRead.from_entity(server) for server in servers]


@router.get("/metadata/allowed", tags=["metadata"])
def get_allowed_plans_and_locations(
    plans: PlanRepository = Depends(get_plan_repository),
    hosts: ProxmoxHostRepository = Depends(get_proxmox_host_repository),
    upgrades = Depends(get_upgrade_repository),
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
                "clone_mode": plan.clone_mode,
                "price": plan.price,
                "default_expire_days": plan.default_expire_days,
                "description": plan.description,
            }
            for plan in plans.list()
        ],
        "locations": sorted({host.location for host in hosts.list()}),
        "upgrades": [
            {
                "name": upgrade.name,
                "add_vcpu": upgrade.add_vcpu,
                "add_memory_mb": upgrade.add_memory_mb,
                "add_disk_gb": upgrade.add_disk_gb,
                "price": upgrade.price,
                "description": upgrade.description,
            }
            for upgrade in upgrades.list()
        ],
    }


@router.get("/{server_id}", response_model=ServerRead)
def get_server(
    server_id: UUID,
    current_user = Depends(get_current_user),
    refresher: RefreshServerStatus = Depends(get_server_status_refresher),
):
    server = refresher.refresh_owned(server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found or not owned")
    return ServerRead.from_entity(server)


@router.post("/{server_id}/start", response_model=ServerRead)
def start_server(
    server_id: UUID,
    current_user = Depends(get_current_user),
    control: ControlServerPower = Depends(get_server_power_control),
):
    try:
        server = control.start(
            server_id,
            user_id=current_user.id,
        )
        return ServerRead.from_entity(server)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/{server_id}/stop", response_model=ServerRead)
def stop_server(
    server_id: UUID,
    current_user = Depends(get_current_user),
    control: ControlServerPower = Depends(get_server_power_control),
):
    try:
        server = control.stop(
            server_id,
            user_id=current_user.id,
        )
        return ServerRead.from_entity(server)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/{server_id}/reboot", response_model=ServerRead)
def reboot_server(
    server_id: UUID,
    current_user = Depends(get_current_user),
    control: ControlServerPower = Depends(get_server_power_control),
):
    try:
        server = control.reboot(
            server_id,
            user_id=current_user.id,
        )
        return ServerRead.from_entity(server)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/{server_id}/reset", response_model=ServerRead)
def reset_server(
    server_id: UUID,
    current_user = Depends(get_current_user),
    control: ControlServerPower = Depends(get_server_power_control),
):
    try:
        server = control.reset(
            server_id,
            user_id=current_user.id,
        )
        return ServerRead.from_entity(server)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/{server_id}/shutdown", response_model=ServerRead)
def shutdown_server(
    server_id: UUID,
    current_user = Depends(get_current_user),
    control: ControlServerPower = Depends(get_server_power_control),
):
    try:
        server = control.shutdown(
            server_id,
            user_id=current_user.id,
        )
        return ServerRead.from_entity(server)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/{server_id}/suspend", response_model=ServerRead)
def suspend_server(
    server_id: UUID,
    current_user = Depends(get_current_user),
    control: ControlServerPower = Depends(get_server_power_control),
):
    try:
        server = control.suspend(
            server_id,
            user_id=current_user.id,
        )
        return ServerRead.from_entity(server)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/{server_id}/resume", response_model=ServerRead)
def resume_server(
    server_id: UUID,
    current_user = Depends(get_current_user),
    control: ControlServerPower = Depends(get_server_power_control),
):
    try:
        server = control.resume(
            server_id,
            user_id=current_user.id,
        )
        return ServerRead.from_entity(server)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/{server_id}/extend", response_model=ServerRead)
def extend_server(
    server_id: UUID,
    payload: ServerExtendRequest,
    current_user = Depends(get_current_user),
    extender: ExtendServerExpiry = Depends(get_server_expiry_extender),
):
    try:
        server = extender.extend(
            server_id,
            additional_days=payload.additional_days,
            user_id=current_user.id,
        )
        return ServerRead.from_entity(server)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/{server_id}/upgrade", response_model=ServerRead)
def upgrade_server(
    server_id: UUID,
    payload: ServerUpgradeRequest,
    current_user = Depends(get_current_user),
    upgrader = Depends(get_server_upgrade),
):
    try:
        server = upgrader.apply(
            server_id,
            upgrade_name=payload.upgrade,
            user_id=current_user.id,
        )
        return ServerRead.from_entity(server)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/{server_id}/password/reset", response_model=ServerRead)
def reset_password(
    server_id: UUID,
    current_user = Depends(get_current_user),
    resetter: ResetServerPassword = Depends(get_password_resetter),
):
    try:
        server, password = resetter.reset(
            server_id,
            user_id=current_user.id,
        )
        return ServerRead.from_entity(server, vm_password=password)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
