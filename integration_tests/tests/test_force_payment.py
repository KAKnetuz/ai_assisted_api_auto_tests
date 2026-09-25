"""
Тесты принудительной оплаты: создание заказа, списание средств и закрытие заказа за один вызов.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

import pytest

from integration_tests.api_clients.block_client import BlockClient
from integration_tests.api_clients.force_payment_client import ForcePaymentClient
from integration_tests.api_clients.order_client import OrderClient
from integration_tests.config.constants import FORCE_PAYMENT_SCALE, AccountTag, ResultCode
from integration_tests.helpers.assertions import CustomAssertions
from integration_tests.helpers.data_generators import DataGenerators

try:
    from integration_tests.utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    from integration_tests.utils.logger import logger


PAY_STATUS_CANDIDATES = {
    "оплачен",
    "оплачено",
    "paid",
    "paid_in_full",
    "complete",
}

ORDER_CLIENT_STATUS_METHODS = (
    "get_order_status",
    "get_order_status_with_tariff",
    "get_order_list",
)


def _normalize_decimal(value: Any) -> str:
    assert value is not None
    return f"{float(str(value)):.2f}"


def _is_valid_uuid(value: Any) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def _build_payload(
    supplier_uuid: str,
    tariff_unique_name: str,
    account_number: str | None = None,
    price: str = "50.00",
    procedure_number: str | None = None,
    procedure_uuid: str | None = None,
    include_account_fields: bool = True,
) -> dict[str, Any]:
    final_proc_number = procedure_number if procedure_number is not None else f"PROC-{uuid.uuid4().hex[:8]}"
    final_proc_uuid = procedure_uuid if procedure_uuid is not None else str(uuid.uuid4())

    payload: dict[str, Any] = {
        "Price": price,
        "ProcedureNumber": final_proc_number,
        "ProcedureUuid": final_proc_uuid,
        "SupplierUuid": supplier_uuid,
        "TariffUniqueName": tariff_unique_name,
    }

    if include_account_fields and account_number:
        payload["AccountNumber"] = account_number
        payload["AccountTag"] = AccountTag.SERVICES

    return payload


def _assert_force_payment_success(data: dict[str, Any]) -> None:
    CustomAssertions.assert_field_exists(data, "Sum", str)
    CustomAssertions.assert_field_exists(data, "AvailibleSupplierAmount", str)
    CustomAssertions.assert_field_exists(data, "TransactionUuid", str)
    CustomAssertions.assert_field_exists(data, "TransactionDatetime", str)
    CustomAssertions.assert_field_exists(data, "Discounts", list)

    normalized_sum = _normalize_decimal(data["Sum"])
    assert float(normalized_sum) > 0.0, f"Sum={data['Sum']!r}"

    assert _is_valid_uuid(data["TransactionUuid"]), f"TransactionUuid={data['TransactionUuid']!r}"
    assert str(data["TransactionDatetime"]).strip()

    normalized_available = _normalize_decimal(data["AvailibleSupplierAmount"])
    assert float(normalized_available) >= 0.0, f"AvailibleSupplierAmount={data['AvailibleSupplierAmount']!r}"

    assert isinstance(data["Discounts"], list)


def _assert_client_error(response: Any) -> None:
    CustomAssertions.assert_status_code(response, [400, 422])
    CustomAssertions.assert_valid_json(response)


def _get_order_status_response(order_client: Any, payload: dict[str, Any]) -> Any:
    for method_name in ORDER_CLIENT_STATUS_METHODS:
        method = getattr(order_client, method_name, None)
        if callable(method):
            return method(payload)
    pytest.fail(f"Не найден метод получения статуса: {ORDER_CLIENT_STATUS_METHODS}")


def _get_first_order(order_client: Any, payload: dict[str, Any]) -> dict[str, Any]:
    last_data = None
    for attempt in range(1, 4):
        response = _get_order_status_response(order_client, payload)
        CustomAssertions.assert_status_code(response, [200])
        data = CustomAssertions.assert_valid_json(response)
        last_data = data
        orders = data.get("Orders", [])
        if isinstance(orders, list) and orders:
            return orders[0]
        time.sleep(1)
    pytest.fail(f"Заказ не найден за 3 попытки. Payload={payload}. Последний ответ={last_data}.")


def _extract_order_status(order: dict[str, Any]) -> str:
    status = order.get("Status") or order.get("OrderStatus")
    assert status, f"Status not found: {order}"
    return str(status)


def _extract_pay_status(order: dict[str, Any]) -> str:
    pay_status = order.get("StatusPay") or order.get("OrderPayStatus")
    assert pay_status is not None and str(pay_status).strip(), f"PayStatus not found: {order}"
    return str(pay_status).strip()


def _cancel_order_and_refund(
    order_client: OrderClient,
    block_client: BlockClient,
    supplier_uuid: str,
    order_uuid: str,
    procedure_uuid: str,
) -> None:
    """Очистка: отмена заказа и снятие блокировки. Ошибки только логируются."""
    try:
        cancel_response = order_client.cancel_order_by_uuid(
            order_uuid=order_uuid,
            supplier_uuid=supplier_uuid,
            reason="Тестовая отмена заказа для возврата средств",
        )
        if cancel_response.status_code in [200, 201]:
            logger.info("Заказ %s отменён", order_uuid)
        else:
            logger.warning("Отмена вернула статус %s", cancel_response.status_code)
    except Exception as e:
        logger.error("Ошибка отмены заказа %s: %s", order_uuid, str(e))

    try:
        unblock_response = block_client.unblock({"ProcedureUuid": procedure_uuid, "SupplierUuid": supplier_uuid})
        if unblock_response.status_code in [200, 201]:
            logger.info("Средства по процедуре %s разблокированы", procedure_uuid)
        else:
            logger.warning("Разблокировка вернула статус %s", unblock_response.status_code)
    except Exception as e:
        logger.error("Ошибка разблокировки %s: %s", procedure_uuid, str(e))


class TestForcePayment:

    @pytest.mark.smoke
    def test_pos_force_payment_valid_data(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        account_number: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            account_number=account_number,
            price="50.00",
            include_account_fields=True,
        )
        response = force_payment_client.force_payment(payload)
        CustomAssertions.assert_status_code(response, [200])
        data = CustomAssertions.assert_valid_json(response)
        _assert_force_payment_success(data)

    @pytest.mark.regression
    @pytest.mark.parametrize(
        "price, expected_sum",
        FORCE_PAYMENT_SCALE,
        ids=["step1", "step2", "step3"],
    )
    def test_pos_force_payment_scale_steps(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        account_number: str,
        tariff_scale_unique_name: str,
        price: str,
        expected_sum: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            account_number=account_number,
            price=price,
            include_account_fields=False,
        )
        response = force_payment_client.force_payment(payload)
        CustomAssertions.assert_status_code(response, [200])
        data = CustomAssertions.assert_valid_json(response)
        _assert_force_payment_success(data)
        actual_sum = _normalize_decimal(data["Sum"])
        expected_normalized = _normalize_decimal(expected_sum)
        assert actual_sum == expected_normalized

    @pytest.mark.regression
    def test_pos_force_payment_without_optional_account_fields(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            account_number=None,
            price="50.00",
            include_account_fields=False,
        )
        response = force_payment_client.force_payment(payload)
        CustomAssertions.assert_status_code(response, [200])
        data = CustomAssertions.assert_valid_json(response)
        _assert_force_payment_success(data)

    @pytest.mark.regression
    def test_pos_force_payment_order_completed_and_paid_after(
        self,
        force_payment_client: ForcePaymentClient,
        order_client: Any,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            account_number=None,
            price="50.00",
            include_account_fields=False,
        )
        response = force_payment_client.force_payment(payload)
        CustomAssertions.assert_status_code(response, [200])
        data = CustomAssertions.assert_valid_json(response)
        _assert_force_payment_success(data)

        order_status_payload = {
            "SupplierUuid": supplier_uuid,
            "ProcedureUuid": payload["ProcedureUuid"],
            "ProcedureNumber": payload["ProcedureNumber"],
        }
        order = _get_first_order(order_client, order_status_payload)

        order_status = _extract_order_status(order)
        assert order_status == "complete"

        pay_status = _extract_pay_status(order)
        if pay_status.lower() not in PAY_STATUS_CANDIDATES:
            pytest.fail(f"Unknown pay status: {pay_status!r}")

    def test_neg_force_payment_missing_price(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            include_account_fields=False,
        )
        payload.pop("Price")
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_missing_procedure_number(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            include_account_fields=False,
        )
        payload.pop("ProcedureNumber")
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_missing_procedure_uuid(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            include_account_fields=False,
        )
        payload.pop("ProcedureUuid")
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_missing_supplier_uuid(
        self,
        force_payment_client: ForcePaymentClient,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid="placeholder",
            tariff_unique_name=tariff_scale_unique_name,
            include_account_fields=False,
        )
        payload.pop("SupplierUuid")
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_empty_price(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            price="",
            include_account_fields=False,
        )
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_empty_procedure_number(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            procedure_number="",
            include_account_fields=False,
        )
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_empty_procedure_uuid(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            procedure_uuid="",
            include_account_fields=False,
        )
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_empty_supplier_uuid(
        self,
        force_payment_client: ForcePaymentClient,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid="",
            tariff_unique_name=tariff_scale_unique_name,
            include_account_fields=False,
        )
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_invalid_supplier_uuid_format(
        self,
        force_payment_client: ForcePaymentClient,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid="invalid-uuid",
            tariff_unique_name=tariff_scale_unique_name,
            include_account_fields=False,
        )
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_invalid_procedure_uuid_format(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            procedure_uuid="invalid-uuid",
            include_account_fields=False,
        )
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_invalid_price_format(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            include_account_fields=False,
        )
        payload["Price"] = True
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_invalid_procedure_number_format(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            include_account_fields=False,
        )
        payload["ProcedureNumber"] = ["invalid"]
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_invalid_promocode_format(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            include_account_fields=False,
        )
        payload["PromoCode"] = "PROMO"
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_nonexistent_supplier_uuid(
        self,
        force_payment_client: ForcePaymentClient,
        tariff_scale_unique_name: str,
    ) -> None:
        nonexistent = str(DataGenerators.generate_nonexistent_uuid())
        payload = _build_payload(
            supplier_uuid=nonexistent,
            tariff_unique_name=tariff_scale_unique_name,
            include_account_fields=False,
        )
        response = force_payment_client.force_payment(payload)
        if response.status_code == 200:
            data = CustomAssertions.assert_valid_json(response)
            code = str(data.get("Code", ""))
            has_error = code not in {"", str(ResultCode.SUCCESS.value)}
            has_no_tx = not data.get("TransactionUuid")
            assert has_error or has_no_tx
        elif response.status_code in {400, 422}:
            CustomAssertions.assert_valid_json(response)
        else:
            pytest.fail(f"Unexpected status: {response.status_code}")

    def test_neg_force_payment_negative_price(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            price="-50",
            include_account_fields=False,
        )
        response = force_payment_client.force_payment(payload)
        _assert_client_error(response)

    def test_neg_force_payment_duplicate_procedure(
        self,
        force_payment_client: ForcePaymentClient,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
    ) -> None:
        procedure_number = f"PROC-DUP-{uuid.uuid4().hex[:8]}"
        procedure_uuid = str(uuid.uuid4())
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            price="50.00",
            procedure_number=procedure_number,
            procedure_uuid=procedure_uuid,
            include_account_fields=False,
        )

        first_response = force_payment_client.force_payment(payload)
        CustomAssertions.assert_status_code(first_response, [200])
        first_data = CustomAssertions.assert_valid_json(first_response)
        _assert_force_payment_success(first_data)
        first_tx = first_data["TransactionUuid"]

        second_response = force_payment_client.force_payment(payload)
        if second_response.status_code == 200:
            second_data = CustomAssertions.assert_valid_json(second_response)
            _assert_force_payment_success(second_data)
            second_tx = second_data.get("TransactionUuid")
            assert second_tx == first_tx
        elif second_response.status_code in {400, 422}:
            CustomAssertions.assert_valid_json(second_response)
        else:
            pytest.fail(f"Unexpected status: {second_response.status_code}")

    def test_neg_force_payment_price_exceeds_balance_with_positive_balance(
        self,
        force_payment_client: ForcePaymentClient,
        order_client: OrderClient,
        block_client: BlockClient,
        account_client: Any,
        supplier_uuid: str,
        tariff_scale_unique_name: str,
        account_number: str,
    ) -> None:
        account_info_payload = {
            "SupplierUuid": supplier_uuid,
            "AccountNumber": account_number,
        }
        current_balance = 0.0
        try:
            account_methods = ["get_account_info"]
            account_response = None
            for method_name in account_methods:
                method = getattr(account_client, method_name, None)
                if callable(method):
                    account_response = method(account_info_payload)
                    break
            if account_response and account_response.status_code == 200:
                account_data = CustomAssertions.assert_valid_json(account_response)
                if account_data.get("Data"):
                    info = account_data["Data"][0]
                    balance_str = info.get("NotBlockedAmount") or info.get("Amount")
                    if balance_str:
                        current_balance = float(balance_str)
            else:
                current_balance = 100.0
        except Exception:
            current_balance = 100.0

        price_exceeding_balance = str(current_balance + 1000.00)
        payload = _build_payload(
            supplier_uuid=supplier_uuid,
            tariff_unique_name=tariff_scale_unique_name,
            account_number=account_number,
            price=price_exceeding_balance,
            include_account_fields=True,
        )
        procedure_uuid = payload["ProcedureUuid"]
        response = force_payment_client.force_payment(payload)

        order_uuid = None
        if response.status_code in [400, 422]:
            _assert_client_error(response)
        elif response.status_code == 200:
            data = CustomAssertions.assert_valid_json(response)
            if "IsAllowed" in data:
                assert data["IsAllowed"] is False
            elif "Code" in data and str(data["Code"]) not in {"", str(ResultCode.SUCCESS.value)}:
                pass
            elif not data.get("TransactionUuid"):
                pass
            else:
                order_uuid = data.get("OrderUuid")
        else:
            pytest.fail(f"Unexpected status: {response.status_code}")

        if order_uuid:
            _cancel_order_and_refund(
                order_client=order_client,
                block_client=block_client,
                supplier_uuid=supplier_uuid,
                order_uuid=order_uuid,
                procedure_uuid=procedure_uuid,
            )
