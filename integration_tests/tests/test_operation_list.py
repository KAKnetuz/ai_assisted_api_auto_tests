"""
Тесты списка операций по счёту.
"""

import pytest

from integration_tests.api_clients.operation_client import OperationClient
from integration_tests.helpers.assertions import CustomAssertions
from integration_tests.helpers.data_generators import DataGenerators


@pytest.mark.regression
class TestOperationList:
    """Тесты для получения списка операций."""

    def test_get_operations_with_valid_params(
        self,
        operation_client: OperationClient,
        supplier_uuid: str,
    ) -> None:
        """Позитивный тест: запрос с валидными параметрами."""
        # Увеличиваем диапазон до 365 дней, чтобы повысить шанс найти операции
        date_range = DataGenerators.generate_date_range(days_back=365)

        response = operation_client.get_operation_list_by_params(
            supplier_uuid=supplier_uuid,
            from_datetime=date_range["from"],
            to_datetime=date_range["to"],
            limit=100,
            offset=0,
            operation_types=[1],
        )

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_field_exists(data, "Operations", list)

        # Проверяем структуру только если список не пустой
        if len(data["Operations"]) > 0:
            first_op = data["Operations"][0]
            required_fields = [
                "Uuid",
                "Datetime",
                "Description",
                "BalanceBefore",
                "BalanceAfter",
                "TaxAmount",
                "Sum",
                "Type",
            ]
            CustomAssertions.assert_fields_exist(first_op, required_fields)

    def test_get_operations_limit_1(
        self,
        operation_client: OperationClient,
        supplier_uuid: str,
    ) -> None:
        """Позитивный тест: запрос с Limit=1."""
        date_range = DataGenerators.generate_date_range(days_back=365)

        response = operation_client.get_operation_list_by_params(
            supplier_uuid=supplier_uuid,
            from_datetime=date_range["from"],
            to_datetime=date_range["to"],
            limit=1,
            offset=0,
            operation_types=[1],
        )

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_field_exists(data, "Operations", list)

        # Если есть операции, проверяем что вернулась ровно 1
        if len(data["Operations"]) > 0:
            assert len(data["Operations"]) == 1, f"При Limit=1 ожидали 1 запись, получено {len(data['Operations'])}"

    def test_get_operations_missing_supplier(
        self,
        operation_client: OperationClient,
    ) -> None:
        """Негативный тест: отсутствие SupplierUuid."""
        date_range = DataGenerators.generate_date_range(days_back=90)
        payload = {
            "FromDatetime": date_range["from"],
            "ToDatetime": date_range["to"],
            "Limit": 100,
            "Offset": 0,
            "Type": [1],
        }

        response = operation_client.get_operation_list(payload)
        CustomAssertions.assert_status_code(response, [400, 422])

    def test_get_operations_invalid_supplier_format(
        self,
        operation_client: OperationClient,
    ) -> None:
        """Негативный тест: неверный формат SupplierUuid."""
        date_range = DataGenerators.generate_date_range(days_back=90)
        payload = {
            "SupplierUuid": "неправильный-uuid-123",
            "FromDatetime": date_range["from"],
            "ToDatetime": date_range["to"],
            "Limit": 100,
            "Offset": 0,
            "Type": [1],
        }

        response = operation_client.get_operation_list(payload)
        CustomAssertions.assert_status_code(response, [400, 422])
