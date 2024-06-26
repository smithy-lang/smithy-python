#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest

from smithy_http.aio import HTTPRequest
from smithy_http.aio.crt import AWSCRTHTTPClient, AWSCRTHTTPClientConfig


@pytest.mark.skip("Needs to be replaced with a functional test due to flakiness.")
async def test_basic_request_local(sample_request: HTTPRequest) -> None:
    config = AWSCRTHTTPClientConfig()
    session = AWSCRTHTTPClient(client_config=config)
    response = await session.send(request=sample_request)
    assert response.status == 200
    print(f"{response=}")
    body = await response.consume_body_async()
    print(f"{body=}")
    assert b"aws" in body


@pytest.mark.skip("Needs to be replaced with a functional test due to flakiness.")
async def test_basic_request_http2(sample_request: HTTPRequest) -> None:
    config = AWSCRTHTTPClientConfig(force_http_2=True)
    session = AWSCRTHTTPClient(client_config=config)
    response = await session.send(request=sample_request)
    assert response.status == 200
    body = await response.consume_body_async()
    assert b"aws" in body
