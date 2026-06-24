from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str
    auth_access_token_expire_minutes: int
    auth_refresh_token_expire_days: int
    auth_jwt_secret_key: str
    auth_cookie_domain: str = "localhost"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "Lax"
    internal_api_token: str
    encryption_key: str
    backend_cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()

