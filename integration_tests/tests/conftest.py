"""
Фикстуры для API-тестов.
Содержит:
- Фикстуры для получения токена аутентификации
- Фикстуры для инициализации API-клиентов
- Фикстуры с тестовыми данными (UUID, account numbers, тарифы)
- Фикстуры для общих сценариев (создание заказа и т.д.)
- Фикстуры для генерации уникальных данных блокировки
- АВТОМАТИЧЕСКИЙ КОНТЕКСТ КА для улучшенных сообщений об ошибках
"""

import logging
import random
import uuid
from collections.abc import Iterator
from typing import Any

import pytest

from integration_tests.api_clients.account_client import AccountClient
from integration_tests.api_clients.auth_client import AuthClient
from integration_tests.api_clients.block_client import BlockClient
from integration_tests.api_clients.counterparty_client import CounterpartyClient
from integration_tests.api_clients.force_payment_client import ForcePaymentClient
from integration_tests.api_clients.operation_client import OperationClient
from integration_tests.api_clients.order_client import OrderClient
from integration_tests.api_clients.payment_client import PaymentClient
from integration_tests.api_clients.tariff_client import TariffClient
from integration_tests.api_clients.unpaid_orders_client import UnpaidOrdersClient
from integration_tests.config.constants import (
    CURRENCY_RUB,
    PAYMENT_ACCOUNT_TAG_BY_PLATFORM,
    PAYMENT_TARIFF_BY_PLATFORM,
    AccountTag,
)
from integration_tests.config.endpoints import Platform
from integration_tests.config.settings import settings
from integration_tests.config.suppliers import MAIN_ACCOUNT_BY_SUPPLIER, SERVICES_ACCOUNT_BY_SUPPLIER
from integration_tests.helpers.assertions import CustomAssertions, set_test_context

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False


@pytest.fixture(scope="session")
def auth_token() -> str | None:
    try:
        logger.debug("Получение токена аутентификации...")
        auth_client = AuthClient()
        token = auth_client.get_token()
        logger.info("Токен аутентификации успешно получен.")
        return token
    except Exception as e:
        pytest.fail(f"Не удалось получить токен аутентификации: {e}")


@pytest.fixture(scope="module")
def api_headers(auth_token: str | None) -> dict[str, str]:
    if not auth_token:
        pytest.fail("Токен аутентификации не получен")
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    logger.debug(f"Сформированные заголовки: {headers}")
    return headers


@pytest.fixture(scope="module")
def account_client(auth_token: str | None) -> AccountClient:
    if not auth_token:
        pytest.fail("Токен аутентификации не получен")
    return AccountClient(auth_token=auth_token)


@pytest.fixture(scope="module")
def order_client(auth_token: str | None) -> OrderClient:
    if not auth_token:
        pytest.fail("Токен аутентификации не получен")
    return OrderClient(auth_token=auth_token)


@pytest.fixture(scope="module")
def tariff_client(auth_token: str | None) -> TariffClient:
    if not auth_token:
        pytest.fail("Токен аутентификации не получен")
    return TariffClient(auth_token=auth_token)


@pytest.fixture(scope="module")
def block_client(auth_token: str | None) -> BlockClient:
    if not auth_token:
        pytest.fail("Токен аутентификации не получен")
    return BlockClient(auth_token=auth_token)


@pytest.fixture(scope="module")
def operation_client(auth_token: str | None) -> OperationClient:
    if not auth_token:
        pytest.fail("Токен аутентификации не получен")
    return OperationClient(auth_token=auth_token)


@pytest.fixture(scope="module")
def counterparty_client(auth_token: str | None) -> CounterpartyClient:
    if not auth_token:
        pytest.fail("Токен аутентификации не получен")
    return CounterpartyClient(auth_token=auth_token)


@pytest.fixture(scope="module")
def unpaid_orders_client(auth_token: str | None) -> UnpaidOrdersClient:
    if not auth_token:
        pytest.fail("Токен аутентификации не получен")
    return UnpaidOrdersClient(auth_token=auth_token)


@pytest.fixture(scope="module")
def force_payment_client(auth_token: str | None) -> ForcePaymentClient:
    if not auth_token:
        pytest.fail("Токен аутентификации не получен")
    return ForcePaymentClient(auth_token=auth_token)


@pytest.fixture(scope="module")
def payment_client(auth_token: str | None) -> PaymentClient:
    if not auth_token:
        pytest.fail("Токен аутентификации не получен")
    return PaymentClient(auth_token=auth_token)


@pytest.fixture(
    scope="module",
    params=settings.SUPPLIER_UUIDS,
    ids=[f"supplier_{i + 1}" for i in range(len(settings.SUPPLIER_UUIDS))],
)
def supplier_uuid(request: pytest.FixtureRequest) -> str:
    uuid_val = request.param
    logger.info(f"Используется SupplierUuid: {uuid_val}")
    return uuid_val


@pytest.fixture(scope="module")
def account_number(supplier_uuid: str) -> str:
    if supplier_uuid not in MAIN_ACCOUNT_BY_SUPPLIER:
        pytest.fail(f"Не найден AccountNumber для SupplierUuid: {supplier_uuid}.")
    acc_num = MAIN_ACCOUNT_BY_SUPPLIER[supplier_uuid]
    logger.info(f"Для SupplierUuid {supplier_uuid} выбран AccountNumber: {acc_num}")
    return acc_num


@pytest.fixture(scope="module")
def tariff_id() -> int:
    return settings.DEFAULT_TARIFF_ID


@pytest.fixture(scope="module")
def tariff_unique_name() -> str:
    return settings.DEFAULT_TARIFF_UNIQUE_NAME


@pytest.fixture(scope="module")
def tariff_type() -> int:
    return 1


