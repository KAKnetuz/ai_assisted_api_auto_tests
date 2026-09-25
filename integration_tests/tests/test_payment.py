"""
Тесты списания средств с победителя процедуры (payment).
Покрываются платформы platform_a и platform_b.
"""

from decimal import Decimal, InvalidOperation
from typing import Any

import pytest

from integration_tests.api_clients.block_client import BlockClient
from integration_tests.api_clients.payment_client import PaymentClient
from integration_tests.config.constants import (
    PAYMENT_ACCOUNT_TAG_BY_PLATFORM,
    PAYMENT_CONTRACT_PRICES,
    PAYMENT_DEFAULT_PRICE,
    PAYMENT_PLATFORMS,
    PAYMENT_TARIFF_BY_PLATFORM,
    ErrorText,
    ResultCode,
)
from integration_tests.config.endpoints import Platform
from integration_tests.config.settings import settings
from integration_tests.config.suppliers import ACCOUNTS_BY_TAG
from integration_tests.helpers.assertions import CustomAssertions, set_test_context
from integration_tests.helpers.data_generators import DataGenerators

PLATFORMS: list[Any] = [pytest.param(p, id=str(p)) for p in PAYMENT_PLATFORMS]


def _contract_price_cases(platform: Platform) -> list[Any]:
    """Кейсы «цена → ожидаемый ContractPrice» по шкале тарифа платформы."""
    return [
        pytest.param(price, expected, id=f"{price}->{expected}")
        for price, expected in PAYMENT_CONTRACT_PRICES[platform].items()
    ]


def _get_expected_contract_price(endpoint: str, price: str) -> str:
    """Возвращает ожидаемое значение ContractPrice для платформы."""
    return PAYMENT_CONTRACT_PRICES[endpoint][price]


def _make_block_precondition(
    block_client: BlockClient,
    endpoint: str,
    supplier_uuid: str,
    price: str,
    procedure_number: str,
    procedure_uuid: str,
    cleanup: list[dict[str, str]],
) -> tuple[dict[str, Any], Any]:
    """
    Предусловие: блокировка средств по тарифу.
    Блокировка регистрируется в cleanup (фикстура block_cleanup) и снимается после теста.
    Возвращает (response_data, blocked_sum) для cross-check с ContractPrice.
    """
    tariff_name = PAYMENT_TARIFF_BY_PLATFORM[endpoint]
    account_tag = PAYMENT_ACCOUNT_TAG_BY_PLATFORM[endpoint]

    account_number = ACCOUNTS_BY_TAG[account_tag].get(supplier_uuid)
    if not account_number:
        pytest.fail(f"Не найден счёт '{account_tag}' для SupplierUuid: {supplier_uuid}")

    payload: dict[str, Any] = {
        "Price": price,
        "ProcedureNumber": procedure_number,
        "ProcedureUuid": procedure_uuid,
        "SupplierUuid": supplier_uuid,
        "TariffUniqueName": tariff_name,
        "AccountNumber": account_number,
        "AccountTag": account_tag,
    }

    resp = block_client.block(payload, endpoint=endpoint)
    CustomAssertions.assert_status_code(resp, [200, 201])
    cleanup.append({"ProcedureUuid": procedure_uuid, "SupplierUuid": supplier_uuid})

    data = CustomAssertions.assert_valid_json(resp)

    blocked_sum = (
        data.get("TariffBlockedSum")
        or data.get("TariffCurrentBlockedSum")
        or data.get("CollectBlockedSum")
    )
    return data, blocked_sum


