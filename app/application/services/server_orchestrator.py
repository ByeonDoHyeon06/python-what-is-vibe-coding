import httpx

from app.domain.models.plan import PlanSpec
from app.domain.models.proxmox_host import ProxmoxHostConfig
from app.domain.models.server import Server, ServerStatus
from app.domain.models.user import User
from app.infrastructure.clients.proxmox import ProxmoxClient
from app.infrastructure.clients.solapi import SolapiClient
from app.infrastructure.repositories.proxmox_host_repository import ProxmoxHostRepository
from app.infrastructure.repositories.server_repository import ServerRepository


class ServerProvisionOrchestrator:
    """Implements a saga-style orchestration around server provisioning.

    * Validates the domain rules (done upstream).
    * Calls Proxmox to create infrastructure.
    * Sends SMS notifications via SOLAPI.
    * Rolls back the Proxmox resource when any step fails.
    """

    def __init__(
        self,
        server_repo: ServerRepository,
        proxmox_hosts: ProxmoxHostRepository,
        proxmox_client: ProxmoxClient,
        solapi_client: SolapiClient,
    ):
        self.server_repo = server_repo
        self.proxmox_hosts = proxmox_hosts
        self.proxmox_client = proxmox_client
        self.solapi_client = solapi_client

    def provision(
        self, server: Server, user: User, plan: PlanSpec, host: ProxmoxHostConfig, vm_password: str
    ) -> None:
        try:
            server.status = ServerStatus.PROVISIONING
            self.server_repo.update(server)

            self.solapi_client.send_status_sms(
                to=user.phone_number,
                message=(
                    f"{user.email}님, 서버 설정이 시작되었습니다. "
                    f"플랜: {server.plan}, 위치: {server.location}"
                ),
            )

            external_id = self.proxmox_client.provision_server(server, plan=plan, host=host)
            server.external_id = external_id

            try:
                self.proxmox_client.set_admin_password(
                    external_id=server.external_id,
                    host=host,
                    node=server.proxmox_node or host.node,
                    password=vm_password,
                )
            except Exception:  # noqa: BLE001
                pass

            proxmox_status = None
            try:
                proxmox_status = self.proxmox_client.get_server_status(
                    external_id=server.external_id, host=host, node=server.proxmox_node or host.node
                )
            except Exception:
                proxmox_status = None

            server.status = self._map_proxmox_status(proxmox_status) or ServerStatus.STOPPED
            self.server_repo.update(server)

            self.solapi_client.send_provisioning_sms(
                to=user.phone_number,
                message=(
                    f"{user.email}님, 서버가 준비되었습니다. "
                    f"ID: {server.external_id}, 플랜: {server.plan}, 위치: {server.location}"
                ),
            )
        except httpx.TimeoutException as exc:
            server.status = ServerStatus.FAILED
            self.server_repo.update(server)
            self.solapi_client.send_status_sms(
                to=user.phone_number,
                message=f"{user.email}님, 서버 설정이 지연되었습니다. 잠시 후 다시 확인해주세요.",
            )
            raise ValueError("Provisioning timed out; please retry") from exc
        except Exception as exc:  # noqa: BLE001
            self._rollback(server)
            server.status = ServerStatus.FAILED
            self.server_repo.update(server)
            self.solapi_client.send_status_sms(
                to=user.phone_number,
                message=f"{user.email}님, 서버 생성 중 오류가 발생했습니다. 지원팀에 문의해주세요.",
            )
            raise ValueError("Provisioning failed; see server status") from exc

    def _rollback(self, server: Server) -> None:
        if server.external_id and server.proxmox_host_id:
            host = self.proxmox_hosts.get(server.proxmox_host_id)
            if host:
                node = server.proxmox_node or host.node
                self.proxmox_client.destroy_server(server.external_id, host=host, node=node)
        server.status = ServerStatus.ROLLED_BACK
        self.server_repo.update(server)

    @staticmethod
    def _map_proxmox_status(status: str | None) -> ServerStatus | None:
        if not status:
            return None

        normalized = status.lower()
        if normalized in {"running", "online", "started"}:
            return ServerStatus.ACTIVE
        if normalized in {"stopped", "shutdown", "off"}:
            return ServerStatus.STOPPED
        if normalized in {"paused", "suspended", "hibernated"}:
            return ServerStatus.STOPPED
        if normalized in {"booting", "starting", "init"}:
            return ServerStatus.PROVISIONING
        return ServerStatus.FAILED if normalized in {"failed", "error"} else None
