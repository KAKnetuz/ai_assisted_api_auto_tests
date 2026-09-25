"""
Клиент для работы с заказами:
- создание
- отмена
- проверка статуса
- получение списка заказов
"""
from typing import Any

import requests

from integration_tests.api_clients.base_api_client import BaseAPIClient
from integration_tests.config import endpoints
from integration_tests.config.endpoints import Platform
from integration_tests.helpers.data_generators import DataGenerators


class OrderClient(BaseAPIClient):

    def create_order(
        self,
        payload: dict[str, Any],
        endpoint: str = Platform.CORE,
        **kwargs: Any,
    ) -> requests.Response:
        url = endpoints.resolve(endpoints.ORDER_CREATE_ENDPOINTS, endpoint, "order create")
        return self.post(url, json=payload, **kwargs)

    def create_order_with_params(
        self,
        supplier_uuid: str,
        tariff_id: int | str,
        price: str = "100",
        procedure_number: str | None = None,
        procedure_uuid: str | None = None,
        account_number: str | None = None,
        endpoint: str = Platform.CORE,
        **kwargs: Any,
    ) -> requests.Response:
        payload = DataGenerators.build_order_create_payload(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_id,
            price=price,
            procedure_number=procedure_number,
            procedure_uuid=procedure_uuid,
            account_number=account_number,
        )
        return self.create_order(payload, endpoint=endpoint, **kwargs)

    def get_order_status(
        self,
        payload: dict[str, Any],
        endpoint: str = Platform.CORE,
        **kwargs: Any,
    ) -> requests.Response:
        url = endpoints.resolve(endpoints.ORDER_STATUS_ENDPOINTS, endpoint, "order status")
        return self.post(url, json=payload, **kwargs)

    def get_order_status_by_order_uuid(
        self,
        supplier_uuid: str,
        order_uuid: str,
        endpoint: str = Platform.CORE,
        **kwargs: Any,
    ) -> requests.Response:
        payload = DataGenerators.build_order_status_payload(
            supplier_uuid=supplier_uuid,
            order_uuid=order_uuid,
        )
        return self.get_order_status(payload, endpoint=endpoint, **kwargs)

    def get_order_list(
        self,
        payload: dict[str, Any],
        endpoint: str = Platform.CORE,
        **kwargs: Any,
    ) -> requests.Response:
        url = endpoints.resolve(endpoints.ORDER_LIST_ENDPOINTS, endpoint, "order list")
        return self.post(url, json=payload, **kwargs)

    def get_order_status_with_tariff(
        self,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> requests.Response:
        return self.post(endpoints.ORDER_STATUS_WITH_TARIFF, json=payload, **kwargs)

    def cancel_order(
        self,
        payload: dict[str, str],
        **kwargs: Any,
    ) -> requests.Response:
        return self.post(endpoints.ORDER_CANCEL, json=payload, **kwargs)

    def cancel_order_by_uuid(
        self,
        order_uuid: str,
        supplier_uuid: str,
        reason: str = "Тестовая отмена заказа.",
        **kwargs: Any,
    ) -> requests.Response:
        payload = DataGenerators.build_order_cancel_payload(
            order_uuid=order_uuid,
            supplier_uuid=supplier_uuid,
            reason=reason,
        )
        return self.cancel_order(payload, **kwargs)