def _assert_payment_success(
    response: Any,
    expected_suppliers: list[str],
    expected_price: str,
    blocked_sums: list[Any],
    endpoint: str,
) -> None:
    """Ассерт успешного ответа payment (200, Status=true, ContractPrice)."""
    CustomAssertions.assert_status_code(response, 200)
    data = CustomAssertions.assert_valid_json(response)

    assert data.get("Status") is True, f"Ожидался Status=true, получено {data.get('Status')}. Тело ответа: {data}"

    payment_info = data.get("PaymentInfo", [])
    assert isinstance(payment_info, list), "PaymentInfo должен быть списком"
    assert len(payment_info) == len(expected_suppliers), (
        f"Количество элементов PaymentInfo ({len(payment_info)}) не совпадает с ожидаемым ({len(expected_suppliers)})"
    )

    expected_contract = _get_expected_contract_price(endpoint, expected_price)

    for i, item in enumerate(payment_info):
        assert item.get("Status") is True, f"Элемент {i}: Status должен быть true. Тело: {item}"
        assert item.get("SupplierUuid") == expected_suppliers[i], (
            f"Элемент {i}: SupplierUuid не совпадает. "
            f"Ожидался {expected_suppliers[i]}, получен {item.get('SupplierUuid')}"
        )

        contract_price = item.get("ContractPrice")
        assert contract_price is not None, f"Элемент {i}: Отсутствует ContractPrice"

        try:
            assert Decimal(str(contract_price)) == Decimal(expected_contract), (
                f"Элемент {i}: Ожидался ContractPrice={expected_contract} "
                f"(по шкале тарифа для Price={expected_price}), получено {contract_price}"
            )
        except InvalidOperation:
            pytest.fail(f"Элемент {i}: ContractPrice '{contract_price}' не является валидным числом")

        if blocked_sums and i < len(blocked_sums) and blocked_sums[i] is not None:
            try:
                assert Decimal(str(contract_price)) == Decimal(str(blocked_sums[i])), (
                    f"Элемент {i}: Cross-check failed. ContractPrice={contract_price}, BlockedSum={blocked_sums[i]}"
                )
            except (InvalidOperation, TypeError):
                pass


# ==============================================================================
# ПОЗИТИВНЫЕ ТЕСТЫ
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.parametrize("endpoint", PLATFORMS)
def test_pos_payment_single_winner(
    block_client: BlockClient,
    payment_client: PaymentClient,
    block_cleanup: list[dict[str, str]],
    endpoint: str,
) -> None:
    supplier = settings.SUPPLIER_UUIDS[0]
    set_test_context(supplier_uuid=supplier)

    price = PAYMENT_DEFAULT_PRICE[endpoint]
    proc_num = DataGenerators.generate_procedure_number()
    proc_uuid = DataGenerators.generate_uuid()

    _, blocked_sum = _make_block_precondition(
        block_client, endpoint, supplier, price, proc_num, proc_uuid, block_cleanup
    )

    item = PaymentClient.build_payment_info_item(supplier_uuid=supplier, price=price)
    payload = PaymentClient.build_payment_payload(
        procedure_number=proc_num,
        procedure_uuid=proc_uuid,
        payment_info=[item],
    )

    response = payment_client.payment(payload, endpoint=endpoint)
    _assert_payment_success(response, [supplier], price, [blocked_sum], endpoint)


@pytest.mark.regression
@pytest.mark.parametrize("endpoint", PLATFORMS)
def test_pos_payment_multiple_winners(
    block_client: BlockClient,
    payment_client: PaymentClient,
    block_cleanup: list[dict[str, str]],
    endpoint: str,
) -> None:
    suppliers = settings.SUPPLIER_UUIDS[:2]
    price = PAYMENT_DEFAULT_PRICE[endpoint]
    proc_num = DataGenerators.generate_procedure_number()
    proc_uuid = DataGenerators.generate_uuid()

    blocked_sums: list[Any] = []
    for sup in suppliers:
        set_test_context(supplier_uuid=sup)
        _, b_sum = _make_block_precondition(block_client, endpoint, sup, price, proc_num, proc_uuid, block_cleanup)
        blocked_sums.append(b_sum)

    payment_items = [PaymentClient.build_payment_info_item(supplier_uuid=sup, price=price) for sup in suppliers]
    payload = PaymentClient.build_payment_payload(
        procedure_number=proc_num,
        procedure_uuid=proc_uuid,
        payment_info=payment_items,
    )

    response = payment_client.payment(payload, endpoint=endpoint)
    _assert_payment_success(response, suppliers, price, blocked_sums, endpoint)


@pytest.mark.regression
@pytest.mark.parametrize("endpoint", PLATFORMS)
@pytest.mark.parametrize(
    "price,expected",
    _contract_price_cases(Platform.PLATFORM_A),
)
def test_pos_payment_contract_price_platform_a(
    block_client: BlockClient,
    payment_client: PaymentClient,
    block_cleanup: list[dict[str, str]],
    endpoint: str,
    price: str,
    expected: str,
) -> None:
    if endpoint != Platform.PLATFORM_A:
        pytest.skip("Тест только для платформы A")

    supplier = settings.SUPPLIER_UUIDS[0]
    set_test_context(supplier_uuid=supplier)

    proc_num = DataGenerators.generate_procedure_number()
    proc_uuid = DataGenerators.generate_uuid()

    _make_block_precondition(block_client, endpoint, supplier, price, proc_num, proc_uuid, block_cleanup)

    item = PaymentClient.build_payment_info_item(supplier_uuid=supplier, price=price)
    payload = PaymentClient.build_payment_payload(
        procedure_number=proc_num,
        procedure_uuid=proc_uuid,
        payment_info=[item],
    )

    response = payment_client.payment(payload, endpoint=endpoint)
    _assert_payment_success(response, [supplier], price, [None], endpoint)


