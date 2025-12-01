from dataclasses import dataclass
from functools import lru_cache
from typing import Optional
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.application.services.server_orchestrator import ServerProvisionOrchestrator
from app.application.use_cases.control_server_power import ControlServerPower
from app.application.use_cases.extend_server_expiry import ExtendServerExpiry
from app.application.use_cases.provision_server import ProvisionServer

from app.application.use_cases.refresh_server_status import RefreshServerStatus
from app.application.use_cases.reset_server_password import ResetServerPassword
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
from app.domain.models.user import User
from app.infrastructure.storage.sqlite import SQLAlchemyDataStore


@lru_cache()
def get_datastore() -> SQLAlchemyDataStore:
    return SQLAlchemyDataStore(settings.database_path)


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


@dataclass
class AuthContext:
    user: Optional[User]
    is_admin: bool = False
    token_claims: dict | None = None


def _decode_token(token: str) -> dict:
    if not settings.jwt_issuer or not settings.jwt_audience:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT issuer/audience not configured",
        )

    options = {"verify_signature": bool(settings.jwt_secret)}
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options=options,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    return payload


def _extract_admin(claims: dict) -> bool:
    role = claims.get("role")
    if isinstance(role, str) and role.lower() == "admin":
        return True
    roles = claims.get("roles")
    if isinstance(roles, (list, tuple)) and any(str(r).lower() == "admin" for r in roles):
        return True
    scope = claims.get("scope") or claims.get("scopes")
    if isinstance(scope, str) and "admin" in {s.lower() for s in scope.split()}:
        return True
    return False


def _map_user(claims: dict) -> User:
    sub = claims.get("sub")
    issuer = claims.get("iss") or settings.jwt_issuer
    if not sub or not issuer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject/issuer")

    external_id = claims.get("external_auth_id") or f"{issuer}:{sub}"
    repo = get_user_repository()
    user = repo.get_by_external_auth(external_id)
    if not user:
        email = (
            claims.get("email")
            or claims.get("preferred_username")
            or f"{sub}@{issuer}"
        )
        phone = claims.get("phone_number") or claims.get("phone") or "unknown"
        user = User(email=email, phone_number=phone, external_auth_id=external_id)
        repo.add(user)
    return user


def get_auth_context(
    authorization: str | None = Header(default=None, alias="Authorization"),
    admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    impersonate_user: str | None = Header(default=None, alias="X-Impersonate-User"),
):
    """Authenticate via bearer token or allow admin-key override."""

    if admin_key:
        if not settings.admin_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin API key not configured",
            )
        if admin_key != settings.admin_api_key:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key")
        user = None
        if impersonate_user:
            repo = get_user_repository()
            try:
                user = repo.get(UUID(impersonate_user))  # type: ignore[arg-type]
            except Exception:  # noqa: BLE001
                user = None
        return AuthContext(user=user, is_admin=True, token_claims=None)

    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization scheme")

    claims = _decode_token(token)
    user = _map_user(claims)
    return AuthContext(user=user, is_admin=_extract_admin(claims), token_claims=claims)


def get_current_user(auth: AuthContext = Depends(get_auth_context)) -> User:
    if not auth.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User authentication required")
    return auth.user


def require_admin(auth: AuthContext = Depends(get_auth_context)):
    if auth.is_admin:
        return True
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


@lru_cache()
def get_password_resetter() -> ResetServerPassword:
    return ResetServerPassword(
        server_repo=get_server_repository(),
        proxmox_hosts=get_proxmox_host_repository(),
        proxmox_client=get_proxmox_client(),
    )
