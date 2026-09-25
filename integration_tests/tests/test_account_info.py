"""Тесты информации о лицевом счёте (платформы core и platform_b)."""

import uuid
from typing import Any

import pytest

from integration_tests.config.constants import (
    ACCOUNT_INFO_PLATFORMS,
    CURRENCY_RUB,
    CURRENCY_USD,
    ErrorText,
    ResultCode,
)
from integration_tests.config.endpoints import Platform
from integration_tests.helpers.assertions import CustomAssertions


def normalize_account_info_response(data: dict[str, Any], endpoint: str) -> list[dict[str, Any]]:
    if endpoint == Platform.CORE:
        if "Data" not in data:
            pytest.fail(f"Endpoint должен вернуть поле 'Data'. Получено: {data}")
        return data["Data"]
    else:
        if isinstance(data, dict) and "Amount" in data:
            return [data]
        elif isinstance(data, list):
            return data
        else:
            pytest.fail(f"Неожиданная структура ответа: {data}")


def normalize_currency_field(account_data: dict[str, Any], endpoint: str) -> int:
    if endpoint == Platform.CORE:
        return account_data.get("CurrencyCode")
    else:
        return account_data.get("Currency")


def get_required_fields(endpoint: str) -> list[str]:
    if endpoint == Platform.CORE:
        return [
            "Amount",
            "NotBlockedAmount",
            "BlockedAmount",
            "ReservedToUnlockAmount",
            "AccountNumber",
            "AccountRefillTax",
            "CurrencyCode",
            "AccountTag",
        ]
    else:
        return [
            "Amount",
            "NotBlockedAmount",
            "BlockedAmount",
            "ReservedToUnlockAmount",
            "AccountNumber",
            "AccountRefillTax",
            "Currency",
        ]


