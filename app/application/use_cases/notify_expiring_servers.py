from datetime import datetime

from app.infrastructure.clients.solapi import SolapiClient
from app.infrastructure.repositories.server_repository import ServerRepository
from app.infrastructure.repositories.user_repository import UserRepository


class NotifyExpiringServers:
    """Send SOLAPI alerts for servers approaching expiration."""

    def __init__(
        self,
        server_repo: ServerRepository,
        user_repo: UserRepository,
        solapi_client: SolapiClient,
        warning_days: int,
    ):
        self.server_repo = server_repo
        self.user_repo = user_repo
        self.solapi_client = solapi_client
        self.warning_days = warning_days

    def notify(self) -> None:
        now = datetime.utcnow()
        expiring = self.server_repo.list_expiring_within(now, self.warning_days)
        for server in expiring:
            if server.expire_at is None:
                continue

            # avoid sending multiple times per day
            if server.last_notified_at and server.last_notified_at.date() == now.date():
                continue

            user = self.user_repo.get(server.owner_id)
            if not user:
                continue

            self.solapi_client.send_status_sms(
                to=user.phone_number,
                message=(
                    f"{user.email}님, {server.expire_at.date()}에 서버 만료 예정입니다. "
                    "연장이 필요하면 만료 전까지 갱신해주세요."
                ),
            )
            server.last_notified_at = now
            self.server_repo.update(server)
