"""
Клиент для получения количества контрагентов.
"""

from typing import Any

import requests

from integration_tests.api_clients.base_api_client import BaseAPIClient
from integration_tests.config import endpoints


class CounterpartyClient(BaseAPIClient):
    """Клиент для получения количества контрагентов."""

    def get_counterparty_count(
        self,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Получение количества контрагентов (GET-запрос).

        Args:
            params: query-параметры (например, {'Type': 1}).
        """
        return self.get(endpoints.COUNTERPARTY_COUNT, params=params, **kwargs)

    def get_counterparty_count_by_type(
        self,
        counterparty_type: int,
        **kwargs: Any,
    ) -> requests.Response:
        """Удобный метод: получение количества по типу."""
        return self.get_counterparty_count(params={"Type": counterparty_type}, **kwargs)
