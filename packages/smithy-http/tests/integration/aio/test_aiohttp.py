#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest

from smithy_http.aio import HTTPRequest
from smithy_http.aio.aiohttp import AIOHTTPClient, AIOHTTPClientConfig


@pytest.mark.skip("Needs to be replaced with a functional test due to flakiness.")
async def test_basic_request_local(sample_request: HTTPRequest) -> None:
    config = AIOHTTPClientConfig()
    session = AIOHTTPClient(client_config=config)
    response = await session.send(request=sample_request)
    assert response.status == 200
    body = await response.consume_body_async()
    assert b"aws" in body
