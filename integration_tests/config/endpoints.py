"""
Модуль с константами URL-эндпоинтов API.
Все пути относительно BASE_URL.

Платформы:
    - core        — базовый модуль (общие методы для всех платформ);
    - platform_a  — первая торговая платформа;
    - platform_b  — вторая торговая платформа.
"""
from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Final


def _ep(base: str, *segments: str) -> str:
    return "/".join((base, *segments))


class Platform(StrEnum):
    """Идентификаторы платформ (совместимы со строками)."""

    CORE = "core"
    PLATFORM_A = "platform_a"
    PLATFORM_B = "platform_b"


CORE_MODULE: Final[str] = "/api/v1/core"
PLATFORM_A_MODULE: Final[str] = "/api/v1/platform-a"
PLATFORM_B_MODULE: Final[str] = "/api/v1/platform-b"
PAYMENTS_MODULE: Final[str] = "/api/v1/payments"

# --- core ---
ACCOUNT_INFO: Final[str] = _ep(CORE_MODULE, "accounts", "info")
ORDER_CREATE: Final[str] = _ep(CORE_MODULE, "orders", "create")
ORDER_CANCEL: Final[str] = _ep(CORE_MODULE, "orders", "cancel")
ORDER_STATUS: Final[str] = _ep(CORE_MODULE, "orders", "status")
ORDER_LIST: Final[str] = _ep(CORE_MODULE, "orders", "list")
TARIFF_INFO: Final[str] = _ep(CORE_MODULE, "tariffs", "calculate")
TARIFF_SEARCH: Final[str] = _ep(CORE_MODULE, "tariffs", "search")
COUNTERPARTY_COUNT: Final[str] = _ep(CORE_MODULE, "counterparties", "count")
FUNDS_UNBLOCK: Final[str] = _ep(CORE_MODULE, "funds", "unblock")

# --- platform_a ---
FUNDS_BLOCK_A: Final[str] = _ep(PLATFORM_A_MODULE, "funds", "block")
TARIFF_INFO_A: Final[str] = _ep(PLATFORM_A_MODULE, "tariffs", "calculate")
PAYMENT_A: Final[str] = _ep(PLATFORM_A_MODULE, "payments")
FORCE_PAYMENT: Final[str] = _ep(PLATFORM_A_MODULE, "payments", "force")

# --- platform_b ---
ACCOUNT_INFO_B: Final[str] = _ep(PLATFORM_B_MODULE, "accounts", "info")
ORDER_CREATE_B: Final[str] = _ep(PLATFORM_B_MODULE, "orders", "create")
ORDER_LIST_B: Final[str] = _ep(PLATFORM_B_MODULE, "orders", "list")
ORDER_STATUS_WITH_TARIFF: Final[str] = _ep(PLATFORM_B_MODULE, "orders", "status-with-tariff")
FUNDS_BLOCK_B: Final[str] = _ep(PLATFORM_B_MODULE, "funds", "block")
TARIFF_INFO_B: Final[str] = _ep(PLATFORM_B_MODULE, "tariffs", "calculate")
PAYMENT_B: Final[str] = _ep(PLATFORM_B_MODULE, "payments")
OPERATION_LIST: Final[str] = _ep(PLATFORM_B_MODULE, "operations", "list")

# --- payments ---
UNPAID_ORDERS: Final[str] = _ep(PAYMENTS_MODULE, "unpaid-orders")

# --- Маппинги «платформа → эндпоинт» для API-клиентов ---
ACCOUNT_INFO_ENDPOINTS: Final[dict[Platform, str]] = {
    Platform.CORE: ACCOUNT_INFO,
    Platform.PLATFORM_B: ACCOUNT_INFO_B,
}
ORDER_CREATE_ENDPOINTS: Final[dict[Platform, str]] = {
    Platform.CORE: ORDER_CREATE,
    Platform.PLATFORM_B: ORDER_CREATE_B,
}
ORDER_LIST_ENDPOINTS: Final[dict[Platform, str]] = {
    Platform.CORE: ORDER_LIST,
    Platform.PLATFORM_B: ORDER_LIST_B,
}
ORDER_STATUS_ENDPOINTS: Final[dict[Platform, str]] = {
    Platform.CORE: ORDER_STATUS,
    Platform.PLATFORM_B: ORDER_STATUS_WITH_TARIFF,
}
TARIFF_INFO_ENDPOINTS: Final[dict[Platform, str]] = {
    Platform.CORE: TARIFF_INFO,
    Platform.PLATFORM_A: TARIFF_INFO_A,
    Platform.PLATFORM_B: TARIFF_INFO_B,
}
BLOCK_ENDPOINTS: Final[dict[Platform, str]] = {
    Platform.PLATFORM_A: FUNDS_BLOCK_A,
    Platform.PLATFORM_B: FUNDS_BLOCK_B,
}
PAYMENT_ENDPOINTS: Final[dict[Platform, str]] = {
    Platform.PLATFORM_A: PAYMENT_A,
    Platform.PLATFORM_B: PAYMENT_B,
}


def resolve(mapping: Mapping[Platform, str], platform: str, operation: str) -> str:
    """
    Возвращает URL операции для платформы.

    Raises:
        ValueError: если операция не поддерживается на указанной платформе.
    """
    url = mapping.get(platform)  # StrEnum: ключ "core" == Platform.CORE
    if not url:
        raise ValueError(
            f"Неизвестная платформа для {operation}: '{platform}'. "
            f"Допустимые значения: {[str(p) for p in mapping]}"
        )
    return url


__all__ = [
    "ACCOUNT_INFO",
    "ACCOUNT_INFO_B",
    "ACCOUNT_INFO_ENDPOINTS",
    "BLOCK_ENDPOINTS",
    "CORE_MODULE",
    "COUNTERPARTY_COUNT",
    "FORCE_PAYMENT",
    "FUNDS_BLOCK_A",
    "FUNDS_BLOCK_B",
    "FUNDS_UNBLOCK",
    "OPERATION_LIST",
    "ORDER_CANCEL",
    "ORDER_CREATE",
    "ORDER_CREATE_B",
    "ORDER_CREATE_ENDPOINTS",
    "ORDER_LIST",
    "ORDER_LIST_B",
    "ORDER_LIST_ENDPOINTS",
    "ORDER_STATUS",
    "ORDER_STATUS_ENDPOINTS",
    "ORDER_STATUS_WITH_TARIFF",
    "PAYMENTS_MODULE",
    "PAYMENT_A",
    "PAYMENT_B",
    "PAYMENT_ENDPOINTS",
    "PLATFORM_A_MODULE",
    "PLATFORM_B_MODULE",
    "TARIFF_INFO",
    "TARIFF_INFO_A",
    "TARIFF_INFO_B",
    "TARIFF_INFO_ENDPOINTS",
    "TARIFF_SEARCH",
    "UNPAID_ORDERS",
    "Platform",
    "resolve",
]
