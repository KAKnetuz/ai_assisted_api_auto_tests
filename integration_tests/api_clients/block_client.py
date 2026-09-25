"""
Клиент для работы с блокировкой и разблокировкой средств.

Блокировка доступна на платформах platform_a и platform_b,
разблокировка — через общий эндпоинт модуля core.
"""
from typing import Any

import requests

from integration_tests.api_clients.base_api_client import BaseAPIClient
from integration_tests.config import endpoints
from integration_tests.config.constants import AccountTag
from integration_tests.config.endpoints import Platform
from integration_tests.helpers.data_generators import DataGenerators


class BlockClient(BaseAPIClient):
    """Клиент для операций блокировки и разблокировки средств."""

    def block(
        self,
        payload: dict[str, Any],
        endpoint: str = Platform.PLATFORM_A,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Блокировка средств по готовому payload.

        Args:
            payload: Тело запроса.
            endpoint: Идентификатор платформы.
            **kwargs: Дополнительные аргументы для requests.

        Returns:
            Объект Response.

        Raises:
            ValueError: Если указан неизвестный endpoint.
        """
        url = endpoints.resolve(endpoints.BLOCK_ENDPOINTS, endpoint, "block")
        return self.post(url, json=payload, **kwargs)

    def unblock(
        self,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> requests.Response:
        """
        Разблокировка средств по готовому payload.

        Args:
            payload: Тело запроса разблокировки.
                Ожидаемая структура:
                {
                    "ProcedureUuid": "uuid-строка",
                    "SupplierUuid": "uuid-строка"
                }
            **kwargs: Дополнительные аргументы для requests.

        Returns:
            Объект Response.
        """
        return self.post(endpoints.FUNDS_UNBLOCK, json=payload, **kwargs)

    def block_with_params(
        self,
        supplier_uuid: str,
        account_number: str,
        tariff_unique_name: str,
        price: str = "100",
        procedure_number: str | None = None,
        procedure_uuid: str | None = None,
        account_tag: str = AccountTag.MAIN,
        endpoint: str = Platform.PLATFORM_A,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Удобный метод: блокировка средств с автоматическим формированием payload.

        Args:
            supplier_uuid: UUID контрагента.
            account_number: Номер счёта.
            tariff_unique_name: Уникальное имя тарифа.
            price: Сумма блокировки.
            procedure_number: Номер процедуры (генерируется автоматически, если None).
            procedure_uuid: UUID процедуры (генерируется автоматически, если None).
            account_tag: Тег счёта.
            endpoint: Идентификатор платформы.
            **kwargs: Дополнительные аргументы для requests.

        Returns:
            requests.Response с TransactionUuid, IsBlocked, TariffBlockedSum.
        """
        payload = DataGenerators.build_block_payload(
            supplier_uuid=supplier_uuid,
            account_number=account_number,
            tariff_unique_name=tariff_unique_name,
            price=price,
            procedure_number=procedure_number,
            procedure_uuid=procedure_uuid,
            account_tag=account_tag,
        )
        return self.block(payload, endpoint=endpoint, **kwargs)
