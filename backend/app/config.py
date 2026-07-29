from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Konfigurasi aplikasi, seluruhnya dibaca dari environment variable."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    database_url: str = "sqlite:///./sentiken_dev.db"

    redis_url: str = "redis://localhost:6379/0"
    job_execution_mode: str = "inline"  # "inline" atau "rq"

    admin_email: str = "admin@sentiken.local"
    admin_password: str = "change_me_admin_password"
    admin_full_name: str = "Administrator SENTIKEN"

    jwt_secret_key: str = "change_me_to_a_long_random_secret_value"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    cors_allowed_origins: str = "*"

    rate_limit_per_minute: int = 60
    scrape_request_delay_seconds: float = 1.5
    scrape_max_retries: int = 3

    max_csv_upload_size_mb: int = 15

    ml_model_storage_dir: str = "./storage/models"
    export_storage_dir: str = "./storage/exports"

    pln_mobile_package_id: str = ""
    mypertamina_package_id: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
