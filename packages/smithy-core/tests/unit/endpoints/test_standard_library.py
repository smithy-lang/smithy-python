# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any

import pytest
from smithy_core.endpoints._standard_library import STANDARD_FUNCTIONS

FUNCTIONS = STANDARD_FUNCTIONS


@pytest.mark.parametrize(
    "args, expected",
    [
        (("abcdefg", 0, 4, False), "abcd"),
        (("abcdefg", 0, 4, True), "defg"),
        (("abcdefg", 1, 3, True), "ef"),
        (("abc", 0, 4, False), None),
        (("abcdéfg", 0, 4, False), None),
    ],
)
def test_substring(args: tuple[Any, ...], expected: str | None) -> None:
    assert FUNCTIONS["substring"](*args) == expected


@pytest.mark.parametrize(
    "value, allow_sub_domains, expected",
    [
        ("us-east-1", False, True),
        ("3abc4", False, True),
        ("a" * 64, False, False),
        ("-abc", False, False),
        ("", False, False),
        ("a.b", False, False),
        ("a.b", True, True),
        ("a..b", True, False),
        ("a.", True, False),
    ],
)
def test_is_valid_host_label(
    value: str, allow_sub_domains: bool, expected: bool
) -> None:
    assert FUNCTIONS["isValidHostLabel"](value, allow_sub_domains) is expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (
            "https://example.com",
            {
                "scheme": "https",
                "authority": "example.com",
                "path": "",
                "normalizedPath": "/",
                "isIp": False,
            },
        ),
        (
            "http://127.0.0.1:8080/foo/bar",
            {
                "scheme": "http",
                "authority": "127.0.0.1:8080",
                "path": "/foo/bar",
                "normalizedPath": "/foo/bar/",
                "isIp": True,
            },
        ),
        (
            "https://[fe80::1]:443/",
            {
                "scheme": "https",
                "authority": "[fe80::1]:443",
                "path": "/",
                "normalizedPath": "/",
                "isIp": True,
            },
        ),
        # The authority drops userinfo.
        (
            "https://user:pass@example.com:8443",
            {
                "scheme": "https",
                "authority": "example.com:8443",
                "path": "",
                "normalizedPath": "/",
                "isIp": False,
            },
        ),
        ("https://user@", None),
        ("https://example.com/?foo=bar", None),
        ("https://example.com?", None),
        ("https://a b.com", None),
        ("ftp://example.com", None),
        ("https://example.com:port", None),
    ],
)
def test_parse_url(value: str, expected: dict[str, Any] | None) -> None:
    assert FUNCTIONS["parseURL"](value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("abc-_.~", "abc-_.~"),
        ("a b/c:?", "a%20b%2Fc%3A%3F"),
        ("é", "%C3%A9"),
    ],
)
def test_uri_encode(value: str, expected: str) -> None:
    assert FUNCTIONS["uriEncode"](value) == expected


@pytest.mark.parametrize(
    "args, expected",
    [
        (("a--b--c", "--", 0), ("a", "b", "c")),
        (("a--b--c", "--", 1), ("a--b--c",)),
        (("a--b--c", "--", 2), ("a", "b--c")),
        (("", "--", 0), ("",)),
    ],
)
def test_split(args: tuple[Any, ...], expected: tuple[str, ...]) -> None:
    assert FUNCTIONS["split"](*args) == expected
