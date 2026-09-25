"""
Кастомные ассерты для API-тестов.
"""

import threading
from typing import Any

import requests

from integration_tests.config.constants import ResultCode

# --- Thread-Local Context для автоматического добавления инфо о КА в ошибки ---
_test_context = threading.local()


def set_test_context(supplier_uuid: str | None = None, account_number: str | None = None) -> None:
    """Устанавливает контекст текущего теста (используется в conftest.py)."""
    _test_context.supplier_uuid = supplier_uuid or "Не указан"
    _test_context.account_number = account_number or "Не указан"


def _get_context_message() -> str:
    """Формирует строку с информацией о КА для сообщений об ошибках."""
    uuid_short = getattr(_test_context, "supplier_uuid", "Не указан")
    if uuid_short != "Не указан" and len(uuid_short) > 8:
        uuid_short = f"{uuid_short[:8]}..."

    acc_num = getattr(_test_context, "account_number", "Не указан")
    return f"\n   🏢 [КА: UUID={uuid_short}, Account={acc_num}]"


class CustomAssertions:
    """Расширенные ассерты для API-тестов."""

    # --- Проверки HTTP статус-кодов ---

    @staticmethod
    def assert_status_code(
        response: requests.Response,
        expected: int | list[int],
    ) -> None:
        """
        Проверка HTTP статус-кода с подробным сообщением и контекстом КА.
        """
        expected_list = [expected] if isinstance(expected, int) else expected
        context_msg = _get_context_message()

        if response.status_code not in expected_list:
            raise AssertionError(
                f"❌ Ожидался статус-код {expected_list}, получен {response.status_code}.{context_msg}\n"
                f"   URL: {response.url}\n"
                f"   Тело ответа: {response.text[:300]}..."
            )

    @staticmethod
    def assert_status_2xx(response: requests.Response) -> None:
        """Проверка, что статус-код в диапазоне 2xx (успех)."""
        context_msg = _get_context_message()
        if not (200 <= response.status_code < 300):
            raise AssertionError(
                f"❌ Ожидался статус 2xx, получен {response.status_code}.{context_msg}\n"
                f"   Тело ответа: {response.text[:300]}"
            )

    @staticmethod
    def assert_status_4xx(response: requests.Response) -> None:
        """Проверка, что статус-код в диапазоне 4xx (ошибка клиента)."""
        context_msg = _get_context_message()
        if not (400 <= response.status_code < 500):
            raise AssertionError(
                f"❌ Ожидался статус 4xx, получен {response.status_code}.{context_msg}\n"
                f"   Тело ответа: {response.text[:300]}"
            )

    # --- Проверки JSON-ответа ---

    @staticmethod
    def assert_valid_json(response: requests.Response) -> Any:
        """
        Проверка, что ответ — валидный JSON, и возврат распарсенных данных.
        """
        context_msg = _get_context_message()
        try:
            return response.json()
        except ValueError as e:
            raise AssertionError(
                f"❌ Ответ не является валидным JSON.{context_msg}\n   Текст ответа: {response.text[:300]}"
            ) from e

    @staticmethod
    def assert_field_exists(
        data: dict[str, Any],
        field: str,
        field_type: type | None = None,
    ) -> None:
        """
        Проверка наличия поля и (опционально) его типа.
        """
        context_msg = _get_context_message()
        if field not in data:
            raise AssertionError(
                f"❌ Поле '{field}' отсутствует в ответе.{context_msg}\n   Доступные поля: {list(data.keys())}"
            )
        if field_type is not None and not isinstance(data[field], field_type):
            raise AssertionError(
                f"❌ Поле '{field}' должно иметь тип {field_type.__name__}, "
                f"получен {type(data[field]).__name__}.{context_msg}"
            )

    @staticmethod
    def assert_fields_exist(
        data: dict[str, Any],
        fields: list[str],
    ) -> None:
        """Проверка наличия нескольких полей."""
        context_msg = _get_context_message()
        missing = [f for f in fields if f not in data]
        if missing:
            raise AssertionError(
                f"❌ В ответе отсутствуют поля: {missing}.{context_msg}\n   Доступные: {list(data.keys())}"
            )

    @staticmethod
    def assert_list_not_empty(
        data_list: list[Any],
        list_name: str = "Список",
    ) -> None:
        """Проверка, что список не пустой."""
        context_msg = _get_context_message()
        if not isinstance(data_list, list):
            raise AssertionError(
                f"❌ {list_name} должен быть списком, получен {type(data_list).__name__}.{context_msg}"
            )
        if len(data_list) == 0:
            raise AssertionError(f"❌ {list_name} не должен быть пустым.{context_msg}")

    # --- Проверки стандартного формата ответа ---

    @staticmethod
    def assert_success_response(data: dict[str, Any]) -> None:
        """
        Проверка стандартного успешного ответа API:
        {'Status': 'Success', 'Code': 0, ...}
        """
        CustomAssertions.assert_fields_exist(data, ["Status", "Code"])
        context_msg = _get_context_message()
        if data["Status"] != "Success":
            raise AssertionError(f"❌ Ожидался Status='Success', получен '{data['Status']}'.{context_msg}")
        if data["Code"] != ResultCode.SUCCESS:
            raise AssertionError(f"❌ Ожидался Code=0, получен {data['Code']}.{context_msg}")

    # --- Проверки для конкретных сущностей ---

    @staticmethod
    def assert_order_status(
        order: dict[str, Any],
        expected_status: str,
    ) -> None:
        """Проверка статуса заказа."""
        context_msg = _get_context_message()
        if "Status" not in order:
            raise AssertionError(f"❌ В заказе отсутствует поле 'Status'.{context_msg}")
        if order["Status"] != expected_status:
            raise AssertionError(
                f"❌ Ожидался статус заказа '{expected_status}', получен '{order['Status']}'.{context_msg}"
            )

    @staticmethod
    def assert_block_success(data: dict[str, Any]) -> None:
        """Проверка успешного ответа блокировки средств."""
        context_msg = _get_context_message()
        CustomAssertions.assert_field_exists(data, "IsBlocked", bool)
        if data["IsBlocked"] is not True:
            raise AssertionError(f"❌ Ожидалось IsBlocked=True, получено {data['IsBlocked']}.{context_msg}")
        CustomAssertions.assert_field_exists(data, "TransactionUuid", str)
        CustomAssertions.assert_field_exists(data, "TariffBlockedSum", str)
        if not float(data["TariffBlockedSum"]) > 0:
            raise AssertionError(
                f"❌ Сумма блокировки должна быть > 0, получено {data['TariffBlockedSum']}.{context_msg}"
            )

    @staticmethod
    def assert_cancel_success(data: dict[str, Any]) -> None:
        """Проверка успешного ответа отмены заказа."""
        context_msg = _get_context_message()
        CustomAssertions.assert_field_exists(data, "Success", bool)
        if data["Success"] is not True:
            raise AssertionError(f"❌ Ожидалось Success=True при отмене, получено {data['Success']}.{context_msg}")
        CustomAssertions.assert_field_exists(data, "CancellationReason", str)
        if len(data["CancellationReason"]) > 250:
            raise AssertionError(
                f"❌ Длина CancellationReason должна быть ≤ 250, "
                f"получено {len(data['CancellationReason'])}.{context_msg}"
            )

    @staticmethod
    def assert_tariff_allowed(data: dict[str, Any]) -> None:
        """Проверка, что тариф разрешён к покупке (расчёт стоимости)."""
        context_msg = _get_context_message()

        is_allowed = data.get("IsAllowed") if "IsAllowed" in data else data.get("isAllowed")

        if is_allowed is None:
            raise AssertionError(
                f"❌ В ответе отсутствует поле IsAllowed/isAllowed.{context_msg}\n"
                f"   Доступные поля: {list(data.keys())}"
            )

        if is_allowed is not True:
            raise AssertionError(f"❌ Ожидалось IsAllowed=True, получено {is_allowed}.{context_msg}")

        # Проверка наличия суммы
        has_amount = "AvailableSupplierAmount" in data or "AvailibleSupplierAmount" in data
        if not has_amount:
            raise AssertionError(
                f"❌ В ответе отсутствует поле AvailableSupplierAmount/AvailibleSupplierAmount.{context_msg}\n"
                f"   Доступные поля: {list(data.keys())}"
            )
