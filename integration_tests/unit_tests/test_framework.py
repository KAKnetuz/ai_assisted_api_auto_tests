"""
Офлайн-тесты самого фреймворка (без обращения к API).
Запускаются в CI: ловят поломки маршрутизации, политики повторов и маскирования.
"""

import pytest

from integration_tests.api_clients.base_api_client import BaseAPIClient
from integration_tests.config import endpoints
from integration_tests.config.endpoints import Platform
from integration_tests.utils.logger import CustomLogger

PLATFORM_MAPPINGS = {
    "ACCOUNT_INFO_ENDPOINTS": endpoints.ACCOUNT_INFO_ENDPOINTS,
    "ORDER_CREATE_ENDPOINTS": endpoints.ORDER_CREATE_ENDPOINTS,
    "ORDER_LIST_ENDPOINTS": endpoints.ORDER_LIST_ENDPOINTS,
    "ORDER_STATUS_ENDPOINTS": endpoints.ORDER_STATUS_ENDPOINTS,
    "TARIFF_INFO_ENDPOINTS": endpoints.TARIFF_INFO_ENDPOINTS,
    "BLOCK_ENDPOINTS": endpoints.BLOCK_ENDPOINTS,
    "PAYMENT_ENDPOINTS": endpoints.PAYMENT_ENDPOINTS,
}


@pytest.mark.parametrize("mapping", PLATFORM_MAPPINGS.values(), ids=PLATFORM_MAPPINGS.keys())
def test_resolve_returns_url_for_every_supported_platform(mapping) -> None:
    for platform, url in mapping.items():
        assert endpoints.resolve(mapping, str(platform), "op") == url
        assert url.startswith("/api/")


def test_resolve_rejects_unsupported_platform() -> None:
    with pytest.raises(ValueError, match=r"Неизвестная платформа для block: 'core'"):
        endpoints.resolve(endpoints.BLOCK_ENDPOINTS, Platform.CORE, "block")


def test_retry_policy_does_not_repeat_post() -> None:
    client = BaseAPIClient(base_url="http://localhost")
    retry = client.session.get_adapter("https://").max_retries
    assert "GET" in retry.allowed_methods
    assert "POST" not in retry.allowed_methods


@pytest.mark.parametrize(
    "data",
    [
        {"token": "SECRET-0123456789-abcdefghij-END"},
        {"Data": {"access_token": "SECRET-0123456789-abcdefghij-END"}},
        [{"Authorization": "Bearer SECRET-0123456789-abcdefghij-END"}],
    ],
    ids=["flat", "nested", "list"],
)
def test_sensitive_values_are_masked(data) -> None:
    masked = CustomLogger("unit-test")._mask_sensitive_data(data)
    assert "SECRET-0123456789-abcdefghij-END" not in str(masked)


def test_non_sensitive_values_are_kept() -> None:
    data = {"SupplierUuid": "11111111-1111-1111-1111-111111111111", "Price": "100"}
    assert CustomLogger("unit-test")._mask_sensitive_data(data) == data