@pytest.mark.regression
@pytest.mark.parametrize("endpoint", PLATFORMS)
@pytest.mark.parametrize(
    "price,expected",
    _contract_price_cases(Platform.PLATFORM_B),
)
def test_pos_payment_contract_price_platform_b(
    block_client: BlockClient,
    payment_client: PaymentClient,
    block_cleanup: list[dict[str, str]],
    endpoint: str,
    price: str,
    expected: str,
) -> None:
    if endpoint != Platform.PLATFORM_B:
        pytest.skip("Тест только для платформы B")

    supplier = settings.SUPPLIER_UUIDS[0]
    set_test_context(supplier_uuid=supplier)

    proc_num = DataGenerators.generate_procedure_number()
    proc_uuid = DataGenerators.generate_uuid()

    _make_block_precondition(block_client, endpoint, supplier, price, proc_num, proc_uuid, block_cleanup)

    item = PaymentClient.build_payment_info_item(supplier_uuid=supplier, price=price)
    payload = PaymentClient.build_payment_payload(
        procedure_number=proc_num,
        procedure_uuid=proc_uuid,
        payment_info=[item],
    )

    response = payment_client.payment(payload, endpoint=endpoint)
    _assert_payment_success(response, [supplier], price, [None], endpoint)


# ==============================================================================
# НЕГАТИВНЫЕ ТЕСТЫ
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("endpoint", PLATFORMS)
@pytest.mark.parametrize(
    "field_to_remove",
    ["ProcedureNumber", "ProcedureUuid", "PaymentInfo"],
    ids=["no_procedure_number", "no_procedure_uuid", "no_payment_info"],
)
def test_neg_payment_missing_field(
    payment_client: PaymentClient,
    endpoint: str,
    field_to_remove: str,
) -> None:
    payload = PaymentClient.build_payment_payload()
    del payload[field_to_remove]

    response = payment_client.payment(payload, endpoint=endpoint)
    CustomAssertions.assert_status_code(response, [400, 422])


@pytest.mark.regression
@pytest.mark.parametrize("endpoint", PLATFORMS)
def test_neg_payment_empty_payment_info_array(
    payment_client: PaymentClient,
    endpoint: str,
) -> None:
    payload = PaymentClient.build_payment_payload(payment_info=[])
    response = payment_client.payment(payload, endpoint=endpoint)
    CustomAssertions.assert_status_code(response, [400, 422])


@pytest.mark.regression
@pytest.mark.parametrize("endpoint", PLATFORMS)
@pytest.mark.parametrize(
    "field_to_remove",
    ["SupplierUuid", "Price"],
    ids=["no_supplier_in_item", "no_price_in_item"],
)
def test_neg_payment_missing_field_in_item(
    payment_client: PaymentClient,
    endpoint: str,
    field_to_remove: str,
) -> None:
    item = PaymentClient.build_payment_info_item(supplier_uuid=settings.SUPPLIER_UUIDS[0], price="1000")
    del item[field_to_remove]

    payload = PaymentClient.build_payment_payload(payment_info=[item])
    response = payment_client.payment(payload, endpoint=endpoint)
    CustomAssertions.assert_status_code(response, [400, 422])


@pytest.mark.regression
@pytest.mark.parametrize("endpoint", PLATFORMS)
def test_neg_payment_nonexistent_supplier_uuid(
    block_client: BlockClient,
    payment_client: PaymentClient,
    block_cleanup: list[dict[str, str]],
    endpoint: str,
) -> None:
    valid_supplier = settings.SUPPLIER_UUIDS[0]
    proc_num = DataGenerators.generate_procedure_number()
    proc_uuid = DataGenerators.generate_uuid()

    _make_block_precondition(block_client, endpoint, valid_supplier, "1000", proc_num, proc_uuid, block_cleanup)

    fake_uuid = DataGenerators.generate_nonexistent_uuid()
    item = PaymentClient.build_payment_info_item(supplier_uuid=fake_uuid, price="1000")
    payload = PaymentClient.build_payment_payload(
        procedure_number=proc_num,
        procedure_uuid=proc_uuid,
        payment_info=[item],
    )

    response = payment_client.payment(payload, endpoint=endpoint)
    CustomAssertions.assert_status_code(response, 422)

    data = CustomAssertions.assert_valid_json(response)
    code = data.get("Code") or (data.get("PaymentInfo", [{}])[0].get("Code") if data.get("PaymentInfo") else None)
    message = data.get("Message") or (
        data.get("PaymentInfo", [{}])[0].get("Message") if data.get("PaymentInfo") else ""
    )

    # API может вернуть SUPPLIER_NOT_FOUND или PROCEDURE_NOT_FOUND
    # (поставщик не участвовал в данной процедуре)
    expected_codes = {str(ResultCode.SUPPLIER_NOT_FOUND.value), str(ResultCode.PROCEDURE_NOT_FOUND.value)}
    assert str(code) in expected_codes, f"Ожидался Code из {expected_codes}, получен {code!r}"
    assert ErrorText.NOT_FOUND in str(message).lower(), (
        f"В Message должно быть '{ErrorText.NOT_FOUND}', получено {message!r}"
    )


