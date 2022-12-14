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

from smithy_python._private.http import (
    URL,
    Request,
    Response,
    StaticEndpointParams,
    StaticEndpointResolver,
)


def test_url() -> None:
    url = URL(
        host="test.com",
        path="/my/path",
        scheme="http",
        query_params=[("foo", "bar")],
        port=80,
    )

    assert url.host == "test.com"
    assert url.path == "/my/path"
    assert url.scheme == "http"
    assert url.query_params == [("foo", "bar")]
    assert url.port == 80


def test_request() -> None:
    url = URL(host="test.com")
    request = Request(
        url=url,
        headers=[("foo", "bar")],
        body=b"test body",
    )

    assert request.method == "GET"
    assert request.url == url
    assert request.headers == [("foo", "bar")]
    assert request.body == b"test body"


def test_resposne() -> None:
    response = Response(
        status_code=200,
        headers=[("foo", "bar")],
        body=b"test body",
    )

    assert response.status_code == 200
    assert response.headers == [("foo", "bar")]
    assert response.body == b"test body"


async def test_endpoint_provider_with_url_string() -> None:
    params = StaticEndpointParams(
        url="https://foo.example.com/spam:8080?foo=bar&foo=baz"
    )
    expected = URL(
        host="foo.example.com",
        path="/spam",
        scheme="https",
        query_params=[("foo", "bar"), ("foo", "baz")],
        port=8080,
    )
    resolver = StaticEndpointResolver()
    result = await resolver.resolve_endpoint(params=params)
    assert result.url == expected
    assert result.headers == []


async def test_endpoint_provider_with_url_object() -> None:
    expected = URL(
        host="foo.example.com",
        path="/spam",
        scheme="https",
        query_params=[("foo", "bar"), ("foo", "baz")],
        port=8080,
    )
    params = StaticEndpointParams(url=expected)
    resolver = StaticEndpointResolver()
    result = await resolver.resolve_endpoint(params=params)
    assert result.url == expected
    assert result.headers == []
