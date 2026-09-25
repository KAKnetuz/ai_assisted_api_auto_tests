"""
Клиент для работы со списком операций по счёту.
"""

from typing import Any

import requests

from integration_tests.api_clients.base_api_client import BaseAPIClient
from integration_tests.config import endpoints
from integration_tests.helpers.data_generators import DataGenerators


class OperationClient(BaseAPIClient):
    """Клиент для получения списка операций контрагента."""

    def get_operation_list(
        self,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> requests.Response:
        """Получение списка операций по готовому payload."""
        return self.post(endpoints.OPERATION_LIST, json=payload, **kwargs)

    def get_operation_list_by_params(
        self,
        supplier_uuid: str,
        from_datetime: str | None = None,
        to_datetime: str | None = None,
        limit: int = 100,
        offset: int = 0,
        operation_types: list[int] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Удобный метод: получение списка операций с автоматическим формированием payload.

        Args:
            supplier_uuid: UUID поставщика.
            from_datetime: начало диапазона (ISO 8601).
            to_datetime: конец диапазона (ISO 8601).
            limit: лимит записей.
            offset: смещение.
            operation_types: список типов операций.
        """
        payload = DataGenerators.build_operation_list_payload(
            supplier_uuid=supplier_uuid,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            limit=limit,
            offset=offset,
            operation_types=operation_types,
        )
        return self.get_operation_list(payload, **kwargs)
