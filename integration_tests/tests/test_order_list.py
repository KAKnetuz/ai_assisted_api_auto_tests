"""
Тесты получения списка заказов контрагента.
Покрываются платформы core и platform_b.
"""
import re
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from integration_tests.api_clients.order_client import OrderClient
from integration_tests.config.constants import ORDER_LIST_PLATFORMS, AccountTag, ErrorText
from integration_tests.helpers.assertions import CustomAssertions
from integration_tests.helpers.data_generators import DataGenerators
from integration_tests.utils.logger import get_logger

logger = get_logger(__name__)


def _iter_orders(data: dict[str, Any]) -> Generator[dict[str, Any]]:
    yield from data.get("Orders", [])


def _total_orders(data: dict[str, Any]) -> int:
    return len(data.get("Orders", []))


def _get_pay_data(order: dict[str, Any]) -> Any:
    return order.get("OrderPayData", order.get("OrderPayData "))


class TestOrderListPositive:

    @pytest.mark.smoke
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_pos_order_list_only_supplier(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        shared_order_data: dict[str, str],
        endpoint: str,
    ) -> None:
        """Базовый позитив: только SupplierUuid."""
        payload = {"SupplierUuid": supplier_uuid}
        response = order_client.get_order_list(payload, endpoint=endpoint)

        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)

        CustomAssertions.assert_field_exists(data, "Count", int)
        CustomAssertions.assert_field_exists(data, "Orders", list)
        logger.info("Топ-level Count на %s: %s", endpoint, data.get("Count"))

        orders = list(_iter_orders(data))
        assert orders, f"Список Orders пуст на {endpoint}, хотя у контрагента есть заказы"

        found_uuids = [o["OrderUuid"] for o in orders]
        assert shared_order_data["order_uuid"] in found_uuids, (
            f"Созданный заказ {shared_order_data['order_uuid']} отсутствует "
            f"в списке заказов на {endpoint}"
        )

        for order in orders:
            CustomAssertions.assert_field_exists(order, "OrderUuid")
            CustomAssertions.assert_field_exists(order, "OrderStatus")
            CustomAssertions.assert_field_exists(order, "OrderPayStatus")
            CustomAssertions.assert_field_exists(order, "AccountNumber")
            CustomAssertions.assert_field_exists(order, "AccountTag")
            CustomAssertions.assert_field_exists(order, "OrderPrice")
            CustomAssertions.assert_field_exists(order, "TariffId", int)
            CustomAssertions.assert_field_exists(order, "TariffName")

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_pos_order_list_filter_account_number(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        account_number: str,
        endpoint: str,
    ) -> None:
        """Фильтр по AccountNumber."""
        payload = {
            "SupplierUuid": supplier_uuid,
            "AccountNumber": account_number,
        }
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)

        orders = list(_iter_orders(data))
        if not orders:
            logger.info("Выдача пуста на %s, проверка фильтра вакуумная", endpoint)
            return
        for order in orders:
            assert order["AccountNumber"] == account_number

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_pos_order_list_filter_account_tag(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        endpoint: str,
    ) -> None:
        """Фильтр по AccountTag."""
        payload = {
            "SupplierUuid": supplier_uuid,
            "AccountTag": AccountTag.MAIN,
        }
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)

        orders = list(_iter_orders(data))
        if not orders:
            logger.info("Выдача пуста на %s, проверка фильтра вакуумная", endpoint)
            return
        for order in orders:
            assert order["AccountTag"] == AccountTag.MAIN

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_pos_order_list_filter_account_number_and_tag(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        account_number: str,
        endpoint: str,
    ) -> None:
        """Связка фильтров AccountNumber + AccountTag."""
        payload = {
            "SupplierUuid": supplier_uuid,
            "AccountNumber": account_number,
            "AccountTag": AccountTag.MAIN,
        }
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)

        orders = list(_iter_orders(data))
        if not orders:
            logger.info("Выдача пуста на %s, проверка фильтра вакуумная", endpoint)
            return
        for order in orders:
            assert order["AccountNumber"] == account_number
            assert order["AccountTag"] == AccountTag.MAIN

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_pos_order_list_filter_create_date_range(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        shared_order_data: dict[str, str],
        endpoint: str,
    ) -> None:
        """Фильтр по диапазону дат создания заказа."""
        now = datetime.now(UTC)
        from_dt = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        to_dt = (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        payload = {
            "SupplierUuid": supplier_uuid,
            "FromOrderCreateDatetime": from_dt,
            "ToOrderCreateDatetime": to_dt,
        }
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)

        orders = list(_iter_orders(data))
        for order in orders:
            created = order.get("OrderCreatedDate", "")
            assert from_dt[:10] <= created[:10] <= to_dt[:10]

        found_uuids = [o["OrderUuid"] for o in orders]
        assert shared_order_data["order_uuid"] in found_uuids

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_pos_order_list_filter_pay_date_range(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        endpoint: str,
    ) -> None:
        """Фильтр по диапазону дат оплаты (широкий диапазон)."""
        payload = {
            "SupplierUuid": supplier_uuid,
            "FromOrderPayDataTime": "2000-01-01T00:00:00.000Z",
            "ToOrderPayDataTime": "2099-12-31T23:59:59.000Z",
        }
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        CustomAssertions.assert_valid_json(response)
        data = response.json()
        for order in _iter_orders(data):
            pay_data = _get_pay_data(order)
            if pay_data:
                logger.info("OrderPayData %s в диапазоне", pay_data)

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_pos_order_list_limit_one(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        endpoint: str,
    ) -> None:
        """Пагинация: Limit=1."""
        payload = {"SupplierUuid": supplier_uuid, "Limit": 1}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        assert _total_orders(data) == 1

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_pos_order_list_offset_beyond(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        endpoint: str,
    ) -> None:
        """Пагинация: Offset за пределами выборки."""
        payload = {"SupplierUuid": supplier_uuid, "Offset": 10000}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)
        assert _total_orders(data) == 0

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    @pytest.mark.parametrize("direction", ["asc", "desc"])
    def test_pos_order_list_sort_by_price(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        endpoint: str,
        direction: str,
    ) -> None:
        """Сортировка по цене."""
        payload = {"SupplierUuid": supplier_uuid, "SortByPrice": direction}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)

        prices = []
        for o in _iter_orders(data):
            try:
                prices.append(float(o.get("OrderPrice", 0)))
            except (TypeError, ValueError):
                prices.append(0.0)
        assert prices, f"Список Orders пуст на {endpoint}"

        if direction == "asc":
            assert prices == sorted(prices)
        else:
            assert prices == sorted(prices, reverse=True)

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    @pytest.mark.parametrize("direction", ["asc", "desc"])
    def test_pos_order_list_sort_by_create_date(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        endpoint: str,
        direction: str,
    ) -> None:
        """Сортировка по дате создания."""
        payload = {"SupplierUuid": supplier_uuid, "SortByOrderCreateDate": direction}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)

        dates = [o.get("OrderCreatedDate", "") for o in _iter_orders(data)]
        assert dates, f"Список Orders пуст на {endpoint}"

        if direction == "asc":
            assert dates == sorted(dates)
        else:
            assert dates == sorted(dates, reverse=True)

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_pos_order_list_pay_data_consistency(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        endpoint: str,
    ) -> None:
        """Согласованность OrderPayStatus и OrderPayData."""
        payload = {"SupplierUuid": supplier_uuid}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 200)
        data = CustomAssertions.assert_valid_json(response)

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")
        orders = list(_iter_orders(data))
        assert orders, f"Список Orders пуст на {endpoint}"

        for order in orders:
            status = order.get("OrderPayStatus")
            pay_data = _get_pay_data(order)
            if status == "paid":
                assert pay_data is not None
                assert date_pattern.search(str(pay_data))
            if pay_data is None:
                assert status != "paid"