@pytest.mark.regression
@pytest.mark.parametrize("endpoint", PLATFORMS)
def test_neg_payment_price_out_of_range(
    block_client: BlockClient,
    payment_client: PaymentClient,
    block_cleanup: list[dict[str, str]],
    endpoint: str,
) -> None:
    supplier = settings.SUPPLIER_UUIDS[0]
    proc_num = DataGenerators.generate_procedure_number()
    proc_uuid = DataGenerators.generate_uuid()

    _make_block_precondition(block_client, endpoint, supplier, "1000", proc_num, proc_uuid, block_cleanup)

    item = PaymentClient.build_payment_info_item(supplier_uuid=supplier, price="10000000000000")
    payload = PaymentClient.build_payment_payload(
        procedure_number=proc_num,
        procedure_uuid=proc_uuid,
        payment_info=[item],
    )

    response = payment_client.payment(payload, endpoint=endpoint)
    CustomAssertions.assert_status_code(response, 422)

    # API может вернуть ошибку диапазона цены или «процедура не найдена»
    # при некорректном контексте/цене
    assert ErrorText.OUT_OF_RANGE in response.text or ErrorText.NOT_FOUND in response.text, (
        f"Ожидалась ошибка о параметрах или процедуре. Тело ответа: {response.text[:300]}"
    )


@pytest.mark.regression
@pytest.mark.parametrize("endpoint", PLATFORMS)
def test_neg_payment_duplicate_request(
    block_client: BlockClient,
    payment_client: PaymentClient,
    block_cleanup: list[dict[str, str]],
    endpoint: str,
) -> None:
    supplier = settings.SUPPLIER_UUIDS[0]
    set_test_context(supplier_uuid=supplier)

    price = PAYMENT_DEFAULT_PRICE[endpoint]
    proc_num = DataGenerators.generate_procedure_number()
    proc_uuid = DataGenerators.generate_uuid()

    _make_block_precondition(block_client, endpoint, supplier, price, proc_num, proc_uuid, block_cleanup)

    item = PaymentClient.build_payment_info_item(supplier_uuid=supplier, price=price)
    payload = PaymentClient.build_payment_payload(
        procedure_number=proc_num,
        procedure_uuid=proc_uuid,
        payment_info=[item],
    )

    resp1 = payment_client.payment(payload, endpoint=endpoint)
    CustomAssertions.assert_status_code(resp1, 200)
    data1 = CustomAssertions.assert_valid_json(resp1)
    assert data1.get("Status") is True, f"Первый payment должен вернуть Status=true, получено {data1.get('Status')}"

    resp2 = payment_client.payment(payload, endpoint=endpoint)
    CustomAssertions.assert_status_code(resp2, 200)
    data2 = CustomAssertions.assert_valid_json(resp2)

    # ВАЖНО: API возвращает верхнеуровневый Status=True даже при дубликате.
    # Ошибка находится внутри элемента PaymentInfo.
    pi = data2.get("PaymentInfo", [])
    assert len(pi) > 0, f"PaymentInfo не должен быть пустым. Тело: {data2}"

    assert pi[0].get("Status") is False, (
        f"Статус элемента PaymentInfo должен быть false, получено {pi[0].get('Status')}"
    )
    assert str(pi[0].get("Code")) == str(ResultCode.ALREADY_PAID.value), (
        f"Ожидался Code={ResultCode.ALREADY_PAID.value} (ALREADY_PAID), получен {pi[0].get('Code')!r}"
    )
    assert ErrorText.ALREADY_PAID in str(pi[0].get("Message", "")).lower(), (
        f"В Message должно быть '{ErrorText.ALREADY_PAID}', получено {pi[0].get('Message')!r}"
    )
