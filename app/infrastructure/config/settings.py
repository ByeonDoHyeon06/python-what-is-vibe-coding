from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for external services and application defaults."""

    app_name: str = Field("VibeCoding Host Automation", env="APP_NAME")
    environment: str = Field("local", env="APP_ENV")

    # Proxmox settings
    proxmox_host: str = Field("https://proxmox.local", env="PROXMOX_HOST")
    proxmox_username: str = Field("root", env="PROXMOX_USERNAME")
    proxmox_password: str = Field("", env="PROXMOX_PASSWORD")
    proxmox_realm: str = Field("pam", env="PROXMOX_REALM")

    # SOLAPI settings
    solapi_api_key: str = Field("", env="SOLAPI_KEY")
    solapi_api_secret: str = Field("", env="SOLAPI_SECRET")
    solapi_from_number: str = Field("", env="SOLAPI_FROM")

    # Persistence
    database_path: str = Field("data/vibecoding.db", env="DATABASE_PATH")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
