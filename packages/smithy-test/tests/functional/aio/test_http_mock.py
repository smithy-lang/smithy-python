#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest

pytest.importorskip("restjson")

from restjson.aio.client import AsyncRestJsonProtocolClient
from restjson.aio.config import AsyncRestJsonProtocolConfig
from restjson.client import RestJsonProtocolClient
from restjson.models import SimpleScalarPropertiesInput
from smithy_test import HTTPMockError, HTTPMockMismatchError
from smithy_test.aio import mock_async


async def _client() -> AsyncRestJsonProtocolClient:
    return AsyncRestJsonProtocolClient(
        await AsyncRestJsonProtocolConfig.resolve(
            region="us-west-2",
            aws_access_key_id="real",
            aws_secret_access_key="real",
        )
    )


async def test_matches_and_responds() -> None:
    async with await _client() as client:
        controller = await mock_async(client)
        controller.expect_request(
            path="/SimpleScalarProperties",
            headers={"Authorization": "/Credential=HTTP_MOCK//"},
            body=lambda body: b'"stringValue":"value"' in body,
        ).respond_with(body=b'{"stringValue": "hi"}')

        output = await client.simple_scalar_properties(
            SimpleScalarPropertiesInput(string_value="value")
        )

    assert output.string_value == "hi"
    assert controller.requests[0].body == b'{"stringValue":"value"}'


async def test_returns_none_without_response() -> None:
    async with await _client() as client:
        (await mock_async(client)).expect_request()

        assert (
            await client.simple_scalar_properties(SimpleScalarPropertiesInput()) is None
        )


async def test_raises_without_expectations() -> None:
    async with await _client() as client:
        await mock_async(client)

        with pytest.raises(HTTPMockError):
            await client.simple_scalar_properties(SimpleScalarPropertiesInput())


async def test_raises_on_exit_with_unmet_expectations() -> None:
    async with await _client() as client:
        with pytest.raises(HTTPMockMismatchError, match="matched 1 of 2 requests"):
            with await mock_async(client) as controller:
                controller.expect_request().times(2)

                await client.simple_scalar_properties(SimpleScalarPropertiesInput())


async def test_rejects_a_sync_client() -> None:
    with pytest.raises(TypeError, match=r"smithy_test\.mock\(\)"):
        await mock_async(RestJsonProtocolClient())  # type: ignore[arg-type]
