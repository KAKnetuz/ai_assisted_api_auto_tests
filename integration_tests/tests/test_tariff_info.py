"""
Тесты расчёта стоимости по тарифу (платформа core).
"""

import pytest

from integration_tests.api_clients.tariff_client import TariffClient
from integration_tests.helpers.assertions import CustomAssertions


@pytest.mark.smoke
class TestTariffInfo:
    """Тесты для получения информации о тарифе."""

    # ==========================================
    # ПОЗИТИВНЫЕ ТЕСТЫ: Основной тариф
    # ==========================================

    def test_tariff_info_with_unique_name(
        self,
        tariff_client: TariffClient,
        supplier_uuid: str,
        account_number: str,
        tariff_unique_name: str,
    ) -> None:
        """Позитивный тест: расчёт стоимости по TariffUniqueName (основной тариф)."""
        response = tariff_client.get_tariff_info_by_name(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_unique_name,
            price="100",
            account_number=account_number,
        )

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_tariff_allowed(data)

    def test_tariff_info_with_id(
        self,
        tariff_client: TariffClient,
        supplier_uuid: str,
        account_number: str,
        tariff_id: int,
    ) -> None:
        """Позитивный тест: расчёт стоимости по TariffId (основной тариф)."""
        response = tariff_client.get_tariff_info_by_id(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_id,
            price="200",
            account_number=account_number,
        )

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_tariff_allowed(data)

    # ==========================================
    # ПОЗИТИВНЫЕ ТЕСТЫ: Тариф со шкалой
    # ==========================================

    def test_tariff_info_scale_with_unique_name(
        self,
        tariff_client: TariffClient,
        supplier_uuid: str,
        account_number: str,
        tariff_scale_unique_name: str,
    ) -> None:
        """
        Позитивный тест: расчёт стоимости по тарифу со шкалой (TariffUniqueName).
        Цена "150" попадает во вторую ступень шкалы.
        """
        response = tariff_client.get_tariff_info_by_name(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            price="150",
            account_number=account_number,
        )

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_tariff_allowed(data)

    def test_tariff_info_scale_with_id(
        self,
        tariff_client: TariffClient,
        supplier_uuid: str,
        account_number: str,
        tariff_scale_id: int,
    ) -> None:
        """
        Позитивный тест: расчёт стоимости по тарифу со шкалой (TariffId).
        Цена "150" попадает во вторую ступень шкалы.
        """
        response = tariff_client.get_tariff_info_by_id(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_scale_id,
            price="150",
            account_number=account_number,
        )

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_tariff_allowed(data)

    # ==========================================
    # НЕГАТИВНЫЕ ТЕСТЫ
    # ==========================================

    def test_tariff_info_missing_supplier(
        self,
        tariff_client: TariffClient,
        account_number: str,
        tariff_unique_name: str,
    ) -> None:
        """Негативный тест: отсутствие SupplierUuid."""
        payload = {
            "TariffUniqueName": tariff_unique_name,
            "Price": "100",
            "AccountNumber": account_number,
        }

        response = tariff_client.get_tariff_info(payload)
        CustomAssertions.assert_status_code(response, [400, 422])

    def test_tariff_info_invalid_supplier_format(
        self,
        tariff_client: TariffClient,
        account_number: str,
        tariff_unique_name: str,
    ) -> None:
        """Негативный тест: неверный формат SupplierUuid."""
        payload = {
            "SupplierUuid": "неправильный-uuid-123",
            "TariffUniqueName": tariff_unique_name,
            "Price": "100",
            "AccountNumber": account_number,
        }

        response = tariff_client.get_tariff_info(payload)
        CustomAssertions.assert_status_code(response, [400, 422])
