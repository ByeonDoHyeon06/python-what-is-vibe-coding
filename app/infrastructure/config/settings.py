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
    expiry_warning_days: int = Field(3, env="EXPIRY_WARNING_DAYS")

    # Admin
    admin_api_key: str = Field("", env="ADMIN_API_KEY")

    # JWT auth
    jwt_issuer: str | None = Field(None, env="JWT_ISSUER")
    jwt_audience: str | None = Field(None, env="JWT_AUDIENCE")
    jwt_secret: str | None = Field(None, env="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
