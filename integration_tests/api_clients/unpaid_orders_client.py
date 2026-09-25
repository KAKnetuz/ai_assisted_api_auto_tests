"""
Клиент для работы со списком неоплаченных заказов.
"""

from typing import Any

import requests

from integration_tests.api_clients.base_api_client import BaseAPIClient
from integration_tests.config import endpoints


class UnpaidOrdersClient(BaseAPIClient):
    """Клиент для получения списка неоплаченных заказов."""

    def get_unpaid_orders(
        self,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Получение списка неоплаченных заказов (GET-запрос).

        Args:
            params: query-параметры (например, {'SupplierUuid': '...'}).
        """
        return self.get(endpoints.UNPAID_ORDERS, params=params, **kwargs)
