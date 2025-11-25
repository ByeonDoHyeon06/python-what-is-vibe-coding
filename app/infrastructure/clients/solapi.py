from app.infrastructure.config.settings import settings


class SolapiClient:
    """Minimal SOLAPI SMS sender abstraction."""

    def __init__(self):
        self.api_key = settings.solapi_api_key
        self.api_secret = settings.solapi_api_secret
        self.from_number = settings.solapi_from_number

    def send_provisioning_sms(self, to: str, message: str) -> None:
        """Send an SMS via SOLAPI.

        The real implementation would use the official SDK: https://developers.solapi.dev
        """

        # Placeholder hook for the official client
        return None

    def send_status_sms(self, to: str, message: str) -> None:
        """Generic SMS sender for lifecycle and expiry notices."""

        # Placeholder hook for the official client
        return None
