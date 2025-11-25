from dataclasses import dataclass


@dataclass
class ProxmoxHostConfig:
    """Credentials and topology for a Proxmox API endpoint."""

    id: str
    api_url: str
    username: str
    password: str
    realm: str = "pam"
    node: str | None = None
    location: str = "kr-central"
