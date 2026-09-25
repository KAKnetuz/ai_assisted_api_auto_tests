"""
Тесты поиска тарифов по имени.
"""

import pytest

from integration_tests.api_clients.tariff_client import TariffClient
from integration_tests.helpers.assertions import CustomAssertions


@pytest.mark.regression
class TestTariffSearch:
    """Тесты для поиска тарифов по имени."""

    def test_get_tariffs_with_all_params(
        self,
        tariff_client: TariffClient,
        supplier_uuid: str,
        tariff_id: int,
        tariff_type: int,
        tariff_unique_name: str,
    ) -> None:
        """Позитивный тест: запрос со всеми параметрами."""
        response = tariff_client.search_tariffs_by_params(
            supplier_uuid=supplier_uuid,
            tariff_unique_names=[tariff_unique_name],
            tariff_id=tariff_id,
            tariff_type=tariff_type,
        )

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_field_exists(data, "Tariffs", list)
        assert len(data["Tariffs"]) > 0

        first_tariff = data["Tariffs"][0]
        assert first_tariff["TariffId"] == tariff_id
        assert first_tariff["TariffType"] == tariff_type
        assert first_tariff["TariffUniqueName"] == tariff_unique_name

    def test_get_tariffs_only_supplier(
        self,
        tariff_client: TariffClient,
        supplier_uuid: str,
    ) -> None:
        """Позитивный тест: запрос только с SupplierUuid."""
        response = tariff_client.search_tariffs_by_params(
            supplier_uuid=supplier_uuid,
            tariff_unique_names=[],
        )

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        assert len(data["Tariffs"]) > 0

    def test_get_tariffs_supplier_and_id(
        self,
        tariff_client: TariffClient,
        supplier_uuid: str,
        tariff_id: int,
    ) -> None:
        """Позитивный тест: запрос с SupplierUuid и TariffId."""
        response = tariff_client.search_tariffs_by_params(
            supplier_uuid=supplier_uuid,
            tariff_unique_names=[],
            tariff_id=tariff_id,
        )

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        assert len(data["Tariffs"]) > 0
        assert data["Tariffs"][0]["TariffId"] == tariff_id

    def test_get_tariffs_missing_supplier(
        self,
        tariff_client: TariffClient,
        tariff_id: int,
        tariff_type: int,
        tariff_unique_name: str,
    ) -> None:
        """Негативный тест: отсутствие SupplierUuid."""
        payload = {
            "TariffId": tariff_id,
            "TariffType": tariff_type,
            "TariffUniqueName": [tariff_unique_name],
        }

        response = tariff_client.search_tariffs(payload)
        CustomAssertions.assert_status_code(response, [400, 422])

    def test_get_tariffs_invalid_supplier_format(
        self,
        tariff_client: TariffClient,
        tariff_id: int,
        tariff_type: int,
        tariff_unique_name: str,
    ) -> None:
        """Негативный тест: неверный формат SupplierUuid."""
        payload = {
            "SupplierUuid": "неправильный-uuid-123",
            "TariffId": tariff_id,
            "TariffType": tariff_type,
            "TariffUniqueName": [tariff_unique_name],
        }

        response = tariff_client.search_tariffs(payload)
        CustomAssertions.assert_status_code(response, [400, 422])
