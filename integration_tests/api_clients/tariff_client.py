"""
Клиент для работы с тарифами:
- расчёт стоимости / проверка возможности покупки
- поиск тарифов по имени
"""

from typing import Any

import requests

from integration_tests.api_clients.base_api_client import BaseAPIClient
from integration_tests.config import endpoints
from integration_tests.config.endpoints import Platform


class TariffClient(BaseAPIClient):
    """Клиент для работы с тарифами."""

    def get_tariff_info(
        self,
        payload: dict[str, Any],
        endpoint: str = Platform.CORE,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Получение информации о тарифе / расчёт стоимости.

        Args:
            payload: тело запроса. Должно содержать:
                - SupplierUuid
                - Price
                - AccountNumber
                - Либо TariffId, либо TariffUniqueName
            endpoint: идентификатор платформы.
            **kwargs: дополнительные параметры requests.

        Returns:
            Объект requests.Response.

        Raises:
            ValueError: Если указан неизвестный endpoint.
        """
        url = endpoints.resolve(endpoints.TARIFF_INFO_ENDPOINTS, endpoint, "tariff info")
        return self.post(url, json=payload, **kwargs)

    def get_tariff_info_by_id(
        self,
        supplier_uuid: str,
        tariff_id: int | str,
        price: str = "100",
        account_number: str | None = None,
        endpoint: str = Platform.CORE,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Удобный метод: расчёт стоимости по TariffId.

        Args:
            supplier_uuid: UUID поставщика.
            tariff_id: ID тарифа.
            price: цена (строка).
            account_number: номер счёта (опционально).
            endpoint: идентификатор платформы.
            **kwargs: дополнительные параметры requests.

        Returns:
            Объект requests.Response.
        """
        payload: dict[str, Any] = {
            "SupplierUuid": supplier_uuid,
            "TariffId": tariff_id,
            "Price": price,
        }
        if account_number is not None:
            payload["AccountNumber"] = account_number
        return self.get_tariff_info(payload, endpoint=endpoint, **kwargs)

    def get_tariff_info_by_name(
        self,
        supplier_uuid: str,
        tariff_unique_name: str,
        price: str = "100",
        account_number: str | None = None,
        endpoint: str = Platform.CORE,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Удобный метод: расчёт стоимости по TariffUniqueName.

        Args:
            supplier_uuid: UUID поставщика.
            tariff_unique_name: уникальное имя тарифа.
            price: цена (строка).
            account_number: номер счёта (опционально).
            endpoint: идентификатор платформы.
            **kwargs: дополнительные параметры requests.

        Returns:
            Объект requests.Response.
        """
        payload: dict[str, Any] = {
            "SupplierUuid": supplier_uuid,
            "TariffUniqueName": tariff_unique_name,
            "Price": price,
        }
        if account_number is not None:
            payload["AccountNumber"] = account_number
        return self.get_tariff_info(payload, endpoint=endpoint, **kwargs)

    def search_tariffs(
        self,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> requests.Response:
        """
        Поиск тарифов по имени.

        Args:
            payload: тело запроса. Должно содержать:
                - SupplierUuid
                - TariffUniqueName (список строк)
                - Опционально: TariffId, TariffType
            **kwargs: дополнительные параметры requests.

        Returns:
            Объект requests.Response.
        """
        return self.post(endpoints.TARIFF_SEARCH, json=payload, **kwargs)

    def search_tariffs_by_params(
        self,
        supplier_uuid: str,
        tariff_unique_names: list[str],
        tariff_id: int | str | None = None,
        tariff_type: int | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Удобный метод: поиск тарифов с автоматическим формированием payload.

        Args:
            supplier_uuid: UUID поставщика.
            tariff_unique_names: список уникальных имён тарифов.
            tariff_id: ID тарифа (опционально).
            tariff_type: тип тарифа (опционально).
            **kwargs: дополнительные параметры requests.

        Returns:
            Объект requests.Response.
        """
        payload: dict[str, Any] = {
            "SupplierUuid": supplier_uuid,
            "TariffUniqueName": tariff_unique_names,
        }
        if tariff_id is not None:
            payload["TariffId"] = tariff_id
        if tariff_type is not None:
            payload["TariffType"] = tariff_type
        return self.search_tariffs(payload, **kwargs)
