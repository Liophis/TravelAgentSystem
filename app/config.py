"""Application configuration loaded from chained environment files."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILES = [
    PROJECT_ROOT / ".env.local",
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "frontend" / ".env.local",
    PROJECT_ROOT / "frontend" / ".env",
    PROJECT_ROOT / "backend" / ".env.local",
    PROJECT_ROOT / "backend" / ".env",
]

for env_file in ENV_FILES:
    if env_file.exists():
        load_dotenv(env_file, override=False)


class Settings(BaseSettings):
    """Shared application settings, following the TripStar-style config layer."""

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    app_name: str = "Travel Agent System"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    api_base_url: str = "http://localhost:8000"
    amap_web_api_key: str = Field(default="", validation_alias=AliasChoices("AMAP_WEB_API_KEY", "VITE_AMAP_WEB_KEY"))
    vite_amap_web_js_key: str = Field(default="", validation_alias=AliasChoices("VITE_AMAP_WEB_JS_KEY", "AMAP_WEB_JS_KEY"))
    google_maps_api_key: str = ""
    google_maps_proxy: str = ""
    xhs_cookie: str = ""
    openai_api_key: str = Field(default="", validation_alias=AliasChoices("OPENAI_API_KEY", "LLM_API_KEY"))
    openai_base_url: str = Field(default="https://api.openai.com/v1", validation_alias=AliasChoices("OPENAI_BASE_URL", "LLM_BASE_URL"))
    openai_model: str = Field(default="gpt-4o-mini", validation_alias=AliasChoices("OPENAI_MODEL", "LLM_MODEL_ID"))
    log_level: str = "INFO"

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug_value(cls, value: Any) -> Any:
        if isinstance(value, bool):
            return value

        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on", "debug", "dev", "development"}:
            return True
        if normalized in {"0", "false", "no", "off", "release", "prod", "production", ""}:
            return False
        return value

    def get_cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()


def get_settings() -> Settings:
    return settings


_RUNTIME_SETTINGS_FILE = PROJECT_ROOT / "runtime_settings.json"
_RUNTIME_SETTING_KEYS = {
    "api_base_url",
    "amap_web_api_key",
    "vite_amap_web_js_key",
    "google_maps_api_key",
    "google_maps_proxy",
    "xhs_cookie",
    "openai_api_key",
    "openai_base_url",
    "openai_model",
    "log_level",
}


def _load_runtime_overrides() -> Dict[str, Any]:
    if not _RUNTIME_SETTINGS_FILE.exists():
        return {}
    try:
        with open(_RUNTIME_SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {k: data[k] for k in _RUNTIME_SETTING_KEYS if k in data}
    except Exception as exc:
        print(f"⚠️  读取运行时配置失败，已回退到环境变量: {exc}")
    return {}


def _persist_runtime_overrides(overrides: Dict[str, Any]) -> None:
    _RUNTIME_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_RUNTIME_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)


def _sync_env_from_settings() -> None:
    if settings.api_base_url:
        os.environ["VITE_API_BASE_URL"] = settings.api_base_url
    if settings.amap_web_api_key:
        os.environ["AMAP_WEB_API_KEY"] = settings.amap_web_api_key
        os.environ["VITE_AMAP_WEB_KEY"] = settings.amap_web_api_key
    if settings.vite_amap_web_js_key:
        os.environ["VITE_AMAP_WEB_JS_KEY"] = settings.vite_amap_web_js_key
    if settings.google_maps_api_key:
        os.environ["GOOGLE_MAPS_API_KEY"] = settings.google_maps_api_key
    if settings.google_maps_proxy:
        os.environ["GOOGLE_MAPS_PROXY"] = settings.google_maps_proxy
    if settings.xhs_cookie:
        os.environ["XHS_COOKIE"] = settings.xhs_cookie
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        os.environ["LLM_API_KEY"] = settings.openai_api_key
    if settings.openai_base_url:
        os.environ["OPENAI_BASE_URL"] = settings.openai_base_url
        os.environ["LLM_BASE_URL"] = settings.openai_base_url
    if settings.openai_model:
        os.environ["OPENAI_MODEL"] = settings.openai_model
        os.environ["LLM_MODEL_ID"] = settings.openai_model
    if settings.log_level:
        os.environ["LOG_LEVEL"] = settings.log_level


def _apply_runtime_overrides(overrides: Dict[str, Any]) -> None:
    for key, value in overrides.items():
        if key in _RUNTIME_SETTING_KEYS and hasattr(settings, key):
            setattr(settings, key, value if value is not None else "")
    _sync_env_from_settings()


def get_runtime_settings() -> Dict[str, str]:
    return {
        "api_base_url": settings.api_base_url or "",
        "amap_web_api_key": settings.amap_web_api_key or settings.vite_amap_web_js_key or "",
        "vite_amap_web_js_key": settings.vite_amap_web_js_key or "",
        "google_maps_api_key": settings.google_maps_api_key or "",
        "google_maps_proxy": settings.google_maps_proxy or "",
        "xhs_cookie": settings.xhs_cookie or "",
        "openai_api_key": settings.openai_api_key or "",
        "openai_base_url": settings.openai_base_url or "",
        "openai_model": settings.openai_model or "",
        "log_level": settings.log_level or "",
    }


def update_runtime_settings(updates: Dict[str, Any]) -> Dict[str, str]:
    normalized: Dict[str, Any] = {}
    for key, value in updates.items():
        if key not in _RUNTIME_SETTING_KEYS:
            continue
        normalized[key] = str(value).strip() if value is not None else ""

    existing = _load_runtime_overrides()
    existing.update(normalized)
    _persist_runtime_overrides(existing)
    _apply_runtime_overrides(existing)
    return get_runtime_settings()


_runtime_overrides = _load_runtime_overrides()
_apply_runtime_overrides(_runtime_overrides)
