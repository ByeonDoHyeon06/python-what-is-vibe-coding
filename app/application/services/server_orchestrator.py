from app.domain.models.server import Server, ServerStatus
from app.domain.models.user import User
from app.infrastructure.clients.proxmox import ProxmoxClient
from app.infrastructure.clients.solapi import SolapiClient
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
        proxmox_client: ProxmoxClient,
        solapi_client: SolapiClient,
    ):
        self.server_repo = server_repo
        self.proxmox_client = proxmox_client
        self.solapi_client = solapi_client

    def provision(self, server: Server, user: User) -> None:
        try:
            server.status = ServerStatus.PROVISIONING
            self.server_repo.update(server)

            node = self.proxmox_client.resolve_node(server.location)
            plan_template = self.proxmox_client.resolve_plan_template(server.plan)
            external_id = self.proxmox_client.provision_server(
                server, node=node, plan_template=plan_template
            )
            server.external_id = external_id

            server.status = ServerStatus.ACTIVE
            self.server_repo.update(server)

            self.solapi_client.send_provisioning_sms(
                to=user.phone_number,
                message=(
                    f"{user.email}님, 서버가 준비되었습니다. "
                    f"ID: {server.external_id}, 플랜: {server.plan}, 위치: {server.location}"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            self._rollback(server)
            raise exc

    def _rollback(self, server: Server) -> None:
        if server.external_id:
            self.proxmox_client.destroy_server(server.external_id)
        server.status = ServerStatus.ROLLED_BACK
        self.server_repo.update(server)
