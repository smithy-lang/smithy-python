# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from smithy_python._private import URI, Field, Fields, HostType
from smithy_python._private.http import (
    HTTPRequest,
    HTTPResponse,
    StaticEndpointParams,
    StaticEndpointResolver,
)
from smithy_python.async_utils import async_list
from smithy_python.exceptions import SmithyHTTPException


def test_uri_basic() -> None:
    uri = URI(
        host="test.aws.dev",
        path="/my/path",
        query="foo=bar",
    )

    assert uri.host == "test.aws.dev"
    assert uri.path == "/my/path"
    assert uri.query == "foo=bar"
    assert uri.netloc == "test.aws.dev"
    assert uri.build() == "https://test.aws.dev/my/path?foo=bar"


def test_uri_all_fields_present() -> None:
    uri = URI(
        host="test.aws.dev",
        path="/my/path",
        scheme="http",
        query="foo=bar",
        port=80,
        username="abc",
        password="def",
        fragment="frag",
    )

    assert uri.host == "test.aws.dev"
    assert uri.path == "/my/path"
    assert uri.scheme == "http"
    assert uri.query == "foo=bar"
    assert uri.port == 80
    assert uri.username == "abc"
    assert uri.password == "def"
    assert uri.fragment == "frag"
    assert uri.netloc == "abc:def@test.aws.dev:80"
    assert uri.build() == "http://abc:def@test.aws.dev:80/my/path?foo=bar#frag"


def test_uri_without_scheme_field() -> None:
    uri = URI(
        host="test.aws.dev",
        path="/my/path",
        query="foo=bar",
        port=80,
        username="abc",
        password="def",
        fragment="frag",
    )
    # scheme should default to https
    assert uri.scheme == "https"
    assert uri.build() == "https://abc:def@test.aws.dev:80/my/path?foo=bar#frag"


def test_uri_without_port_number() -> None:
    uri = URI(
        host="test.aws.dev",
        path="/my/path",
        scheme="http",
        query="foo=bar",
        username="abc",
        password="def",
        fragment="frag",
    )
    # by default, the port is omitted from computed netloc and built URI string
    assert uri.port is None
    assert uri.netloc == "abc:def@test.aws.dev"
    assert uri.build() == "http://abc:def@test.aws.dev/my/path?foo=bar#frag"


def test_uri_ipv6_host() -> None:
    uri = URI(host="::1")
    assert uri.host == "::1"
    assert uri.netloc == "[::1]"
    assert uri.build() == "https://[::1]"
    assert uri.host_type == HostType.IPv6


def test_uri_escaped_path() -> None:
    uri = URI(host="test.aws.dev", path="/%20%2F")
    assert uri.path == "/%20%2F"
    assert uri.build() == "https://test.aws.dev/%20%2F"


def test_uri_password_but_no_username() -> None:
    uri = URI(host="test.aws.dev", password="def")
    assert uri.password == "def"
    # the password is ignored if no username is present
    assert uri.netloc == "test.aws.dev"


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


async def test_endpoint_provider_with_uri_string() -> None:
    params = StaticEndpointParams(
        uri="https://foo.example.com:8080/spam?foo=bar&foo=baz"
    )
    expected = URI(
        host="foo.example.com",
        path="/spam",
        scheme="https",
        query="foo=bar&foo=baz",
        port=8080,
    )
    resolver = StaticEndpointResolver()
    result = await resolver.resolve_endpoint(params=params)
    assert result.uri == expected
    assert result.headers == Fields([])


async def test_endpoint_provider_with_uri_object() -> None:
    expected = URI(
        host="foo.example.com",
        path="/spam",
        scheme="https",
        query="foo=bar&foo=baz",
        port=8080,
    )
    params = StaticEndpointParams(uri=expected)
    resolver = StaticEndpointResolver()
    result = await resolver.resolve_endpoint(params=params)
    assert result.uri == expected
    assert result.headers == Fields([])


@pytest.mark.parametrize(
    "input_uri, host_type",
    [
        (URI(host="example.com"), HostType.DOMAIN),
        (URI(host="001:db8:3333:4444:5555:6666:7777:8888"), HostType.IPv6),
        (URI(host="::"), HostType.IPv6),
        (URI(host="2001:db8::"), HostType.IPv6),
        (URI(host="192.168.1.1"), HostType.IPv4),
    ],
)
def test_host_type(input_uri: URI, host_type: HostType) -> None:
    assert input_uri.host_type == host_type


@pytest.mark.parametrize(
    "input_host", ["example.com\t", "umlaut-äöü.aws.dev", "foo\nbar.com"]
)
def test_uri_init_with_disallowed_characters(input_host: str) -> None:
    with pytest.raises(SmithyHTTPException):
        URI(host=input_host)
