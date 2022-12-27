from datetime import datetime, timedelta, timezone
from math import isnan
from typing import Any

import pytest

from smithy_python.exceptions import SmithyException
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
    "typ, value, should_raise",
    [
        (str, b"", True),
        (str, "", False),
        (int, "", True),
        (int, 1, False),
        (int, 1.0, True),
        (bool, True, False),
        (bool, 0, True),
        (bool, "", True),
    ],
)
def test_expect_type(typ: Any, value: Any, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(SmithyException):
            expect_type(typ, value)
    else:
        assert expect_type(typ, value) == value


@pytest.mark.parametrize(
    "given, expected",
    [
        (1, None),
        (1.0, 1.0),
        ("1.0", None),
        ("nan", None),
        ("Infinity", float("Infinity")),
        ("infinity", None),
        ("inf", None),
        ("-Infinity", float("-Infinity")),
        ("-infinity", None),
        ("-inf", None),
    ],
)
def test_limited_parse_float(given: float | str, expected: float | None) -> None:
    if expected is None:
        with pytest.raises(SmithyException):
            limited_parse_float(given)
    else:
        assert limited_parse_float(given) == expected


def test_limited_parse_float_nan() -> None:
    assert isnan(limited_parse_float("NaN"))
