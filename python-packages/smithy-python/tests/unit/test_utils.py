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

# mypy: allow-untyped-defs
# mypy: allow-incomplete-defs

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import isnan
from typing import Any, NamedTuple
from unittest.mock import Mock

import pytest

from smithy_python.exceptions import ExpectationNotMetException
from smithy_python.utils import (
    ensure_utc,
    epoch_seconds_to_datetime,
    expect_type,
    limited_parse_float,
    limited_serialize_float,
    remove_dot_segments,
    serialize_epoch_seconds,
    serialize_float,
    serialize_rfc3339,
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
        (float | int, 1),
        (float | int, 1.1),
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
        (float | int, "1"),
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
    "given, expected",
    [
        (1, "1.0"),
        (1.0, "1.0"),
        (1.1, "1.1"),
        # It's not particularly important whether the result of this is "1.1e3" or
        # "1100.0" since both are valid representations. This is how float behaves
        # by default in python though, and there's no reason to do extra work to
        # change it.
        (1.1e3, "1100.0"),
        (1e1, "10.0"),
        (32.100, "32.1"),
        (0.321000e2, "32.1"),
        # It's at about this point that floats start using scientific notation.
        (1e16, "1e+16"),
        (float("NaN"), "NaN"),
        (float("Infinity"), "Infinity"),
        (float("-Infinity"), "-Infinity"),
        (Decimal("1"), "1.0"),
        (Decimal("1.0"), "1.0"),
        (Decimal("1.1"), "1.1"),
        (Decimal("1.1e3"), "1.1E+3"),
        (Decimal("1e1"), "1E+1"),
        (Decimal("32.100"), "32.1"),
        (Decimal("0.321000e+2"), "32.1"),
        (Decimal("1e16"), "1E+16"),
        (Decimal("NaN"), "NaN"),
        (Decimal("Infinity"), "Infinity"),
        (Decimal("-Infinity"), "-Infinity"),
    ],
)
def test_serialize_float(given: float | Decimal, expected: str) -> None:
    assert serialize_float(given) == expected


class DateTimeTestcase(NamedTuple):
    dt_object: datetime
    rfc3339_str: str
    epoch_seconds_num: int | float
    epoch_seconds_str: str


DATETIME_TEST_CASES: list[DateTimeTestcase] = [
    DateTimeTestcase(
        dt_object=datetime(2017, 1, 1, tzinfo=timezone.utc),
        rfc3339_str="2017-01-01T00:00:00Z",
        epoch_seconds_num=1483228800,
        epoch_seconds_str="1483228800",
    ),
    DateTimeTestcase(
        dt_object=datetime(2017, 1, 1, microsecond=1, tzinfo=timezone.utc),
        rfc3339_str="2017-01-01T00:00:00.000001Z",
        epoch_seconds_num=1483228800.000001,
        epoch_seconds_str="1483228800.000001",
    ),
    DateTimeTestcase(
        dt_object=datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        rfc3339_str="1969-12-31T23:59:59Z",
        epoch_seconds_num=-1,
        epoch_seconds_str="-1",
    ),
    # The first second affected by the Year 2038 problem where fromtimestamp raises an
    # OverflowError on 32-bit systems for dates beyond 2038-01-19 03:14:07 UTC.
    DateTimeTestcase(
        dt_object=datetime(2038, 1, 19, 3, 14, 8, tzinfo=timezone.utc),
        rfc3339_str="2038-01-19T03:14:08Z",
        epoch_seconds_num=2147483648,
        epoch_seconds_str="2147483648",
    ),
]


@pytest.mark.parametrize(
    "given, expected",
    [
        (1.0, 1.0),
        (float("NaN"), "NaN"),
        (float("Infinity"), "Infinity"),
        (float("-Infinity"), "-Infinity"),
    ],
)
def test_limited_serialize_float(given: float, expected: str | float) -> None:
    assert limited_serialize_float(given) == expected


@pytest.mark.parametrize(
    "given, expected",
    [(case.dt_object, case.rfc3339_str) for case in DATETIME_TEST_CASES],
)
def test_serialize_rfc3339(given: datetime, expected: str) -> None:
    assert serialize_rfc3339(given) == expected


@pytest.mark.parametrize(
    "given, expected",
    [(case.dt_object, case.epoch_seconds_num) for case in DATETIME_TEST_CASES],
)
def test_serialize_epoch_seconds(given: datetime, expected: int) -> None:
    assert serialize_epoch_seconds(given) == expected


@pytest.mark.parametrize(
    "given, expected",
    [(case.epoch_seconds_num, case.dt_object) for case in DATETIME_TEST_CASES],
)
def test_epoch_seconds_to_datetime(given: int | float, expected: datetime) -> None:
    assert epoch_seconds_to_datetime(given) == expected


def test_epoch_seconds_to_datetime_with_overflow_error(monkeypatch):
    # Emulate the Year 2038 problem by always raising an OverflowError.
    datetime_mock = Mock(wraps=datetime)
    datetime_mock.fromtimestamp = Mock(side_effect=OverflowError())
    monkeypatch.setattr("smithy_python.utils.datetime", datetime_mock)
    dt_object = datetime(2038, 1, 19, 3, 14, 8, tzinfo=timezone.utc)
    epoch_seconds_to_datetime(2147483648) == dt_object


@pytest.mark.parametrize(
    "input_path, remove_consecutive_slashes, expected_path",
    [
        ("/foo/bar", False, "/foo/bar"),
        ("/foo/bar/", False, "/foo/bar/"),
        ("/foo/bar/.", False, "/foo/bar/"),
        ("/foo/bar/..", False, "/foo/"),
        ("/foo/bar/../", False, "/foo/"),
        ("/foo/bar/../baz", False, "/foo/baz"),
        ("/foo/bar/../baz/", False, "/foo/baz/"),
        ("/foo/bar/./baz", False, "/foo/bar/baz"),
        ("/foo/bar/./baz/", False, "/foo/bar/baz/"),
        ("/foo/bar/././baz", False, "/foo/bar/baz"),
        ("/foo/bar/././baz/", False, "/foo/bar/baz/"),
        ("/foo/bar/./../baz", False, "/foo/baz"),
        ("/foo/bar/./../baz/", False, "/foo/baz/"),
        ("/foo/bar/.././baz", False, "/foo/baz"),
        ("/foo/bar/.././baz/", False, "/foo/baz/"),
        ("/foo/bar/../../baz", False, "/baz"),
        ("", False, ""),
        ("/", False, "/"),
        ("/.", False, "/"),
        ("/..", False, "/"),
        ("/./", False, "/"),
        ("/../", False, ""),
        ("/./.", False, "/"),
        ("./", False, ""),
        ("../", False, ""),
        ("..", False, ""),
        (".", False, ""),
        ("/foo/bar", True, "/foo/bar"),
        ("/foo/bar/", True, "/foo/bar/"),
        ("/foo//bar/.", True, "/foo/bar/"),
        ("/foo/bar//..", True, "/foo/bar/"),
        ("//foo//bar//..//", True, "/foo/bar/"),
    ],
)
def test_remove_dot_segments(
    input_path: str, remove_consecutive_slashes: bool, expected_path: str
) -> None:
    assert remove_dot_segments(input_path, remove_consecutive_slashes) == expected_path
