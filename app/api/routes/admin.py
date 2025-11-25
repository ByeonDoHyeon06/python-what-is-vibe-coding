from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_config_repository
from app.infrastructure.repositories.config_repository import ProvisioningConfigRepository
from app.interfaces.schemas import (
    AllowedSettings,
    AllowedSettingsUpdate,
    ProxmoxHostRead,
    ProxmoxHostUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/settings/allowed", response_model=AllowedSettings)
def get_allowed_settings(config: ProvisioningConfigRepository = Depends(get_config_repository)):
    return AllowedSettings(
        allowed_locations=sorted(config.get_allowed_locations()),
        allowed_plans=sorted(config.get_allowed_plans()),
    )


@router.put("/settings/allowed", response_model=AllowedSettings)
def update_allowed_settings(
    payload: AllowedSettingsUpdate,
    config: ProvisioningConfigRepository = Depends(get_config_repository),
):
    if payload.allowed_locations is None and payload.allowed_plans is None:
        raise HTTPException(status_code=400, detail="No updates provided")

    if payload.allowed_locations is not None:
        config.set_allowed_locations(payload.allowed_locations)
    if payload.allowed_plans is not None:
        config.set_allowed_plans(payload.allowed_plans)

    return AllowedSettings(
        allowed_locations=sorted(config.get_allowed_locations()),
        allowed_plans=sorted(config.get_allowed_plans()),
    )


@router.get("/proxmox/hosts", response_model=list[ProxmoxHostRead])
def list_proxmox_hosts(config: ProvisioningConfigRepository = Depends(get_config_repository)):
    return [ProxmoxHostRead.from_entity(host) for host in config.list_proxmox_hosts()]


@router.put("/proxmox/hosts/{host_name}", response_model=ProxmoxHostRead)
def upsert_proxmox_host(
    host_name: str,
    payload: ProxmoxHostUpdate,
    config: ProvisioningConfigRepository = Depends(get_config_repository),
):
    host = config.upsert_proxmox_host(host_name, payload.nodes)
    return ProxmoxHostRead.from_entity(host)


@router.delete("/proxmox/hosts/{host_name}")
def delete_proxmox_host(host_name: str, config: ProvisioningConfigRepository = Depends(get_config_repository)):
    deleted = config.delete_proxmox_host(host_name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Host not found")
    return {"status": "deleted", "host": host_name}

