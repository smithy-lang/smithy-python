#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core import URI
from smithy_core.aio.utils import async_list

from smithy_http import Field, Fields
from smithy_http.aio import HTTPRequest, HTTPResponse


async def test_request() -> None:
    uri = URI(host="test.aws.dev")
    headers = Fields([Field(name="foo", values=["bar"])])
    request = HTTPRequest(
        method="GET",
        destination=uri,
        fields=headers,
        body=async_list([b"test body"]),
    )

    assert request.method == "GET"
    assert request.destination == uri
    assert request.fields == headers
    request_body = b"".join([chunk async for chunk in request.body])
    assert request_body == b"test body"


async def test_response() -> None:
    headers = Fields([Field(name="foo", values=["bar"])])
    response = HTTPResponse(
        status=200,
        fields=headers,
        body=async_list([b"test body"]),
    )

    assert response.status == 200
    assert response.fields == headers
    response_body = await response.consume_body()
    assert response_body == b"test body"
