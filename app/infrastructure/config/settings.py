# from pydantic import BaseSettings, Field
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for external services and application defaults."""

    app_name: str = Field("VibeCoding Host Automation", env="APP_NAME")
    environment: str = Field("local", env="APP_ENV")

    # Proxmox settings
    proxmox_host: str = Field("https://proxmox.local", env="PROXMOX_HOST")
    proxmox_user: str = Field("root", env="PROXMOX_USER")
    proxmox_password: str = Field("", env="PROXMOX_PASSWORD")
    proxmox_realm: str = Field("pam", env="PROXMOX_REALM")
    proxmox_default_node: str | None = Field("pve", env="PROXMOX_DEFAULT_NODE")
    proxmox_node_map: dict[str, str] = Field(default_factory=dict)
    proxmox_plan_templates: dict[str, dict[str, str | int]] = Field(
        default_factory=lambda: {
            "basic": {"template_vmid": "9000", "type": "qemu"},
            "pro": {"template_vmid": "9001", "type": "qemu"},
        }
    )

    # SOLAPI settings
    solapi_api_key: str = Field("", env="SOLAPI_KEY")
    solapi_api_secret: str = Field("", env="SOLAPI_SECRET")
    solapi_from_number: str = Field("", env="SOLAPI_FROM")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
