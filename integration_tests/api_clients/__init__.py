"""
Пакет API-клиентов (Service Layer).

Экспортирует всех клиентов для удобного импорта:
    from integration_tests.api_clients import (
        AuthClient, AccountClient, OrderClient, TariffClient,
        BlockClient, OperationClient, CounterpartyClient, UnpaidOrdersClient,
    )
"""

from integration_tests.api_clients.account_client import AccountClient
from integration_tests.api_clients.auth_client import AuthClient
from integration_tests.api_clients.block_client import BlockClient
from integration_tests.api_clients.counterparty_client import CounterpartyClient
from integration_tests.api_clients.operation_client import OperationClient
from integration_tests.api_clients.order_client import OrderClient
from integration_tests.api_clients.tariff_client import TariffClient
from integration_tests.api_clients.unpaid_orders_client import UnpaidOrdersClient

__all__ = [
    "AccountClient",
    "AuthClient",
    "BlockClient",
    "CounterpartyClient",
    "OperationClient",
    "OrderClient",
    "TariffClient",
    "UnpaidOrdersClient",
]
