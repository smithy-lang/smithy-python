#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os
from unittest.mock import patch

import pytest
from smithy_core import URI
from smithy_http.exceptions import SmithyHTTPError
from smithy_http.interfaces import HTTPProxyConfig


@pytest.mark.parametrize(
    "proxy_url, expected",
    [
        ("proxy.local ", URI(scheme="http", host="proxy.local", port=80)),
        (
            "http://proxy.local:3128",
            URI(scheme="http", host="proxy.local", port=3128),
        ),
        ("proxy.local:3128", URI(scheme="http", host="proxy.local", port=3128)),
        ("http://proxy.local", URI(scheme="http", host="proxy.local", port=80)),
        ("https://proxy.local", URI(scheme="https", host="proxy.local", port=443)),
        ("HTTP://Proxy.Local:8080/", URI(scheme="http", host="proxy.local", port=8080)),
        ("http://[::1]:3128", URI(scheme="http", host="::1", port=3128)),
        (
            "http://user:passw0rd@proxy.local:3128",
            URI(
                scheme="http",
                host="proxy.local",
                port=3128,
                username="user",
                password="passw0rd",
            ),
        ),
        (
            "http://user@proxy.local:3128",
            URI(scheme="http", host="proxy.local", port=3128, username="user"),
        ),
        (
            "http://:token@proxy.local:3128",
            URI(
                scheme="http",
                host="proxy.local",
                port=3128,
                username="",
                password="token",
            ),
        ),
        ("http://@proxy.local:3128", URI(scheme="http", host="proxy.local", port=3128)),
    ],
)
def test_proxy_url_parsing(proxy_url: str, expected: URI) -> None:
    proxy = HTTPProxyConfig._parse_url(proxy_url)  # pyright: ignore[reportPrivateUsage]
    assert proxy == expected
    assert proxy.username == expected.username
    assert proxy.password == expected.password


def test_proxy_by_destination_scheme() -> None:
    config = HTTPProxyConfig(
        http_proxy="http://plain.local:8080", https_proxy="http://secure.local:8081"
    )
    http_proxy = config.proxy_for(URI(scheme="http", host="example.com"))
    https_proxy = config.proxy_for(URI(scheme="https", host="example.com"))
    assert http_proxy is not None and http_proxy.host == "plain.local"
    assert https_proxy is not None and https_proxy.host == "secure.local"


def test_no_proxy_unknown_scheme() -> None:
    config = HTTPProxyConfig(http_proxy="http://proxy:1", https_proxy="http://proxy:1")
    assert config.proxy_for(URI(scheme="ws", host="example.com")) is None


def test_empty_config_disables_proxy() -> None:
    assert HTTPProxyConfig().proxy_for(URI(host="example.com")) is None


@pytest.mark.parametrize(
    "proxy_url, message",
    [
        ("socks5://proxy.local:1080", "Unsupported proxy URL scheme"),
        ("http://proxy.local:noport", "invalid port"),
        ("http://:8080", "no host"),
    ],
)
def test_invalid_proxy_fails(proxy_url: str, message: str) -> None:
    with pytest.raises(SmithyHTTPError, match=message):
        HTTPProxyConfig(https_proxy=proxy_url)


def test_invalid_proxy_error_omits_credentials() -> None:
    with pytest.raises(SmithyHTTPError) as exc_info:
        HTTPProxyConfig(https_proxy="http://user:passw0rd@proxy.local:bad")
    assert "passw0rd" not in str(exc_info.value)


