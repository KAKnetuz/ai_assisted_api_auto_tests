"""
Константы для интеграционных тестов.

Все значения (коды ответов, тексты ошибок, шкалы тарифов) — демонстрационные
плейсхолдеры, а не данные реальной системы.
"""
from enum import IntEnum, StrEnum
from typing import Final

from integration_tests.config.endpoints import Platform


class AccountTag(StrEnum):
    """Типы лицевых счетов."""

    MAIN = "main"
    SERVICES = "services"
    EXTRA = "extra"


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class ResultCode(IntEnum):
    """Бизнес-коды в поле Code ответа API."""

    SUCCESS = 0
    SUPPLIER_NOT_FOUND = 1001
    PROCEDURE_NOT_FOUND = 1002
    ALREADY_PAID = 1003
    TARIFF_NOT_FOUND = 1004
    DUPLICATE_ORDER = 1005
    CURRENCY_NOT_SUPPORTED = 1006


# --- Платформы, на которых доступна операция (для parametrize) ---
ACCOUNT_INFO_PLATFORMS: Final[tuple[Platform, ...]] = (Platform.CORE, Platform.PLATFORM_B)
ORDER_CREATE_PLATFORMS: Final[tuple[Platform, ...]] = (Platform.CORE, Platform.PLATFORM_B)
ORDER_LIST_PLATFORMS: Final[tuple[Platform, ...]] = (Platform.CORE, Platform.PLATFORM_B)
BLOCK_PLATFORMS: Final[tuple[Platform, ...]] = (Platform.PLATFORM_A, Platform.PLATFORM_B)
PAYMENT_PLATFORMS: Final[tuple[Platform, ...]] = (Platform.PLATFORM_A, Platform.PLATFORM_B)

SORT_DIRECTIONS: Final[tuple[SortDirection, ...]] = (
    SortDirection.ASC,
    SortDirection.DESC,
)

DEFAULT_ACCOUNT_TAG: Final[AccountTag] = AccountTag.MAIN
CURRENCY_RUB: Final[int] = 643  # ISO 4217
CURRENCY_USD: Final[int] = 840  # ISO 4217

LIMIT_ONE: Final[int] = 1
LIMIT_ZERO: Final[int] = 0
LIMIT_NEGATIVE: Final[int] = -1
OFFSET_NEGATIVE: Final[int] = -1
OFFSET_BEYOND: Final[int] = 10_000

TARIFF_REQUIRED_FIELDS: Final[tuple[str, ...]] = ("TariffName", "TariffType")
ORDER_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "OrderUuid",
    "OrderStatus",
    "OrderPayStatus",
    "AccountNumber",
    "AccountTag",
    "Price",
)


class ErrorText:
    """Стабильные фрагменты сообщений об ошибках API."""

    REQUIRED_FIELD: Final[str] = "Обязательное поле"
    VALID_UUID: Final[str] = "Must be a valid UUID"
    VALID_NUMBER: Final[str] = "Введите правильное число"
    GE_ONE: Final[str] = "больше либо равно 1"
    GE_ZERO: Final[str] = "больше либо равно 0"
    MIN_PRICE: Final[str] = "0.00"
    NOT_FOUND: Final[str] = "не найден"
    ALREADY_EXISTS: Final[str] = "уже существует"
    ALREADY_PAID: Final[str] = "уже оплачен"
    OUT_OF_RANGE: Final[str] = "вне допустимого диапазона"
    CURRENCY: Final[str] = "валюта"


# --- Демонстрационные тарифные шкалы: цена процедуры → ожидаемое списание ---
PAYMENT_CONTRACT_PRICES: Final[dict[Platform, dict[str, str]]] = {
    Platform.PLATFORM_A: {  # процентный тариф: 2% от цены
        "1000": "20.00",
        "5000": "100.00",
        "250": "5.00",
        "100": "2.00",
    },
    Platform.PLATFORM_B: {  # ступенчатая шкала
        "100000": "5000.00",
        "1000000": "7500.00",
        "5000000": "10000.00",
        "100000000": "12500.00",
    },
}
PAYMENT_DEFAULT_PRICE: Final[dict[Platform, str]] = {
    Platform.PLATFORM_A: "1000",
    Platform.PLATFORM_B: "100000",
}
PAYMENT_TARIFF_BY_PLATFORM: Final[dict[Platform, str]] = {
    Platform.PLATFORM_A: "payment_tariff_a",
    Platform.PLATFORM_B: "payment_tariff_b",
}
PAYMENT_ACCOUNT_TAG_BY_PLATFORM: Final[dict[Platform, AccountTag]] = {
    Platform.PLATFORM_A: AccountTag.SERVICES,
    Platform.PLATFORM_B: AccountTag.MAIN,
}
FORCE_PAYMENT_SCALE: Final[tuple[tuple[str, str], ...]] = (
    ("50.00", "5.00"),
    ("250.00", "10.00"),
    ("750.00", "15.00"),
)

NONEXISTENT_ENTITY_STATUSES: Final[tuple[int, ...]] = (200, 404, 422)
INVALID_DATE_STATUSES: Final[tuple[int, ...]] = (200, 400, 422)
