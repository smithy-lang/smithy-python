#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_http.aio import HTTPRequest
from smithy_http.aio.aiohttp import AIOHTTPClient, AIOHTTPClientConfig


async def test_basic_request_local(sample_request: HTTPRequest) -> None:
    config = AIOHTTPClientConfig()
    session = AIOHTTPClient(client_config=config)
    response = await session.send(request=sample_request)
    assert response.status == 200
    body = await response.consume_body()
    assert b"aws" in body
