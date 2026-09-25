"""
Тесты создания заказа (платформы core и platform_b).
"""

from __future__ import annotations

import logging
from typing import Any

import allure
import pytest

from integration_tests.api_clients.order_client import OrderClient
from integration_tests.config.constants import ORDER_CREATE_PLATFORMS, ErrorText, ResultCode
from integration_tests.config.endpoints import Platform
from integration_tests.helpers.assertions import CustomAssertions
from integration_tests.helpers.data_generators import DataGenerators

logger = logging.getLogger(__name__)


# ======================================================================
# ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ КЛАССА
# ======================================================================
@allure.epic("API-тесты")
@allure.feature("Создание заказа")
class TestOrderCreate:
    """Тесты создания заказов на платформах core / platform_b."""

    # ------------------------------------------------------------------
    # Безопасная очистка: отмена заказа без падения теста
    # ------------------------------------------------------------------
    @staticmethod
    def _cleanup_order(
        order_client: OrderClient,
        order_uuid: str,
        supplier_uuid: str,
    ) -> None:
        """Попытка отменить заказ. Подавляет любые исключения — только лог."""
        try:
            cancel_payload: dict[str, str] = {
                "OrderUuid": order_uuid,
                "SupplierUuid": supplier_uuid,
                "Reason": "Автотест: автоматическая отмена после проверки",
            }
            order_client.cancel_order(cancel_payload)
            logger.info("✅ Заказ %s успешно отменён", order_uuid)
        except Exception as e:
            logger.warning("⚠️ Очистка заказа %s не удалась: %s", order_uuid, e)

    # ------------------------------------------------------------------
    # Общая логика негативных проверок (DRY)
    # ------------------------------------------------------------------
    @staticmethod
    def _assert_negative_case(
        response: Any,
        expected_statuses: list[int],
        expected_substr: str | None = None,
        expected_code: ResultCode | None = None,
        endpoint: str = "",
    ) -> None:
        """
        Универсальный чекер негативного сценария.

        :param response: ответ requests.Response
        :param expected_statuses: список допустимых HTTP-кодов
        :param expected_substr: подстрока, которую ожидаем в теле ответа
        :param expected_code: ожидаемый Code в JSON (опционально)
        :param endpoint: имя эндпоинта для логов
        """
        CustomAssertions.assert_status_code(response, expected_statuses)

        if expected_code is not None:
            data = CustomAssertions.assert_valid_json(response)
            actual_code = str(data.get("Code"))
            assert actual_code == str(expected_code.value), (
                f"[{endpoint}] Ожидался Code={expected_code.value} ({expected_code.name}), получен Code={actual_code}. "
                f"Тело: {response.text[:300]}"
            )

        if expected_substr is not None:
            assert expected_substr in response.text, (
                f"[{endpoint}] Ожидалась подстрока {expected_substr!r} "
                f"на статусе {response.status_code}. Тело: {response.text[:300]}"
            )
        else:
            logger.info(
                "Негатив [%s]: статус=%s, тело=%s",
                endpoint,
                response.status_code,
                response.text[:300],
            )

    # ------------------------------------------------------------------
    # Фабрика payload (избавляемся от дублирования)
    # ------------------------------------------------------------------
    @staticmethod
    def _build_create_payload(
        supplier_uuid: str,
        tariff_id: int | None = None,
        tariff_unique_name: str | None = None,
        price: str = "100",
        procedure_number: str | None = None,
        procedure_uuid: str | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """Собирает базовый payload создания заказа с возможностью переопределения."""
        payload: dict[str, Any] = {
            "Price": price,
            "ProcedureNumber": procedure_number or DataGenerators.generate_procedure_number(),
            "ProcedureUuid": procedure_uuid or DataGenerators.generate_uuid(),
            "SupplierUuid": supplier_uuid,
        }
        if tariff_id is not None:
            payload["TariffId"] = str(tariff_id)
        if tariff_unique_name is not None:
            payload["TariffUniqueName"] = tariff_unique_name
        payload.update(overrides)
        return payload

    # ==================================================================
    # ПОЗИТИВНЫЕ ТЕСТЫ
    # ==================================================================
    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "endpoint, strict_new",
        [(Platform.CORE, True), (Platform.PLATFORM_B, False)],
        ids=str,
    )
    @allure.story("Позитив: создание и проверка статуса")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_pos_create_order_and_check_status(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        tariff_id: int,
        endpoint: str,
        strict_new: bool,
        request: pytest.FixtureRequest,
    ) -> None:
        """
        Создание заказа и проверка его статуса.
        Для core — жёсткая проверка Status='new'.
        Для platform_b — мягкая (только лог), т.к. платформа может возвращать иной статус.
        """
        # Arrange
        payload = self._build_create_payload(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_id,
            price="100",
        )

        # Act: создание
        response_create = order_client.create_order_with_params(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_id,
            price="100",
            procedure_number=payload["ProcedureNumber"],
            procedure_uuid=payload["ProcedureUuid"],
            endpoint=endpoint,
        )

        # Assert: создание
        CustomAssertions.assert_status_code(response_create, 201)
        create_data = CustomAssertions.assert_valid_json(response_create)
        CustomAssertions.assert_field_exists(create_data, "OrderUuid")
        assert create_data.get("Status") == "new", (
            f"Ожидаемый статус в ответе 201 — 'new', получен {create_data.get('Status')!r}"
        )

        order_uuid: str = create_data["OrderUuid"]


        request.addfinalizer(lambda: self._cleanup_order(order_client, order_uuid, supplier_uuid))

        # Act: проверка статуса через универсальный core-эндпоинт
        response_status = order_client.get_order_status_by_order_uuid(
            supplier_uuid=supplier_uuid,
            order_uuid=order_uuid,
            endpoint=Platform.CORE,
        )

        # Assert: статус (жёстко/мягко в зависимости от платформы)
        if response_status.status_code == 200:
            status_data = CustomAssertions.assert_valid_json(response_status)
            orders = status_data.get("Orders") or []
            if orders and isinstance(orders, list) and "Status" in orders[0]:
                actual_status = orders[0]["Status"]
                if strict_new:
                    assert actual_status == "new", (
                        f"Ожидаемый статус заказа 'new', получен {actual_status!r}"
                    )
                else:
                    logger.info("Мягкая проверка статуса для %s: %s", endpoint, actual_status)
        else:
            logger.info(
                "Мягкая проверка: get_order_status вернул %s для %s",
                response_status.status_code,
                endpoint,
            )

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_CREATE_PLATFORMS, ids=str)
    @allure.story("Позитив: создание по TariffUniqueName")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_pos_create_order_by_unique_name(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        tariff_unique_name: str,
        endpoint: str,
        request: pytest.FixtureRequest,
    ) -> None:
        """Создание заказа по TariffUniqueName вместо TariffId."""
        # Arrange
        payload = self._build_create_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_unique_name,
            price="100",
        )

        # Act
        response_create = order_client.create_order(payload, endpoint=endpoint)

        # Assert
        CustomAssertions.assert_status_code(response_create, 201)
        create_data = CustomAssertions.assert_valid_json(response_create)
        CustomAssertions.assert_field_exists(create_data, "OrderUuid")
        assert create_data.get("Status") == "new", "Ожидаемый статус 'new'"

        order_uuid: str = create_data["OrderUuid"]
        request.addfinalizer(lambda: self._cleanup_order(order_client, order_uuid, supplier_uuid))

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_CREATE_PLATFORMS, ids=str)
    @allure.story("Позитив: минимальный payload")
    @allure.severity(allure.severity_level.NORMAL)
    def test_pos_create_order_response_minimal_fields(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        tariff_id: int,
        endpoint: str,
        request: pytest.FixtureRequest,
    ) -> None:
        """Минимальный валидный payload — проверяем только OrderUuid и Status."""
        # Arrange
        payload = self._build_create_payload(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_id,
            price="10",
        )

        # Act
        response_create = order_client.create_order(payload, endpoint=endpoint)

        # Assert
        CustomAssertions.assert_status_code(response_create, 201)
        create_data = CustomAssertions.assert_valid_json(response_create)
        CustomAssertions.assert_field_exists(create_data, "OrderUuid")
        assert create_data.get("Status") == "new", "Ожидаемый статус 'new'"

        # Мягкая проверка Sum (если поле пришло)
        sum_value = create_data.get("Sum")
        if sum_value is not None:
            try:
                float(sum_value)
            except ValueError:
                logger.info("Поле Sum присутствует, но не является числом: %s", sum_value)

        order_uuid: str = create_data["OrderUuid"]
        request.addfinalizer(lambda: self._cleanup_order(order_client, order_uuid, supplier_uuid))

    # ==================================================================
    # НЕГАТИВНЫЕ ТЕСТЫ
    # ==================================================================
    @pytest.mark.regression
    @pytest.mark.parametrize(
        "endpoint",
        ORDER_CREATE_PLATFORMS,
        ids=str,
    )
    @allure.story("Негатив: отсутствует SupplierUuid")
    def test_neg_order_create_missing_supplier_uuid(
        self,
        order_client: OrderClient,
        tariff_id: int,
        endpoint: str,
    ) -> None:
        """
        Отсутствие SupplierUuid без Buyer*-полей — ошибка валидации.
        Примечание: отсутствие SupplierUuid легитимно ТОЛЬКО при наличии Buyer*-полей.
        """
        payload = self._build_create_payload(
            supplier_uuid="",  # подменяем ниже
            tariff_id=tariff_id,
        )
        payload.pop("SupplierUuid", None)  # полностью убираем ключ

        response = order_client.create_order(payload, endpoint=endpoint)
        self._assert_negative_case(
            response=response,
            expected_statuses=[400, 422],
            expected_substr=ErrorText.REQUIRED_FIELD,
            endpoint=endpoint,
        )

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_CREATE_PLATFORMS, ids=str)
    @allure.story("Негатив: пустой SupplierUuid")
    def test_neg_order_create_empty_supplier_uuid(
        self,
        order_client: OrderClient,
        tariff_id: int,
        endpoint: str,
    ) -> None:
        """Пустой SupplierUuid — ошибка валидации."""
        payload = self._build_create_payload(
            supplier_uuid="",
            tariff_id=tariff_id,
        )
        response = order_client.create_order(payload, endpoint=endpoint)
        self._assert_negative_case(
            response=response,
            expected_statuses=[400, 422],
            endpoint=endpoint,
        )

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_CREATE_PLATFORMS, ids=str)
    @allure.story("Негатив: неверный формат SupplierUuid")
    def test_neg_order_create_invalid_supplier_uuid_format(
        self,
        order_client: OrderClient,
        tariff_id: int,
        endpoint: str,
    ) -> None:
        """Неверный формат SupplierUuid (не UUID)."""
        payload = self._build_create_payload(
            supplier_uuid="неправильный-uuid-123",
            tariff_id=tariff_id,
        )
        response = order_client.create_order(payload, endpoint=endpoint)
        self._assert_negative_case(
            response=response,
            expected_statuses=[400, 422],
            endpoint=endpoint,
        )

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_CREATE_PLATFORMS, ids=str)
    @allure.story("Негатив: несуществующий SupplierUuid")
    def test_neg_order_create_nonexistent_supplier_uuid(
        self,
        order_client: OrderClient,
        tariff_id: int,
        endpoint: str,
    ) -> None:
        """Валидный UUID, но контрагента нет в БД — ожидается 422 SUPPLIER_NOT_FOUND."""
        payload = self._build_create_payload(
            supplier_uuid=DataGenerators.generate_nonexistent_uuid(),
            tariff_id=tariff_id,
        )
        response = order_client.create_order(payload, endpoint=endpoint)
        self._assert_negative_case(
            response=response,
            expected_statuses=[422],
            expected_substr=ErrorText.NOT_FOUND,
            expected_code=ResultCode.SUPPLIER_NOT_FOUND,
            endpoint=endpoint,
        )


    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_CREATE_PLATFORMS, ids=str)
    @allure.story("Негатив: отрицательная цена")
    def test_neg_order_create_negative_price(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        tariff_id: int,
        endpoint: str,
    ) -> None:
        """Отрицательная цена — 400 с подсказкой о формате."""
        payload = self._build_create_payload(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_id,
            price="-10",
        )
        response = order_client.create_order(payload, endpoint=endpoint)
        self._assert_negative_case(
            response=response,
            expected_statuses=[400],
            expected_substr=ErrorText.MIN_PRICE,
            endpoint=endpoint,
        )

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_CREATE_PLATFORMS, ids=str)
    @allure.story("Негатив: отсутствует идентификатор тарифа")
    def test_neg_order_create_missing_tariff_identifier(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        endpoint: str,
    ) -> None:
        """
        Нет ни TariffId, ни TariffUniqueName.
        Для platform_b — жёстко проверяем TARIFF_NOT_FOUND.
        Для core — мягкая проверка (нет эталонного скрина).
        """
        payload = self._build_create_payload(supplier_uuid=supplier_uuid)
        response = order_client.create_order(payload, endpoint=endpoint)

        if endpoint == Platform.PLATFORM_B:
            self._assert_negative_case(
                response=response,
                expected_statuses=[422],
                expected_substr=ErrorText.NOT_FOUND,
                expected_code=ResultCode.TARIFF_NOT_FOUND,
                endpoint=endpoint,
            )
        else:
            self._assert_negative_case(
                response=response,
                expected_statuses=[400, 422],
                endpoint=endpoint,
            )


    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_CREATE_PLATFORMS, ids=str)
    @allure.story("Негатив: неверный формат ProcedureUuid")
    def test_neg_order_create_invalid_procedure_uuid_format(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        tariff_id: int,
        endpoint: str,
    ) -> None:
        """Неверный формат ProcedureUuid."""
        payload = self._build_create_payload(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_id,
            procedure_uuid="неправильный-uuid",
        )
        response = order_client.create_order(payload, endpoint=endpoint)

        expected_statuses = [400, 422] if endpoint == Platform.CORE else [400]
        expected_substr = ErrorText.VALID_UUID if endpoint == Platform.PLATFORM_B else None

        self._assert_negative_case(
            response=response,
            expected_statuses=expected_statuses,
            expected_substr=expected_substr,
            endpoint=endpoint,
        )

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_CREATE_PLATFORMS, ids=str)
    @allure.story("Негатив: полное отсутствие Procedure*")
    def test_neg_order_create_missing_procedure(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        tariff_id: int,
        endpoint: str,
    ) -> None:
        """
        Полное отсутствие ключей ProcedureNumber и ProcedureUuid.
        Мягкая проверка — скриншоты подтверждают только пустые строки, не отсутствие ключей.
        """
        payload = self._build_create_payload(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_id,
        )
        payload.pop("ProcedureNumber", None)
        payload.pop("ProcedureUuid", None)

        response = order_client.create_order(payload, endpoint=endpoint)
        self._assert_negative_case(
            response=response,
            expected_statuses=[200, 201, 400, 422],  # мягкий диапазон
            endpoint=endpoint,
        )

    @pytest.mark.regression
    @pytest.mark.parametrize("endpoint", ORDER_CREATE_PLATFORMS, ids=str)
    @allure.story("Негатив: дубликат процедуры")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_neg_order_create_duplicate_procedure(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        tariff_id: int,
        endpoint: str,
        request: pytest.FixtureRequest,
    ) -> None:
        """
        Повторная отправка с теми же ProcedureNumber/ProcedureUuid.
        Ожидается 422 DUPLICATE_ORDER.
        Очистка отменяет ТОЛЬКО первый созданный заказ.
        """
        # Arrange
        payload = self._build_create_payload(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_id,
            price="100",
        )

        # Act 1: успешное создание
        response1 = order_client.create_order(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response1, 201)
        data1 = CustomAssertions.assert_valid_json(response1)
        order_uuid_first: str = data1["OrderUuid"]

        # ⚠️ ВАЖНО: клинап регистрируем СРАЗУ, а не в конце метода
        request.addfinalizer(
            lambda: self._cleanup_order(order_client, order_uuid_first, supplier_uuid)
        )

        # Act 2: дубликат
        response2 = order_client.create_order(payload, endpoint=endpoint)

        # Assert
        self._assert_negative_case(
            response=response2,
            expected_statuses=[422],
            expected_substr=ErrorText.ALREADY_EXISTS,
            expected_code=ResultCode.DUPLICATE_ORDER,
            endpoint=endpoint,
        )
