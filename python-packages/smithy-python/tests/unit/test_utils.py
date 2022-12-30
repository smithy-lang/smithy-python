from datetime import datetime, timedelta, timezone
from math import isnan
from typing import Any

import pytest

from smithy_python.exceptions import ExpectationNotMetException
from smithy_python.utils import ensure_utc, expect_type, limited_parse_float


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
