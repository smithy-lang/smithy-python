from datetime import datetime, timezone
from typing import Any, TypeVar

from .exceptions import SmithyException


def ensure_utc(value: datetime) -> datetime:
    """Ensures that the given datetime is a UTC timezone-aware datetime.

    If the datetime isn't timzezone-aware, its timezone is set to UTC. If it is
    aware, it's replaced with the equivalent datetime under UTC.

    :param value: A datetime object that may or may not be timezone-aware.
    :returns: A UTC timezone-aware equivalent datetime.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    else:
        return value.astimezone(timezone.utc)


# Python is way more permissive on value of non-numerical floats than Smithy is, so we
# need to compare potential string values against this set of values that Smithy
# generally permits.
_NON_NUMERICAL_FLOATS = {"NaN", "Infinity", "-Infinity"}


def limited_parse_float(value: Any) -> float:
    """Asserts a value is a float or a limited set of non-numerical strings and returns
    it as a float.

    :param value: An object that is expected to be a float.
    :returns: The given value as a float.
    :raises SmithyException: If the value is not a float or one of the strings ``NaN``,
        ``Infinity``, or ``-Infinity``.
    """
    # TODO: add limited bounds checking
    if isinstance(value, str) and value in _NON_NUMERICAL_FLOATS:
        return float(value)

    return expect_type(float, value)


_T = TypeVar("_T")


def expect_type(typ: type[_T], value: Any) -> _T:
    """Asserts a value is of the given type and returns it as that type.

    This is essentially typing.cast, but with a runtime assertion. If the runtime
    assertion isn't needed, typing.cast should be preferred.

    :param typ: The expected type.
    :param value: The value which is expected to be the given type.
    :returns: The given value cast as the given type.
    :raises SmithyException: If the value does not match the type.
    """
    if not isinstance(value, typ):
        raise SmithyException(f"Expected {typ}, found {type(value)}: {value}")
    return value
