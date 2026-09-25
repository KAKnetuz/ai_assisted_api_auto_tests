"""
Тесты получения количества контрагентов.
"""

import pytest

from integration_tests.api_clients.counterparty_client import CounterpartyClient
from integration_tests.helpers.assertions import CustomAssertions


@pytest.mark.smoke
class TestCounterpartyCount:
    """Тесты для получения количества контрагентов."""

    def test_get_counterparty_count_success(
        self,
        counterparty_client: CounterpartyClient,
    ) -> None:
        """
        Позитивный тест: получение количества контрагентов в системе.
        """
        # Act (теперь это GET без параметров)
        response = counterparty_client.get_counterparty_count()

        # Assert
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)

        CustomAssertions.assert_field_exists(data, "Count", str)
        count_value = data["Count"]
        assert count_value.isdigit(), f"Count должен быть числом, получено '{count_value}'"
        assert int(count_value) >= 0, f"Count не может быть отрицательным: {count_value}"
