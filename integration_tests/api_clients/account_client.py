"""
Клиент для получения информации о лицевом счёте.
Поддерживает платформы core и platform_b.
"""

from typing import Any

import requests

from integration_tests.api_clients.base_api_client import BaseAPIClient
from integration_tests.config import endpoints
from integration_tests.config.endpoints import Platform


class AccountClient(BaseAPIClient):
    """Клиент для получения информации о лицевом счёте контрагента."""

    def get_account_info(
        self,
        payload: dict[str, Any],
        endpoint: str = Platform.CORE,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Запрос информации о счёте по готовому payload.

        Args:
            payload: тело запроса.
            endpoint: идентификатор платформы.
            **kwargs: дополнительные параметры requests.

        Returns:
            Объект requests.Response.

        Raises:
            ValueError: Если указан неизвестный endpoint.
        """
        url = endpoints.resolve(endpoints.ACCOUNT_INFO_ENDPOINTS, endpoint, "account info")
        return self.post(url, json=payload, **kwargs)

    def get_account_info_by_params(
        self,
        supplier_uuid: str,
        account_number: str | None = None,
        account_tag: str | None = None,
        currency: int | None = None,
        endpoint: str = Platform.CORE,
        **kwargs: Any,
    ) -> requests.Response:
        """Удобный метод: формирует payload и запрашивает информацию о счёте."""
        payload: dict[str, Any] = {"SupplierUuid": supplier_uuid}

        if account_number is not None:
            payload["AccountNumber"] = account_number
        if account_tag is not None:
            payload["AccountTag"] = account_tag

        # Обработка различий в именах ключей валюты между платформами
        if currency is not None:
            if endpoint == Platform.PLATFORM_B:
                payload["Currency"] = currency
            else:
                payload["CurrencyCode"] = currency

        return self.get_account_info(payload, endpoint=endpoint, **kwargs)
