#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import pytest
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.aio.utils import read_streaming_blob_async
from smithy_http.aio.testing import AsyncMockHTTPClient
from smithy_http.testing import MockHTTPClientError, create_test_request


def test_supports_duplex_streaming():
    # Declared True so generated duplex stream operations can be unit tested
    # against this client.
    assert AsyncMockHTTPClient.SUPPORTS_DUPLEX_STREAMING is True


async def test_default_response():
    # Test error when no responses are queued
    mock_client = AsyncMockHTTPClient()
    request = create_test_request()

    with pytest.raises(MockHTTPClientError, match="No responses queued"):
        await mock_client.send(request)


async def test_queued_responses_fifo():
    # Test responses are returned in FIFO order
    mock_client = AsyncMockHTTPClient()
    mock_client.add_response(status=404, body=b"not found")
    mock_client.add_response(status=500, body=b"server error")

    request = create_test_request()

    response1 = await mock_client.send(request)
    assert response1.status == 404
    assert await read_streaming_blob_async(response1.body) == b"not found"

    response2 = await mock_client.send(request)
    assert response2.status == 500
    assert await read_streaming_blob_async(response2.body) == b"server error"

    assert mock_client.call_count == 2


async def test_captured_requests():
    # Test all requests are captured for inspection
    mock_client = AsyncMockHTTPClient()
    mock_client.add_response()
    mock_client.add_response()

    request1 = create_test_request(
        method="GET",
        host="test.aws.dev",
    )
    request2 = create_test_request(
        method="POST",
        host="test.aws.dev",
        body=b'{"name": "test"}',
    )

    await mock_client.send(request1)
    await mock_client.send(request2)

    captured = mock_client.captured_requests
    assert len(captured) == 2
    assert captured[0].method == "GET"
    assert captured[1].method == "POST"
    assert captured[1].body == b'{"name": "test"}'


async def test_response_headers():
    # Test response headers are properly set
    mock_client = AsyncMockHTTPClient()
    mock_client.add_response(
        status=201,
        headers=[
            ("Content-Type", "application/json"),
            ("X-Amz-Custom", "test"),
        ],
        body=b'{"id": 123}',
    )
    request = create_test_request()
    response = await mock_client.send(request)

    assert response.status == 201
    assert "Content-Type" in response.fields
    assert response.fields["Content-Type"].as_string() == "application/json"
    assert "X-Amz-Custom" in response.fields
    assert response.fields["X-Amz-Custom"].as_string() == "test"


async def test_call_count_tracking():
    # Test call count is tracked correctly
    mock_client = AsyncMockHTTPClient()
    mock_client.add_response()
    mock_client.add_response()

    request = create_test_request()

    assert mock_client.call_count == 0

    await mock_client.send(request)
    assert mock_client.call_count == 1

    await mock_client.send(request)
    assert mock_client.call_count == 2


async def test_captured_requests_copy():
    # Test that captured_requests returns a copy to prevent modifications
    mock_client = AsyncMockHTTPClient()
    mock_client.add_response()

    request = create_test_request()

    await mock_client.send(request)

    captured1 = mock_client.captured_requests
    captured2 = mock_client.captured_requests

    # Should be different list objects
    assert captured1 is not captured2
    # But with same content
    assert len(captured1) == len(captured2) == 1


async def test_responds_with_a_stream():
    client = AsyncMockHTTPClient()
    stream = AsyncBytesReader(b"streamed")
    client.add_response(body=stream)

    response = await client.send(create_test_request())

    assert response.body is stream
    assert await read_streaming_blob_async(response.body) == b"streamed"
