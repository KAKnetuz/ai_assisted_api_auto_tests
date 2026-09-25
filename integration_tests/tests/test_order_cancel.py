"""
Тесты отмены заказа.
"""

import logging

import pytest

from integration_tests.api_clients.order_client import OrderClient
from integration_tests.helpers.assertions import CustomAssertions
from integration_tests.helpers.data_generators import DataGenerators

logger = logging.getLogger(__name__)


@pytest.mark.smoke
class TestOrderCancel:
    """Тесты для отмены заказов."""

    # ------------------------------------------------------------------
    # 🔒 Безопасная очистка: отмена заказа без падения теста
    # ------------------------------------------------------------------
    @staticmethod
    def _cancel_order_safely(
        order_client: OrderClient,
        order_uuid: str,
        supplier_uuid: str,
    ) -> None:
        """Попытка отменить заказ. Подавляет любые исключения — только лог."""
        try:
            order_client.cancel_order_by_uuid(
                order_uuid=order_uuid,
                supplier_uuid=supplier_uuid,
                reason="Автотест: автоматическая отмена после проверки",
            )
            logger.info("✅ Заказ %s успешно отменён (cleanup)", order_uuid)
        except Exception as e:
            logger.warning("⚠️ Очистка заказа %s не удалась: %s", order_uuid, e)

    def test_create_and_cancel_order(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        tariff_id: int,
        account_number: str,
        request: pytest.FixtureRequest,
    ) -> None:
        """
        Позитивный тест: создание заказа, его отмена и проверка статуса.
        """
        # Act - создание заказа
        response_create = order_client.create_order_with_params(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_id,
            price="100",
            account_number=account_number,
        )
        CustomAssertions.assert_status_code(response_create, 201)
        create_data = CustomAssertions.assert_valid_json(response_create)
        order_uuid = create_data["OrderUuid"]

        # ⚠️ ВАЖНО: регистрируем клинап СРАЗУ после получения order_uuid
        request.addfinalizer(
            lambda: self._cancel_order_safely(order_client, order_uuid, supplier_uuid)
        )

        # Act - отмена заказа
        response_cancel = order_client.cancel_order_by_uuid(
            order_uuid=order_uuid,
            supplier_uuid=supplier_uuid,
            reason="Тестовая отмена заказа.",
        )

        # Assert - проверка отмены
        CustomAssertions.assert_status_code(response_cancel, 200)
        cancel_data = CustomAssertions.assert_valid_json(response_cancel)
        CustomAssertions.assert_cancel_success(cancel_data)

        # Act - проверка статуса
        response_status = order_client.get_order_status_by_order_uuid(
            supplier_uuid=supplier_uuid,
            order_uuid=order_uuid,
        )

        # Assert - проверка статуса
        CustomAssertions.assert_status_code(response_status, 200)
        status_data = CustomAssertions.assert_valid_json(response_status)
        assert len(status_data["Orders"]) > 0
        assert status_data["Orders"][0]["Status"] == "cancel"

    @pytest.mark.regression
    @pytest.mark.parametrize(
        "missing_field",
        ["SupplierUuid", "OrderUuid", "Reason"],
        ids=["missing_supplier", "missing_order", "missing_reason"],
    )
    def test_cancel_order_missing_field(
        self,
        order_client: OrderClient,
        supplier_uuid: str,
        missing_field: str,
    ) -> None:
        """Негативный тест: отсутствие обязательного поля."""
        payload = {
            "OrderUuid": DataGenerators.generate_nonexistent_uuid(),
            "SupplierUuid": supplier_uuid,
            "Reason": "Тестовая отмена заказа.",
        }
        del payload[missing_field]

        response = order_client.cancel_order(payload)
        CustomAssertions.assert_status_code(response, [400, 422])
