"""
Тесты списка неоплаченных заказов.
"""

import pytest

from integration_tests.api_clients.unpaid_orders_client import UnpaidOrdersClient
from integration_tests.helpers.assertions import CustomAssertions


@pytest.mark.regression
class TestUnpaidOrders:
    """Тесты для получения списка неоплаченных заказов."""

    def test_get_unpaid_orders_success(
        self,
        unpaid_orders_client: UnpaidOrdersClient,
        supplier_uuid: str,
    ) -> None:
        """
        Позитивный тест: запрос списка неоплаченных заказов.

        Примечание: список может быть пустым, если все заказы оплачены.
        Мы проверяем только корректность структуры ответа.
        """
        response = unpaid_orders_client.get_unpaid_orders(params={"SupplierUuid": supplier_uuid})

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_success_response(data)

        CustomAssertions.assert_field_exists(data, "Data", list)

        # Проверяем структуру только если есть неоплаченные заказы
        if len(data["Data"]) > 0:
            first_item = data["Data"][0]
            CustomAssertions.assert_fields_exist(first_item, ["InvoiceId", "OrderId"])

    @pytest.mark.parametrize("supplier_uuid_value", ["", "неправильный-uuid-123"], ids=["empty_uuid", "invalid_format"])
    def test_get_unpaid_orders_invalid_supplier_uuid(
        self,
        unpaid_orders_client: UnpaidOrdersClient,
        supplier_uuid_value: str,
    ) -> None:
        """Негативный тест: невалидный SupplierUuid."""
        response = unpaid_orders_client.get_unpaid_orders(params={"SupplierUuid": supplier_uuid_value})
        CustomAssertions.assert_status_code(response, [400, 422])