@pytest.fixture(scope="module")
def tariff_info() -> dict[str, str]:
    return {
        "TariffId": str(settings.DEFAULT_TARIFF_ID),
        "TariffUniqueName": settings.DEFAULT_TARIFF_UNIQUE_NAME,
    }


@pytest.fixture(scope="module")
def tariff_scale_id() -> int:
    return settings.TARIFF_SCALE_ID


@pytest.fixture(scope="module")
def tariff_scale_unique_name() -> str:
    return settings.TARIFF_SCALE_UNIQUE_NAME


@pytest.fixture(scope="module")
def payment_tariff_unique_name(request) -> str:
    platform = getattr(request, "param", Platform.PLATFORM_A)
    return PAYMENT_TARIFF_BY_PLATFORM.get(platform, PAYMENT_TARIFF_BY_PLATFORM[Platform.PLATFORM_A])


@pytest.fixture(scope="module")
def payment_account_tag(request) -> str:
    platform = getattr(request, "param", Platform.PLATFORM_A)
    return PAYMENT_ACCOUNT_TAG_BY_PLATFORM.get(platform, PAYMENT_ACCOUNT_TAG_BY_PLATFORM[Platform.PLATFORM_A])


@pytest.fixture(scope="function")
def block_test_data() -> dict[str, str]:
    data = {
        "procedure_uuid": str(uuid.uuid4()),
        "procedure_number": f"{random.randint(1000, 9999)}",
    }
    logger.debug(f"Сгенерированы уникальные данные для блокировки: {data}")
    return data


@pytest.fixture(scope="module")
def shared_order_data(
    order_client: OrderClient,
    supplier_uuid: str,
    tariff_id: int,
) -> Iterator[dict[str, Any]]:
    """Заказ-предусловие на модуль; после тестов модуля отменяется."""
    procedure_number = f"{random.randint(1000, 9999)}"
    procedure_uuid = str(uuid.uuid4())
    price = "100"
    logger.info(f"Предусловие: Создание заказа с ProcedureNumber: {procedure_number}")
    try:
        response = order_client.create_order_with_params(
            supplier_uuid=supplier_uuid,
            tariff_id=tariff_id,
            price=price,
            procedure_number=procedure_number,
            procedure_uuid=procedure_uuid,
        )
        CustomAssertions.assert_status_code(response, 201)
        response_data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_field_exists(response_data, "OrderUuid")
        order_uuid = response_data["OrderUuid"]
        logger.info(f"Предусловие: Создан заказ с OrderUuid: {order_uuid}")
    except Exception as e:
        pytest.fail(f"Ошибка при создании заказа в предусловии: {e}")

    yield {
        "order_uuid": order_uuid,
        "procedure_uuid": procedure_uuid,
        "procedure_number": procedure_number,
    }

    try:
        order_client.cancel_order_by_uuid(
            order_uuid=order_uuid,
            supplier_uuid=supplier_uuid,
            reason="Автотест: отмена заказа-предусловия",
        )
        logger.info(f"Очистка: заказ {order_uuid} отменён")
    except Exception as e:
        logger.warning(f"Очистка: не удалось отменить заказ {order_uuid}: {e}")


@pytest.fixture(scope="function")
def block_cleanup(block_client: BlockClient) -> Iterator[list[dict[str, str]]]:
    """
    Список блокировок, созданных тестом; после теста каждая снимается.

    Тест добавляет {"ProcedureUuid": ..., "SupplierUuid": ...} сразу после
    успешной блокировки. Ошибка разблокировки (например, средства уже списаны
    payment) не роняет тест — только лог.
    """
    blocks: list[dict[str, str]] = []
    yield blocks
    for unblock_payload in blocks:
        try:
            response = block_client.unblock(unblock_payload)
            logger.info(f"Очистка: разблокировка {unblock_payload} → {response.status_code}")
        except Exception as e:
            logger.warning(f"Очистка: разблокировка {unblock_payload} не удалась: {e}")


@pytest.fixture(scope="module")
def account_info(supplier_uuid: str, account_number: str) -> dict[str, Any]:
    return {
        "SupplierUuid": supplier_uuid,
        "AccountNumber": account_number,
        "AccountTag": AccountTag.MAIN,
        "CurrencyCode": CURRENCY_RUB,
    }


@pytest.fixture(scope="module")
def suppliers_map() -> dict[str, dict[str, str]]:
    all_uuids = set(MAIN_ACCOUNT_BY_SUPPLIER) | set(SERVICES_ACCOUNT_BY_SUPPLIER)
    result_map = {}
    for uuid_val in all_uuids:
        result_map[uuid_val] = {
            AccountTag.MAIN: MAIN_ACCOUNT_BY_SUPPLIER.get(uuid_val, ""),
            AccountTag.SERVICES: SERVICES_ACCOUNT_BY_SUPPLIER.get(uuid_val, ""),
        }
    return result_map


@pytest.fixture(autouse=True, scope="function")
def set_test_context_for_current_supplier(request: pytest.FixtureRequest) -> Iterator[None]:
    """
    Добавляет в сообщения ассертов UUID контрагента и номер счёта.

    Фикстура НЕ зависит от supplier_uuid напрямую: иначе autouse-зависимость
    параметризует каждый тест по всем контрагентам, даже если тест их не использует.
    """
    if "supplier_uuid" in request.fixturenames:
        supplier_uuid = request.getfixturevalue("supplier_uuid")
        set_test_context(
            supplier_uuid=supplier_uuid,
            account_number=MAIN_ACCOUNT_BY_SUPPLIER.get(supplier_uuid),
        )
    else:
        set_test_context(supplier_uuid=None, account_number=None)
    yield
    set_test_context(supplier_uuid=None, account_number=None)