@pytest.mark.parametrize(
    "no_proxy, host, port, bypassed",
    [
        # should be bypassed
        (".example.com", "example.com", None, True),
        (".example.com", "api.example.com", None, True),
        ("EXAMPLE.com", "Api.Example.COM", None, True),
        ("other.com, example.com", "example.com", None, True),
        ("example.com:8443", "example.com", 8443, True),
        ("example.com:443", "example.com", None, True),
        ("169.254.169.254", "169.254.169.254", None, True),
        ("[::1]", "::1", None, True),
        ("[::1]:8443", "::1", 8443, True),
        ("example.com:abc, other.com", "other.com", None, True),
        # should not be bypassed
        ("[::1]:8443", "::1", None, False),
        # IPv6 entries need brackets
        ("::1", "::1", None, False),
        ("::1", "fd00::1", None, False),
        ("example.com", "notexample.com", None, False),
        (" , ,", "example.com", None, False),
        ("example.com:8443", "example.com", None, False),
        ("example.com:abc", "example.com", None, False),
        ("example.com:", "example.com", None, False),
    ],
)
def test_bypass_matching(
    no_proxy: str, host: str, port: int | None, bypassed: bool
) -> None:
    config = HTTPProxyConfig(https_proxy="http://proxy.local:3128", no_proxy=no_proxy)
    proxy = config.proxy_for(URI(scheme="https", host=host, port=port))
    assert (proxy is None) is bypassed


def test_from_environment() -> None:
    environ = {
        "HTTP_PROXY": "http://plain.local:1",
        "HTTPS_PROXY": "http://secure.local:2",
        "NO_PROXY": "somedomain",
    }
    assert HTTPProxyConfig.from_environment(environ) == HTTPProxyConfig(
        http_proxy="http://plain.local:1",
        https_proxy="http://secure.local:2",
        no_proxy="somedomain",
    )


@pytest.mark.parametrize(
    "environ",
    [
        {},
        {"HTTPS_PROXY": ""},
        {"https_proxy": "", "HTTPS_PROXY": ""},
    ],
)
def test_proxy_unset(environ: dict[str, str]) -> None:
    assert HTTPProxyConfig.from_environment(environ) == HTTPProxyConfig()


def test_empty_lowercase_falls_back_to_uppercase() -> None:
    environ = {"https_proxy": "", "HTTPS_PROXY": "http://upper.local:2"}
    assert HTTPProxyConfig.from_environment(environ).https_proxy == (
        "http://upper.local:2"
    )


@pytest.mark.parametrize(
    "name, value",
    [
        ("HTTPS_PROXY", "socks5h://127.0.0.1:1080"),
        ("https_proxy", "http://user:passw0rd@proxy.local:noport"),
        ("HTTP_PROXY", "http://:3128"),
    ],
)
def test_ignores_unusable_proxy_urls(
    name: str, value: str, caplog: pytest.LogCaptureFixture
) -> None:
    config = HTTPProxyConfig.from_environment({name: value, "NO_PROXY": "somedomain"})

    assert config == HTTPProxyConfig(no_proxy="somedomain")
    assert f"Ignoring the {name.lower()} environment variable" in caplog.text
    assert "passw0rd" not in caplog.text


def test_keeps_usable_proxy_when_other_is_unusable() -> None:
    environ = {
        "HTTP_PROXY": "socks5://proxy.local:1080",
        "HTTPS_PROXY": "http://proxy.local:3128",
    }
    assert HTTPProxyConfig.from_environment(environ) == HTTPProxyConfig(
        https_proxy="http://proxy.local:3128"
    )


def test_defaults_to_os_environ() -> None:
    with patch.dict(os.environ, {"HTTPS_PROXY": "http://secure.local:2"}, clear=True):
        assert HTTPProxyConfig.from_environment() == HTTPProxyConfig(
            https_proxy="http://secure.local:2"
        )


@pytest.mark.parametrize(
    "proxy_url",
    [
        "http://user:passw0rd@proxy.local:3128",
        "user:passw0rd@proxy.local:3128",
        "http://:passw0rd@proxy.local:3128",
        "http://user@proxy.local:3128",
        "http://proxy.local:3128",
    ],
)
def test_repr_omits_password(proxy_url: str) -> None:
    config = HTTPProxyConfig(http_proxy=proxy_url, https_proxy=proxy_url)
    rendered = repr(config)
    assert "passw0rd" not in rendered
    assert str(config) == rendered
    expected = HTTPProxyConfig._parse_url(proxy_url)  # pyright: ignore[reportPrivateUsage]
    assert f"http_proxy={expected!r}" in rendered
    assert f"https_proxy={expected!r}" in rendered
