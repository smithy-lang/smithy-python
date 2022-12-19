# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import pytest

from smithy_python._private.http import URI, Field, Fields, HTTPRequest
from smithy_python._private.http.crt import AwsCrtHttpClient, AwsCrtHttpClientConfig
from smithy_python.async_utils import async_list


@pytest.fixture
def aws_request() -> HTTPRequest:
    headers = Fields(
        [
            Field(name="host", values=["aws.amazon.com"]),
            Field(name="user-agent", values=["smithy-python-test"]),
        ]
    )
    return HTTPRequest(
        method="GET",
        destination=URI(host="aws.amazon.com"),
        fields=headers,
        body=async_list([]),
    )


async def test_basic_request_local(aws_request: HTTPRequest) -> None:
    config = AwsCrtHttpClientConfig()
    session = AwsCrtHttpClient(config=config)
    response = await session.send(aws_request)
    assert response.status == 200
    body = await response.consume_body()
    assert b"aws" in body
    assert response.done


async def test_async_basic_request_http2(aws_request: HTTPRequest) -> None:
    config = AwsCrtHttpClientConfig(force_http_2=True)
    session = AwsCrtHttpClient(config=config)
    response = await session.send(aws_request)
    assert response.status == 200
    body = await response.consume_body()
    assert b"aws" in body
    assert response.done
