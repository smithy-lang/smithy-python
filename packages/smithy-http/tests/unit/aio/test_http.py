#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core import URI
from smithy_core.aio.utils import list_async, read_streaming_blob_async
from smithy_http import Field, Fields, HTTPRequest, HTTPResponse


async def test_request() -> None:
    uri = URI(host="test.aws.dev")
    headers = Fields([Field(name="foo", values=["bar"])])
    request = HTTPRequest(
        method="GET",
        destination=uri,
        fields=headers,
        body=list_async([b"test body"]),
    )

    assert request.method == "GET"
    assert request.destination == uri
    assert request.fields == headers
    assert await read_streaming_blob_async(request.body) == b"test body"


async def test_response() -> None:
    headers = Fields([Field(name="foo", values=["bar"])])
    response = HTTPResponse(
        status=200,
        fields=headers,
        body=list_async([b"test body"]),
    )

    assert response.status == 200
    assert response.fields == headers
    assert await read_streaming_blob_async(response.body) == b"test body"
