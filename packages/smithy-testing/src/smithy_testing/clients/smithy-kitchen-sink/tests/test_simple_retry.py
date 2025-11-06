#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_http.testing import MockHTTPClient

from ..codegen.smithy_kitchen_sink.client import SmithyKitchenSink
from ..codegen.smithy_kitchen_sink.models import GetItemInput, ServiceError


def add_error_responses(http_client: MockHTTPClient, count: int) -> None:
    for _ in range(count):
        http_client.add_response(
            status=500,
            headers=[("X-Amzn-Errortype", "InternalError")],
            body=b'{"message": "Server Error"}',
        )


async def test_retry_eventually_succeeds(
    http_client: MockHTTPClient,
    client: SmithyKitchenSink,
):
    add_error_responses(http_client, 2)
    http_client.add_response(status=200, body=b'{"message": "success"}')

    response = await client.get_item(GetItemInput(id="test-123"))

    assert http_client.call_count == 3
    assert response.message == "success"


async def test_max_attempts_exceeded(
    http_client: MockHTTPClient,
    client: SmithyKitchenSink,
):
    add_error_responses(http_client, 5)

    with pytest.raises(ServiceError):
        await client.get_item(GetItemInput(id="test-123"))

    assert http_client.call_count == 5


async def test_throttling_error_retry(
    http_client: MockHTTPClient,
    client: SmithyKitchenSink,
):
    http_client.add_response(
        status=429,
        headers=[("X-Amzn-Errortype", "ThrottlingError")],
        body=b'{"message": "Rate exceeded"}',
    )
    http_client.add_response(200, body=b'{"message": "success"}')

    response = await client.get_item(GetItemInput(id="test-123"))

    assert http_client.call_count == 2
    assert response.message == "success"


async def test_non_retryable_error(
    http_client: MockHTTPClient,
    client: SmithyKitchenSink,
):
    http_client.add_response(
        status=400,
        headers=[("X-Amzn-Errortype", "ItemNotFound")],
        body=b'{"message": "Item not found"}',
    )

    with pytest.raises(ServiceError):
        await client.get_item(GetItemInput(id="nonexistent"))

    assert http_client.call_count == 1
