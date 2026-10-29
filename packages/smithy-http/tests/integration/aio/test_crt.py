#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest
from smithy_core.aio.utils import read_streaming_blob_async
from smithy_http import HTTPRequest
from smithy_http.aio.crt import AsyncAWSCRTHTTPClient, AsyncAWSCRTHTTPClientConfig


@pytest.mark.skip("Needs to be replaced with a functional test due to flakiness.")
async def test_basic_request_local(sample_request: HTTPRequest) -> None:
    config = AsyncAWSCRTHTTPClientConfig()
    session = AsyncAWSCRTHTTPClient(client_config=config)
    response = await session.send(request=sample_request)
    assert response.status == 200
    body = await read_streaming_blob_async(response.body)
    assert b"aws" in body


@pytest.mark.skip("Needs to be replaced with a functional test due to flakiness.")
async def test_basic_request_http2(sample_request: HTTPRequest) -> None:
    config = AsyncAWSCRTHTTPClientConfig(force_http_2=True)
    session = AsyncAWSCRTHTTPClient(client_config=config)
    response = await session.send(request=sample_request)
    assert response.status == 200
    body = await read_streaming_blob_async(response.body)
    assert b"aws" in body
