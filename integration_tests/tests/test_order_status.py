"""Тесты статуса заказа (платформа core)."""

import pytest

from integration_tests.api_clients.order_client import OrderClient
from integration_tests.helpers.assertions import CustomAssertions


@pytest.mark.regression
class TestOrderStatus:

    def test_get_order_status_success(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        shared_order_data: dict,
    ) -> None:
        response = order_client.get_order_status_by_order_uuid(
            supplier_uuid=supplier_uuid,
            order_uuid=shared_order_data["order_uuid"],
        )

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_field_exists(data, "Orders", list)
        assert len(data["Orders"]) > 0

        first_order = data["Orders"][0]
        assert first_order["Status"] == "new"

    @pytest.mark.parametrize(
        "supplier_uuid_value,order_uuid_value,expected_status",
        [
            ("неправильный-uuid-123", "valid-uuid", [400, 422]),
            ("valid-uuid", "неправильный-uuid-123", [400, 422]),
            ("", "valid-uuid", [400, 422]),
            ("valid-uuid", "", 200),
        ],
        ids=["invalid_supplier", "invalid_order", "empty_supplier", "empty_order"],
    )
    def test_get_order_status_invalid_data(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        shared_order_data: dict,
        supplier_uuid_value: str,
        order_uuid_value: str,
        expected_status: int | list[int],
    ) -> None:
        actual_supplier = supplier_uuid if supplier_uuid_value == "valid-uuid" else supplier_uuid_value
        actual_order = shared_order_data["order_uuid"] if order_uuid_value == "valid-uuid" else order_uuid_value

        response = order_client.get_order_status_by_order_uuid(
            supplier_uuid=actual_supplier,
            order_uuid=actual_order,
        )

        CustomAssertions.assert_status_code(response, expected_status)

        if order_uuid_value == "" and supplier_uuid_value == "valid-uuid":
            data = CustomAssertions.assert_valid_json(response)
            CustomAssertions.assert_field_exists(data, "Orders", list)
