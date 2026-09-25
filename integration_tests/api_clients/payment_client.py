"""
Клиент для работы с методом списания денежных средств (payment).
Поддерживает платформы platform_a и platform_b.
"""
from typing import Any

import requests

from integration_tests.api_clients.base_api_client import BaseAPIClient
from integration_tests.config import endpoints
from integration_tests.config.endpoints import Platform
from integration_tests.helpers.data_generators import DataGenerators


class PaymentClient(BaseAPIClient):
    """Клиент для метода payment (списание по заблокированным средствам)."""

    def payment(
        self,
        payload: dict[str, Any],
        endpoint: str = Platform.PLATFORM_A,
        **kwargs: Any,
    ) -> requests.Response:
        url = endpoints.resolve(endpoints.PAYMENT_ENDPOINTS, endpoint, "payment")
        self.logger.info(f"Payment [{endpoint}]: отправка запроса на {url}")
        self.logger.debug(f"Payment [{endpoint}] payload: {payload}")
        return self.post(url, json=payload, **kwargs)

    @staticmethod
    def build_payment_payload(
        procedure_number: str | None = None,
        procedure_uuid: str | None = None,
        payment_info: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        payload["ProcedureNumber"] = (
            procedure_number if procedure_number is not None else DataGenerators.generate_procedure_number()
        )
        payload["ProcedureUuid"] = procedure_uuid if procedure_uuid is not None else DataGenerators.generate_uuid()
        if payment_info is None:
            payload["PaymentInfo"] = [
                PaymentClient.build_payment_info_item(
                    supplier_uuid=DataGenerators.generate_uuid(),
                    price="1000",
                )
            ]
        else:
            payload["PaymentInfo"] = payment_info
        return payload

    @staticmethod
    def build_payment_info_item(
        supplier_uuid: str | None = None,
        price: str | None = None,
        account_number: str | None = None,
        account_tag: str | None = None,
    ) -> dict[str, Any]:
        item: dict[str, Any] = {}
        if supplier_uuid is not None:
            item["SupplierUuid"] = supplier_uuid
        if price is not None:
            item["Price"] = price
        if account_number is not None:
            item["AccountNumber"] = account_number
        if account_tag is not None:
            item["AccountTag"] = account_tag
        return item
