# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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


from datetime import datetime, timedelta, timezone
from math import isnan
from typing import Any

import pytest

from smithy_python._private.http import URI
from smithy_python.exceptions import ExpectationNotMetException
from smithy_python.utils import (
    ensure_utc,
    expect_type,
    host_from_url,
    is_valid_ipv6_endpoint_url,
    limited_parse_float,
    split_every,
    strict_parse_bool,
    strict_parse_float,
)


@pytest.mark.parametrize(
    "given, expected",
    [
        (datetime(2017, 1, 1), datetime(2017, 1, 1, tzinfo=timezone.utc)),
        (
            datetime(2017, 1, 1, tzinfo=timezone.utc),
            datetime(2017, 1, 1, tzinfo=timezone.utc),
        ),
        (
            datetime(2017, 1, 1, tzinfo=timezone(timedelta(hours=1))),
            datetime(2016, 12, 31, 23, tzinfo=timezone.utc),
        ),
    ],
)
def test_ensure_utc(given: datetime, expected: datetime) -> None:
    assert ensure_utc(given) == expected


@pytest.mark.parametrize(
    "typ, value",
    [
        (str, ""),
        (int, 1),
        (bool, True),
    ],
)
def test_expect_type(typ: Any, value: Any) -> None:
    assert expect_type(typ, value) == value


@pytest.mark.parametrize(
    "typ, value",
    [
        (str, b""),
        (int, ""),
        (int, 1.0),
        (bool, 0),
        (bool, ""),
    ],
)
def test_expect_type_raises(typ: Any, value: Any) -> None:
    with pytest.raises(ExpectationNotMetException):
        expect_type(typ, value)


@pytest.mark.parametrize(
    "given, expected",
    [
        (1.0, 1.0),
        ("Infinity", float("Infinity")),
        ("-Infinity", float("-Infinity")),
    ],
)
def test_limited_parse_float(given: float | str, expected: float) -> None:
    assert limited_parse_float(given) == expected


@pytest.mark.parametrize(
    "given",
    [
        (1),
        ("1.0"),
        ("nan"),
        ("infinity"),
        ("inf"),
        ("-infinity"),
        ("-inf"),
    ],
)
def test_limited_parse_float_raises(given: float | str) -> None:
    with pytest.raises(ExpectationNotMetException):
        limited_parse_float(given)


def test_limited_parse_float_nan() -> None:
    assert isnan(limited_parse_float("NaN"))


@pytest.mark.parametrize(
    "given, split_char, n, expected",
    [
        ("a,b,c,d", ",", 1, ["a", "b", "c", "d"]),
        ("a,b,c,d", ",", 2, ["a,b", "c,d"]),
        ("a,b,c,d", ",", 3, ["a,b,c", "d"]),
        ("a,b,c,d", ",", 4, ["a,b,c,d"]),
        ("a,b,c,d", "b", 1, ["a,", ",c,d"]),
    ],
)
def test_split_every(given: str, split_char: str, n: int, expected: list[str]) -> None:
    assert split_every(given, split_char, n) == expected


def test_strict_parse_bool() -> None:
    assert strict_parse_bool("true") is True
    assert strict_parse_bool("false") is False
    with pytest.raises(ExpectationNotMetException):
        strict_parse_bool("")


@pytest.mark.parametrize(
    "given, expected",
    [
        ("1.0", 1.0),
        ("-1.0", -1.0),
        ("1e1", 10.0),
        ("1E1", 10.0),
        ("1e-1", 0.1),
        ("-1e-1", -0.1),
        ("0.1", 0.1),
        ("Infinity", float("Infinity")),
        ("-Infinity", float("-Infinity")),
    ],
)
def test_strict_parse_float(given: str, expected: float) -> None:
    assert strict_parse_float(given) == expected


def test_strict_parse_float_nan() -> None:
    assert isnan(strict_parse_float("NaN"))


@pytest.mark.parametrize(
    "given",
    [
        ("01"),
        ("-01"),
        ("nan"),
        ("infinity"),
        ("inf"),
        ("-infinity"),
        ("-inf"),
    ],
)
def test_strict_parse_float_raises(given: str) -> None:
    with pytest.raises(ExpectationNotMetException):
        strict_parse_float(given)


@pytest.mark.parametrize(
    "url, expected_host",
    [
        (URI("example.com"), "example.com"),
        (URI(host="example.com", scheme="http"), "example.com"),
        (
            URI("2001:db8:3333:4444:5555:6666:7777:8888"),
            "[2001:db8:3333:4444:5555:6666:7777:8888]",
        ),
        (
            URI(host="2001:db8:3333:4444:5555:6666:7777:8888", port=8080),
            "[2001:db8:3333:4444:5555:6666:7777:8888]:8080",
        ),
        (
            URI(host="2001:db8:3333:4444:5555:6666:7777:8888", scheme="http", port=80),
            "[2001:db8:3333:4444:5555:6666:7777:8888]",
        ),
        (
            URI(host="2001:db8:3333:4444:5555:6666:7777:8888", port=443),
            "[2001:db8:3333:4444:5555:6666:7777:8888]",
        ),
        (URI(host="example.com", port=1234), "example.com:1234"),
        (URI(host="example.com", scheme="http", port=80), "example.com"),
        (URI(host="example.com", port=443), "example.com"),
    ],
)
def test_host_from_url(url: URI, expected_host: str) -> None:
    assert host_from_url(url) == expected_host


@pytest.mark.parametrize(
    "url, expected_value",
    [
        (URI("example.com"), False),
        (URI(host="2001:db8:3333:4444:5555:6666:7777:8888", path="/\t\r/"), False),
        (URI("2001:db8:3333:4444:5555:6666:7777:8888"), True),
    ],
)
def test_is_valid_is_valid_ipv6_endpoint_url(url: URI, expected_value: bool) -> None:
    assert is_valid_ipv6_endpoint_url(url) == expected_value
