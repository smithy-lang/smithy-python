#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import pytest

from smithy_core import URI, HostType
from smithy_core.exceptions import SmithyException


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
    with pytest.raises(SmithyException):
        URI(host=input_host)
