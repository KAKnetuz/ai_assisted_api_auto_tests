"""
Тесты блокировки средств (платформы platform_a и platform_b).
"""
import random
import uuid
from typing import Any

import pytest

from integration_tests.api_clients.block_client import BlockClient
from integration_tests.config.constants import BLOCK_PLATFORMS, AccountTag
from integration_tests.helpers.assertions import CustomAssertions
from integration_tests.helpers.data_generators import DataGenerators


@pytest.mark.smoke
class TestBlock:

    @pytest.mark.parametrize("endpoint", BLOCK_PLATFORMS, ids=lambda p: f"{p}_block")
    def test_pos_block_with_valid_data(
        self,
        block_client: BlockClient,
        supplier_uuid: str,
        account_number: str,
        tariff_unique_name: str,
        endpoint: str,
        request: pytest.FixtureRequest,
    ) -> None:
        price = "100"
        procedure_number = f"{random.randint(1000, 9999)}"
        procedure_uuid = str(uuid.uuid4())

        payload = {
            "Price": price,
            "ProcedureNumber": procedure_number,
            "ProcedureUuid": procedure_uuid,
            "SupplierUuid": supplier_uuid,
            "TariffUniqueName": tariff_unique_name,
            "AccountNumber": account_number,
            "AccountTag": AccountTag.MAIN,
        }

        response = block_client.block(payload, endpoint=endpoint)

        CustomAssertions.assert_status_code(response, [200, 201])
        data = CustomAssertions.assert_valid_json(response)
        CustomAssertions.assert_block_success(data)

        def cleanup_unblock():
            try:
                unblock_payload: dict[str, Any] = {
                    "ProcedureUuid": procedure_uuid,
                    "SupplierUuid": supplier_uuid,
                }
                block_client.unblock(unblock_payload)
            except Exception:
                pass

        request.addfinalizer(cleanup_unblock)

    @pytest.mark.parametrize("endpoint", BLOCK_PLATFORMS, ids=lambda p: f"{p}_block")
    @pytest.mark.parametrize(
        "field_to_remove",
        ["SupplierUuid", "Price", "ProcedureNumber", "ProcedureUuid"],
        ids=["no_supplier", "no_price", "no_procedure_number", "no_procedure_uuid"],
    )
    def test_neg_block_missing_required_field(
        self,
        block_client: BlockClient,
        supplier_uuid: str,
        account_number: str,
        tariff_unique_name: str,
        endpoint: str,
        field_to_remove: str,
    ) -> None:
        payload = {
            "Price": "100",
            "ProcedureNumber": DataGenerators.generate_procedure_number(),
            "ProcedureUuid": DataGenerators.generate_uuid(),
            "SupplierUuid": supplier_uuid,
            "TariffUniqueName": tariff_unique_name,
            "AccountNumber": account_number,
            "AccountTag": AccountTag.MAIN,
        }
        del payload[field_to_remove]

        response = block_client.block(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, [400, 422])

    @pytest.mark.parametrize("endpoint", BLOCK_PLATFORMS, ids=lambda p: f"{p}_block")
    @pytest.mark.parametrize(
        "field_name,invalid_value",
        [
            ("SupplierUuid", "неправильный-uuid-123"),
            ("Price", True),
            ("ProcedureNumber", [400, 422]),
            ("ProcedureUuid", "неправильный-uuid-123"),
        ],
        ids=["invalid_supplier", "invalid_price", "invalid_procedure_number", "invalid_procedure_uuid"],
    )
    def test_neg_block_invalid_field_format(
        self,
        block_client: BlockClient,
        supplier_uuid: str,
        account_number: str,
        tariff_unique_name: str,
        endpoint: str,
        field_name: str,
        invalid_value: Any,
    ) -> None:
        payload = {
            "Price": "100",
            "ProcedureNumber": DataGenerators.generate_procedure_number(),
            "ProcedureUuid": DataGenerators.generate_uuid(),
            "SupplierUuid": supplier_uuid,
            "TariffUniqueName": tariff_unique_name,
            "AccountNumber": account_number,
            "AccountTag": AccountTag.MAIN,
        }
        payload[field_name] = invalid_value

        response = block_client.block(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, [400, 422])

    @pytest.mark.parametrize("endpoint", BLOCK_PLATFORMS, ids=lambda p: f"{p}_block")
    @pytest.mark.parametrize(
        "field_name",
        ["SupplierUuid", "Price", "ProcedureNumber", "ProcedureUuid"],
        ids=["empty_supplier", "empty_price", "empty_procedure_number", "empty_procedure_uuid"],
    )
    def test_neg_block_empty_field(
        self,
        block_client: BlockClient,
        supplier_uuid: str,
        account_number: str,
        tariff_unique_name: str,
        endpoint: str,
        field_name: str,
    ) -> None:
        payload = {
            "Price": "100",
            "ProcedureNumber": DataGenerators.generate_procedure_number(),
            "ProcedureUuid": DataGenerators.generate_uuid(),
            "SupplierUuid": supplier_uuid,
            "TariffUniqueName": tariff_unique_name,
            "AccountNumber": account_number,
            "AccountTag": AccountTag.MAIN,
        }
        payload[field_name] = ""

        response = block_client.block(payload, endpoint=endpoint)
        CustomAssertions.assert_status_code(response, [400, 422])

    @pytest.mark.parametrize("endpoint", BLOCK_PLATFORMS, ids=lambda p: f"{p}_block")
    def test_neg_block_nonexistent_supplier(
        self,
        block_client: BlockClient,
        account_number: str,
        tariff_unique_name: str,
        endpoint: str,
    ) -> None:
        response = block_client.block_with_params(
            supplier_uuid=DataGenerators.generate_nonexistent_uuid(),
            account_number=account_number,
            tariff_unique_name=tariff_unique_name,
            price="100",
            endpoint=endpoint,
        )

        if response.status_code in [200, 201]:
            data = CustomAssertions.assert_valid_json(response)
            assert data.get("IsBlocked") is False, (
                f"Для несуществующего SupplierUuid ожидается IsBlocked=False, получено {data.get('IsBlocked')!r}"
            )
        else:
            assert response.status_code in [404, 422], (
                f"Ожидался статус 200/201 (с IsBlocked=False) или 404/422, получен {response.status_code}"
            )