@pytest.mark.parametrize("endpoint", ACCOUNT_INFO_PLATFORMS, ids=str)
class TestAccountInfo:

    @pytest.mark.smoke
    def test_pos_account_info_success(self, account_client, account_info: dict[str, Any], endpoint: str) -> None:
        payload = account_info.copy()
        response = account_client.get_account_info(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        accounts = normalize_account_info_response(data, endpoint)
        assert len(accounts) == 1, f"Ожидаем 1 элемент, получено {len(accounts)}"
        account_data = accounts[0]
        required_fields = get_required_fields(endpoint)
        CustomAssertions.assert_fields_exist(account_data, required_fields)
        assert account_data["AccountNumber"] == account_info["AccountNumber"]
        if "AccountTag" in account_data:
            assert account_data["AccountTag"] == account_info["AccountTag"]
        currency = normalize_currency_field(account_data, endpoint)
        assert currency == account_info["CurrencyCode"]

    @pytest.mark.regression
    def test_pos_account_info_by_supplier_only(
        self, account_client, account_info: dict[str, Any], endpoint: str
    ) -> None:
        payload = {"SupplierUuid": account_info["SupplierUuid"]}
        response = account_client.get_account_info(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        accounts = normalize_account_info_response(data, endpoint)
        assert len(accounts) >= 1
        required_fields = get_required_fields(endpoint)
        for account_data in accounts:
            CustomAssertions.assert_fields_exist(account_data, required_fields)

    @pytest.mark.regression
    def test_pos_account_info_supplier_and_currency(
        self, account_client, account_info: dict[str, Any], endpoint: str
    ) -> None:
        payload = {
            "SupplierUuid": account_info["SupplierUuid"],
            "Currency" if endpoint == Platform.PLATFORM_B else "CurrencyCode": CURRENCY_RUB,
        }
        response = account_client.get_account_info(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        accounts = normalize_account_info_response(data, endpoint)
        assert len(accounts) >= 1

    @pytest.mark.regression
    def test_pos_account_info_amounts_non_negative(
        self, account_client, account_info: dict[str, Any], endpoint: str
    ) -> None:
        payload = account_info.copy()
        response = account_client.get_account_info(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        accounts = normalize_account_info_response(data, endpoint)
        assert len(accounts) >= 1
        account_data = accounts[0]
        amount_fields = ["Amount", "NotBlockedAmount", "BlockedAmount"]
        for field in amount_fields:
            value = account_data.get(field)
            if value is not None:
                try:
                    numeric_value = float(value)
                    assert numeric_value >= 0, f"{field} отрицательный: {numeric_value}"
                except (ValueError, TypeError):
                    pass


@pytest.mark.parametrize("endpoint", ACCOUNT_INFO_PLATFORMS, ids=str)
class TestAccountInfoNegative:

    @pytest.mark.regression
    def test_neg_account_info_missing_supplier_uuid(
        self, account_client, account_info: dict[str, Any], endpoint: str
    ) -> None:
        payload = {"AccountNumber": account_info["AccountNumber"], "AccountTag": account_info["AccountTag"]}
        response = account_client.get_account_info(payload, endpoint=endpoint)
        assert response.status_code in [400, 422]

    @pytest.mark.regression
    def test_neg_account_info_empty_supplier_uuid(
        self, account_client, account_info: dict[str, Any], endpoint: str
    ) -> None:
        payload = {"SupplierUuid": "", "AccountNumber": account_info["AccountNumber"]}
        response = account_client.get_account_info(payload, endpoint=endpoint)
        assert response.status_code in [400, 422]

    @pytest.mark.regression
    def test_neg_account_info_invalid_supplier_uuid_format(
        self, account_client, account_info: dict[str, Any], endpoint: str
    ) -> None:
        payload = {"SupplierUuid": "not-a-uuid", "AccountNumber": account_info["AccountNumber"]}
        response = account_client.get_account_info(payload, endpoint=endpoint)
        assert response.status_code in [400, 422]

    @pytest.mark.regression
    def test_neg_account_info_nonexistent_supplier_uuid(self, account_client, endpoint: str) -> None:
        nonexistent_uuid = str(uuid.uuid4())
        payload = {"SupplierUuid": nonexistent_uuid}
        response = account_client.get_account_info(payload, endpoint=endpoint)
        assert response.status_code in [400, 422]

    @pytest.mark.regression
    @pytest.mark.parametrize(
        "currency_value", [999, -1, "RUB", {}], ids=["invalid_code", "negative", "string", "object"]
    )
    def test_neg_account_info_invalid_currency_enum(
        self, account_client, account_info: dict[str, Any], endpoint: str, currency_value: Any
    ) -> None:
        currency_field = "Currency" if endpoint == Platform.PLATFORM_B else "CurrencyCode"
        payload = {"SupplierUuid": account_info["SupplierUuid"], currency_field: currency_value}
        response = account_client.get_account_info(payload, endpoint=endpoint)
        assert response.status_code == 400

    @pytest.mark.regression
    def test_neg_account_info_unsupported_currency_for_supplier(
        self, account_client, account_info: dict[str, Any], endpoint: str
    ) -> None:
        currency_field = "Currency" if endpoint == Platform.PLATFORM_B else "CurrencyCode"
        payload = {
            "SupplierUuid": account_info["SupplierUuid"],
            currency_field: CURRENCY_USD,
        }
        response = account_client.get_account_info(payload, endpoint=endpoint)
        assert response.status_code == 422
        data = CustomAssertions.assert_valid_json(response)
        code_str = str(data.get("Code", ""))
        message = data.get("Message", "")
        assert code_str == str(ResultCode.CURRENCY_NOT_SUPPORTED.value) or ErrorText.CURRENCY in message.lower()

    @pytest.mark.regression
    def test_neg_account_info_empty_account_number(
        self, account_client, account_info: dict[str, Any], endpoint: str
    ) -> None:
        payload = {"SupplierUuid": account_info["SupplierUuid"], "AccountNumber": ""}
        response = account_client.get_account_info(payload, endpoint=endpoint)
        assert response.status_code in [400, 422]

    @pytest.mark.regression
    def test_neg_account_info_nonexistent_account_number(
        self, account_client, account_info: dict[str, Any], endpoint: str
    ) -> None:
        valid_number = account_info["AccountNumber"]
        parts = valid_number.rsplit("-", 1)
        if len(parts) == 2:
            nonexistent_number = f"{parts[0]}-999"
        else:
            nonexistent_number = f"{valid_number}-999"
        payload = {"SupplierUuid": account_info["SupplierUuid"], "AccountNumber": nonexistent_number}
        response = account_client.get_account_info(payload, endpoint=endpoint)
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = CustomAssertions.assert_valid_json(response)
            accounts = normalize_account_info_response(data, endpoint)
            assert len(accounts) == 0
