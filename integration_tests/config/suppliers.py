"""
Тестовые данные контрагентов: соответствие SupplierUuid → номера лицевых счетов.
Номера счетов — плейсхолдеры, реальные значения подставляются через .env.
"""
from typing import Final

from integration_tests.config.constants import AccountTag
from integration_tests.config.settings import settings

MAIN_ACCOUNT_BY_SUPPLIER: Final[dict[str, str]] = {
    settings.SUPPLIER_UUIDS[0]: "account_1",
    settings.SUPPLIER_UUIDS[1]: "account_2",
    settings.SUPPLIER_UUIDS[2]: "account_3",
}

SERVICES_ACCOUNT_BY_SUPPLIER: Final[dict[str, str]] = {
    settings.SUPPLIER_UUIDS[0]: "account_services_1",
    settings.SUPPLIER_UUIDS[1]: "account_services_2",
    settings.SUPPLIER_UUIDS[2]: "account_services_3",
}

ACCOUNTS_BY_TAG: Final[dict[AccountTag, dict[str, str]]] = {
    AccountTag.MAIN: MAIN_ACCOUNT_BY_SUPPLIER,
    AccountTag.SERVICES: SERVICES_ACCOUNT_BY_SUPPLIER,
}
