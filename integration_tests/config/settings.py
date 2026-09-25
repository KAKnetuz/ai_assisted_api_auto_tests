"""
Конфигурация интеграционных тестов.
Загружает настройки из переменных окружения / .env файла через pydantic-settings.
"""
import json
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INTEGRATION_TESTS_DIR: Path = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=str(_INTEGRATION_TESTS_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    BASE_URL: str = "https://api.example.com"
    REQUEST_TIMEOUT: int = 30

    TOKEN_SERVICE_URL: str = "/api/auth/token"

    LOG_LEVEL: str = "DEBUG"
    LOG_FILE: str | None = str(_INTEGRATION_TESTS_DIR / "logs" / "api_tests.log")

    SUPPLIER_UUIDS: list[str] = [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
        "33333333-3333-3333-3333-333333333333",
    ]

    @field_validator("SUPPLIER_UUIDS", mode="before")
    @classmethod
    def _split_supplier_uuids(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    DEFAULT_TARIFF_ID: int = 12345
    DEFAULT_TARIFF_UNIQUE_NAME: str = "fixed_tariff"
    TARIFF_SCALE_ID: int = 67890
    TARIFF_SCALE_UNIQUE_NAME: str = "scaled_tariff"


settings = Settings()
