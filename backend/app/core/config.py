from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Tour Guide API"
    app_version: str = "0.1.0"
    app_env: str = Field(default="development", alias="APP_ENV")
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )
    database_url: str = Field(
        default="postgresql+psycopg://smart_tour:smart_tour_dev@postgres:5432/smart_tour_guide",
        alias="DATABASE_URL",
    )
    api_database_url: str = Field(default="sqlite:///./smart_tour_dev.db", alias="API_DATABASE_URL")
    dev_database_url: str = Field(default="sqlite:///./smart_tour_dev.db", alias="DEV_DATABASE_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    secret_key: str = Field(default="change-me-in-local-env", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    osm_default_place: str = Field(
        default="Beijing University of Posts and Telecommunications Shahe Campus, Beijing, China",
        alias="OSM_DEFAULT_PLACE",
    )
    osm_fallback_lat: float = Field(default=40.15608, alias="OSM_FALLBACK_LAT")
    osm_fallback_lng: float = Field(default=116.28333, alias="OSM_FALLBACK_LNG")
    osm_fallback_dist: int = Field(default=1500, alias="OSM_FALLBACK_DIST")
    amap_web_api_key: str | None = Field(default=None, alias="AMAP_WEB_API_KEY")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_timeout_seconds: float = Field(default=20, alias="LLM_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
