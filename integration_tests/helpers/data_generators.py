"""
Генераторы тестовых данных для API-тестов.
Содержит фабрики для создания:
- UUID, случайных строк, чисел
- Даты и времени в формате ISO 8601
- Номеров процедур и заказов
- Типовых payload для создания заказов, блокировок и т.д.
"""

import random
import string
import uuid
from datetime import UTC, datetime, timedelta  # <-- Добавляем timezone
from typing import Any

from integration_tests.config.constants import CURRENCY_RUB, AccountTag


class DataGenerators:
    """Генераторы тестовых данных."""

    # --- Базовые генераторы ---

    @staticmethod
    def generate_uuid() -> str:
        """Генерация валидного UUID v4."""
        return str(uuid.uuid4())

    @staticmethod
    def generate_nonexistent_uuid() -> str:
        """
        Генерация валидного по формату, но заведомо несуществующего UUID.
        Используется в негативных тестах.
        """
        return f"00000000-0000-4000-8000-{uuid.uuid4().hex[-12:]}"

    @staticmethod
    def generate_invalid_uuid() -> str:
        """Генерация строки с невалидным форматом UUID."""
        return "неправильный-uuid-123"

    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        """
        Генерация случайной строки из букв и цифр.

        Args:
            length: длина строки.
        """
        alphabet = string.ascii_letters + string.digits
        return "".join(random.choices(alphabet, k=length))

    @staticmethod
    def generate_procedure_number() -> str:
        """Генерация случайного 4-значного номера процедуры."""
        suffix = "".join(random.choices(string.digits, k=8))
        return f"PROC-{suffix}"

    @staticmethod
    def generate_price(min_value: int = 1, max_value: int = 1000) -> str:
        """
        Генерация цены в виде строки (как требует API).

        Args:
            min_value: минимальное значение.
            max_value: максимальное значение.
        """
        return str(random.randint(min_value, max_value))

    # --- Генераторы дат ---

    @staticmethod
    def generate_timestamp(days_offset: int = 0, hours_offset: int = 0) -> str:
        """
        Генерация ISO 8601 timestamp относительно текущего момента.

        Args:
            days_offset: смещение в днях (положительное — в будущее).
            hours_offset: смещение в часах.

        Returns:
            Строка в формате 'YYYY-MM-DDTHH:MM:SS.000Z'.
        """
        # Используем timezone-aware datetime вместо устаревшего utcnow()
        dt = datetime.now(UTC) + timedelta(days=days_offset, hours=hours_offset)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    @staticmethod
    def generate_date_range(days_back: int = 30) -> dict[str, str]:
        """
        Генерация диапазона дат (FromDatetime / ToDatetime) для списка операций.

        Args:
            days_back: сколько дней назад — начало диапазона.

        Returns:
            Словарь {'from': '...', 'to': '...'}.
        """
        return {
            "from": DataGenerators.generate_timestamp(days_offset=-days_back),
            "to": DataGenerators.generate_timestamp(),
        }

    # --- Фабрики payload ---

    @staticmethod
    def build_order_create_payload(
        supplier_uuid: str,
        tariff_id: int | str,
        price: str = "100",
        procedure_number: str | None = None,
        procedure_uuid: str | None = None,
        account_number: str | None = None,
    ) -> dict[str, Any]:
        """
        Формирование payload для создания заказа.

        Args:
            supplier_uuid: UUID поставщика.
            tariff_id: ID тарифа.
            price: цена (строка).
            procedure_number: номер процедуры (если None — генерируется).
            procedure_uuid: UUID процедуры (если None — генерируется).
            account_number: номер счёта (опционально).

        Returns:
            Словарь payload.
        """
        payload: dict[str, Any] = {
            "Price": price,
            "ProcedureNumber": procedure_number or DataGenerators.generate_procedure_number(),
            "ProcedureUuid": procedure_uuid or DataGenerators.generate_uuid(),
            "SupplierUuid": supplier_uuid,
            "TariffId": tariff_id,
        }
        if account_number:
            payload["AccountNumber"] = account_number
        return payload

    @staticmethod
    def build_order_cancel_payload(
        order_uuid: str,
        supplier_uuid: str,
        reason: str = "Тестовая отмена заказа.",
    ) -> dict[str, str]:
        """Формирование payload для отмены заказа"""
        return {
            "OrderUuid": order_uuid,
            "SupplierUuid": supplier_uuid,
            "Reason": reason,
        }

    @staticmethod
    def build_order_status_payload(
        supplier_uuid: str,
        order_uuid: str | None = None,
        procedure_uuid: str | None = None,
        procedure_number: str | None = None,
    ) -> dict[str, str]:
        """Формирование payload для проверки статуса заказа."""
        payload: dict[str, str] = {"SupplierUuid": supplier_uuid}
        if order_uuid:
            payload["OrderUuid"] = order_uuid
        if procedure_uuid:
            payload["ProcedureUuid"] = procedure_uuid
        if procedure_number:
            payload["ProcedureNumber"] = procedure_number
        return payload

    @staticmethod
    def build_block_payload(
        supplier_uuid: str,
        account_number: str,
        tariff_unique_name: str,
        price: str = "100",
        procedure_number: str | None = None,
        procedure_uuid: str | None = None,
        account_tag: str = AccountTag.MAIN,
    ) -> dict[str, Any]:
        """Формирование payload для блокировки средств."""
        return {
            "Price": price,
            "ProcedureNumber": procedure_number or DataGenerators.generate_procedure_number(),
            "ProcedureUuid": procedure_uuid or DataGenerators.generate_uuid(),
            "SupplierUuid": supplier_uuid,
            "TariffUniqueName": tariff_unique_name,
            "AccountNumber": account_number,
            "AccountTag": account_tag,
        }

    @staticmethod
    def build_account_info_payload(
        supplier_uuid: str,
        account_number: str,
        account_tag: str = AccountTag.MAIN,
        currency_code: int = CURRENCY_RUB,
    ) -> dict[str, Any]:
        """Формирование payload для запроса информации о счёте."""
        return {
            "SupplierUuid": supplier_uuid,
            "AccountNumber": account_number,
            "AccountTag": account_tag,
            "CurrencyCode": currency_code,
        }

    @staticmethod
    def build_operation_list_payload(
        supplier_uuid: str,
        from_datetime: str | None = None,
        to_datetime: str | None = None,
        limit: int = 100,
        offset: int = 0,
        operation_types: list[int] | None = None,
    ) -> dict[str, Any]:
        """Формирование payload для списка операций."""
        if from_datetime is None:
            from_datetime = DataGenerators.generate_timestamp(days_offset=-60)
        if to_datetime is None:
            to_datetime = DataGenerators.generate_timestamp()

        return {
            "SupplierUuid": supplier_uuid,
            "FromDatetime": from_datetime,
            "ToDatetime": to_datetime,
            "Limit": limit,
            "Offset": offset,
            "Type": operation_types or [1],
        }
