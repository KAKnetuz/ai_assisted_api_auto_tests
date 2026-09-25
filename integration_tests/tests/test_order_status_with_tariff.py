"""Тесты статуса заказа с данными тарифа (платформа platform_b)."""

import pytest

from integration_tests.api_clients.order_client import OrderClient
from integration_tests.helpers.assertions import CustomAssertions


@pytest.mark.regression
class TestOrderStatusWithTariff:

    def test_get_order_status_with_all_params(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        tariff_id: int,
        shared_order_data: dict,
    ) -> None:
        payload = {
            "SupplierUuid": supplier_uuid,
            "OrderUuid": shared_order_data["order_uuid"],
            "OrderStatus": ["new"],
            "TariffId": tariff_id,
        }

        response = order_client.get_order_status_with_tariff(payload)

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_field_exists(data, "Orders", list)
        assert len(data["Orders"]) > 0

        first_order = data["Orders"][0]
        assert first_order["OrderUuid"] == shared_order_data["order_uuid"]
        assert first_order["OrderStatus"] == "new"
        assert first_order["TariffId"] == tariff_id

    def test_get_order_status_without_order_status(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        tariff_id: int,
        shared_order_data: dict,
    ) -> None:
        payload = {
            "SupplierUuid": supplier_uuid,
            "OrderUuid": shared_order_data["order_uuid"],
            "TariffId": tariff_id,
        }

        response = order_client.get_order_status_with_tariff(payload)

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        assert len(data["Orders"]) > 0

    def test_get_order_status_only_supplier(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
    ) -> None:
        payload = {"SupplierUuid": supplier_uuid}

        response = order_client.get_order_status_with_tariff(payload)

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        assert len(data["Orders"]) > 0

    def test_get_order_status_missing_supplier(
        self,
        order_client: OrderClient,
        tariff_id: int,
        shared_order_data: dict,
    ) -> None:
        payload = {
            "OrderUuid": shared_order_data["order_uuid"],
            "OrderStatus": ["new"],
            "TariffId": tariff_id,
        }

        response = order_client.get_order_status_with_tariff(payload)

        CustomAssertions.assert_status_code(response, [400, 422])
