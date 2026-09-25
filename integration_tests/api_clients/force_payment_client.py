from typing import Any

from requests import Response

from integration_tests.api_clients.base_api_client import BaseAPIClient
from integration_tests.config import endpoints
from integration_tests.config.constants import AccountTag


class ForcePaymentClient(BaseAPIClient):
    """Клиент для принудительной оплаты (создание, оплата и закрытие заказа за один вызов)."""

    def force_payment(self, payload: dict[str, Any]) -> Response:
        """
        Выполняет запрос принудительной оплаты с переданным телом.

        Args:
            payload: тело запроса.

        Returns:
            Объект Response.
        """
        self.logger.info("ForcePayment: отправка запроса на %s", endpoints.FORCE_PAYMENT)
        return self.post(endpoints.FORCE_PAYMENT, json=payload)

    def force_payment_with_params(
        self,
        supplier_uuid: str,
        price: str,
        procedure_number: str,
        procedure_uuid: str,
        tariff_unique_name: str | None = None,
        account_number: str | None = None,
        account_tag: str | None = AccountTag.MAIN,
        promo_code: list | None = None,
    ) -> Response:
        """
        Выполняет запрос принудительной оплаты, собирая тело из именованных аргументов.

        Args:
            supplier_uuid: UUID контрагента.
            price: цена (строка).
            procedure_number: номер процедуры.
            procedure_uuid: UUID процедуры.
            tariff_unique_name: уникальное имя тарифа (опционально).
            account_number: номер счёта (опционально).
            account_tag: тег счёта (по умолчанию AccountTag.MAIN).
            promo_code: список промокодов (опционально).

        Returns:
            Объект Response.
        """
        payload: dict[str, Any] = {
            "SupplierUuid": supplier_uuid,
            "Price": price,
            "ProcedureNumber": procedure_number,
            "ProcedureUuid": procedure_uuid,
        }

        if tariff_unique_name is not None:
            payload["TariffUniqueName"] = tariff_unique_name
        if account_number is not None:
            payload["AccountNumber"] = account_number
        if account_tag is not None:
            payload["AccountTag"] = account_tag
        if promo_code is not None:
            payload["PromoCode"] = promo_code

        self.logger.debug("ForcePayment: собран payload = %s", payload)
        return self.force_payment(payload)