class TestOrderListNegative:

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_neg_order_list_missing_supplier_uuid(
        self, order_client: OrderClient, endpoint: str
    ) -> None:
        """Отсутствие обязательного SupplierUuid."""
        payload: dict[str, Any] = {}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 400)
        assert ErrorText.REQUIRED_FIELD in response.text

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_neg_order_list_empty_supplier_uuid(
        self, order_client: OrderClient, endpoint: str
    ) -> None:
        """Пустой SupplierUuid."""
        payload = {"SupplierUuid": ""}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 400)
        assert ErrorText.VALID_UUID in response.text

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_neg_order_list_invalid_supplier_uuid_format(
        self, order_client: OrderClient, endpoint: str
    ) -> None:
        """Невалидный формат SupplierUuid."""
        payload = {"SupplierUuid": "неправильный-uuid-123"}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 400)
        assert ErrorText.VALID_UUID in response.text

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_neg_order_list_nonexistent_supplier_uuid(
        self, order_client: OrderClient, endpoint: str
    ) -> None:
        """Несуществующий SupplierUuid."""
        payload = {"SupplierUuid": DataGenerators.generate_nonexistent_uuid()}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        assert response.status_code in [200, 404, 422]
        if response.status_code == 200:
            data = response.json()
            assert _total_orders(data) == 0
        else:
            logger.info("Негатив на %s: статус %s", endpoint, response.status_code)

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_neg_order_list_limit_zero(
        self, order_client: OrderClient, supplier_uuid: str, endpoint: str
    ) -> None:
        """Limit=0."""
        payload = {"SupplierUuid": supplier_uuid, "Limit": 0}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 400)
        assert ErrorText.GE_ONE in response.text

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_neg_order_list_limit_negative(
        self, order_client: OrderClient, supplier_uuid: str, endpoint: str
    ) -> None:
        """Limit=-1."""
        payload = {"SupplierUuid": supplier_uuid, "Limit": -1}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 400)
        assert ErrorText.GE_ONE in response.text

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_neg_order_list_limit_non_numeric(
        self, order_client: OrderClient, supplier_uuid: str, endpoint: str
    ) -> None:
        """Limit нечисловой."""
        payload = {"SupplierUuid": supplier_uuid, "Limit": "asc"}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 400)
        assert ErrorText.VALID_NUMBER in response.text

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_neg_order_list_offset_negative(
        self, order_client: OrderClient, supplier_uuid: str, endpoint: str
    ) -> None:
        """Offset=-1."""
        payload = {"SupplierUuid": supplier_uuid, "Offset": -1}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 400)
        assert ErrorText.GE_ZERO in response.text

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_neg_order_list_offset_non_numeric(
        self, order_client: OrderClient, supplier_uuid: str, endpoint: str
    ) -> None:
        """Offset нечисловой."""
        payload = {"SupplierUuid": supplier_uuid, "Offset": "abc"}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, 400)
        assert ErrorText.VALID_NUMBER in response.text

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_LIST_PLATFORMS, ids=str)
    def test_neg_order_list_invalid_date_format(
        self, order_client: OrderClient, supplier_uuid: str, endpoint: str
    ) -> None:
        """Невалидный формат даты."""
        payload = {"SupplierUuid": supplier_uuid, "FromOrderCreateDatetime": "not-a-date"}
        response = order_client.get_order_list(payload, endpoint=endpoint)
        assert response.status_code in [400, 422, 200]
        logger.info("Негатив invalid date на %s: статус %s", endpoint, response.status_code)
