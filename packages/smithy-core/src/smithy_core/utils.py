#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import isinf, isnan
from types import UnionType
from typing import Any, TypeVar, overload

from .exceptions import ExpectationNotMetException

RFC3339 = "%Y-%m-%dT%H:%M:%SZ"
# Same as RFC3339, but with microsecond precision.
RFC3339_MICRO = "%Y-%m-%dT%H:%M:%S.%fZ"


def ensure_utc(value: datetime) -> datetime:
    """Ensures that the given datetime is a UTC timezone-aware datetime.

    If the datetime isn't timezone-aware, its timezone is set to UTC. If it is aware,
    it's replaced with the equivalent datetime under UTC.

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


def epoch_seconds_to_datetime(value: int | float) -> datetime:
    """Parse numerical epoch timestamps (seconds since 1970) into a datetime in UTC.

    Falls back to using ``timedelta`` when ``fromtimestamp`` raises ``OverflowError``.
    From Python's ``fromtimestamp`` documentation: "This may raise OverflowError, if the
    timestamp is out of the range of values supported by the platform C localtime()
    function, and OSError on localtime() failure. It's common for this to be restricted
    to years from 1970 through 2038." This affects 32-bit systems.
    """
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc)
    except OverflowError:
        epoch_zero = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        return epoch_zero + timedelta(seconds=value)


_T = TypeVar("_T")


@overload
def expect_type(typ: type[_T], value: Any) -> _T: ...


# For some reason, mypy and other type checkers don't treat Union like a full type
# despite it being checkable with isinstance and other methods. This essentially means
# we can't pass back the given type when we're given a union. So instead we have to
# return Any.
@overload
def expect_type(typ: UnionType, value: Any) -> Any: ...


def expect_type(typ: UnionType | type, value: Any) -> Any:
    """Asserts a value is of the given type and returns it unchanged.

    This performs both a runtime assertion and type narrowing during type checking
    similar to ``typing.cast``. If the runtime assertion is not needed, ``typing.cast``
    should be preferred.

    :param typ: The expected type.
    :param value: The value which is expected to be the given type.
    :returns: The given value cast as the given type.
    :raises SmithyException: If the value does not match the type.
    """
    if not isinstance(value, typ):
        raise ExpectationNotMetException(
            f"Expected {typ}, found {type(value)}: {value}"
        )
    return value


def split_every(given: str, split_char: str, n: int) -> list[str]:
    """Splits a string every nth instance of the given character.

    :param given: The string to split.
    :param split_char: The character to split on.
    :param n: The number of instances of split_char to see before each split.
    :returns: A list of strings.
    """
    split = given.split(split_char)
    return [split_char.join(split[i : i + n]) for i in range(0, len(split), n)]


def strict_parse_bool(given: str) -> bool:
    """Strictly parses a boolean from string.

    :param given: A string that is expected to contain either "true" or "false".
    :returns: The given string parsed to a boolean.
    :raises ExpectationNotMetException: if the given string is neither "true" nor
        "false".
    """
    match given:
        case "true":
            return True
        case "false":
            return False
        case _:
            raise ExpectationNotMetException(
                f"Expected 'true' or 'false', found: {given}"
            )


# A regex for Smithy floats. It matches JSON-style numbers.
_FLOAT_REGEX = re.compile(
    r"""
    ( # Opens the numeric float group.
        -? # The integral may start with a negative sign, but not a positive one.
        (?:0|[1-9]\d*) # The integral may not have leading 0s unless it is exactly 0.
        (?:\.\d+)? # There may be a fraction starting with a period and containing at
                   # least one number.
        (?: # Opens the exponent group.
            [eE] # The exponent starts with a case-insensitive e
            [+-]? # The exponent may have a positive or negative sign.
            \d+ # The exponent must have one or more digits.
        )? # Closes the exponent group and makes it optional.
    ) # Closes the numeric float group.
    |(-?Infinity) # If the float isn't numeric, it may be Infinity or -Infinity
    |(NaN) # If the float isn't numeric, it may also be NaN
    """,
    re.VERBOSE,
)


def strict_parse_float(given: str) -> float:
    """Strictly parses a float from a string.

    Unlike float(), this forbids the use of "inf" and case-sensitively matches Infinity
    and NaN.

    :param given: A string that is expected to contain a float.
    :returns: The given string parsed to a float.
    :raises ExpectationNotMetException: If the given string isn't a float.
    """
    if _FLOAT_REGEX.fullmatch(given):
        return float(given)
    raise ExpectationNotMetException(f"Expected float, found: {given}")


def serialize_float(given: float | Decimal) -> str:
    """Serializes a float to a string.

    This ensures non-numeric floats are serialized correctly, and ensures that there is
    a fractional part.

    :param given: A float or Decimal to be serialized.
    :returns: The string representation of the given float.
    """
    if isnan(given):
        return "NaN"
    if isinf(given):
        return "-Infinity" if given < 0 else "Infinity"

    if isinstance(given, Decimal):
        given = given.normalize()

    result = str(given)
    if result.isnumeric():
        result += ".0"
    return result


def limited_serialize_float(given: float) -> str | float:
    """Serializes non-numeric floats to strings.

    Numeric floats are returned without alteration.

    :param given: A float to be conditionally serialized.
    :returns: The given float as a float or string.
    """
    if isnan(given):
        return "NaN"
    if isinf(given):
        return "-Infinity" if given < 0 else "Infinity"

    return given


def serialize_rfc3339(given: datetime) -> str:
    """Serializes a datetime into an RFC3339 string representation.

    If ``microseconds`` is 0, no fractional part is serialized.

    :param given: The datetime to serialize.
    :returns: An RFC3339 formatted timestamp.
    """
    if given.microsecond != 0:
        return given.strftime(RFC3339_MICRO)
    else:
        return given.strftime(RFC3339)


def serialize_epoch_seconds(given: datetime) -> float:
    """Serializes a datetime into a string containing the epoch seconds.

    If ``microseconds`` is 0, no fractional part is serialized.

    :param given: The datetime to serialize.
    :returns: A string containing the seconds since the UNIX epoch.
    """
    result = given.timestamp()
    if given.microsecond == 0:
        result = int(result)
    return result


def remove_dot_segments(path: str, remove_consecutive_slashes: bool = False) -> str:
    """Removes dot segments from a path per :rfc:`3986#section-5.2.4`.

    Optionally removes consecutive slashes.

    :param path: The path to modify.
    :param remove_consecutive_slashes: Whether to remove consecutive slashes.
    :returns: The path with dot segments removed.
    """
    output: list[str] = []
    for segment in path.split("/"):
        if segment == ".":
            continue
        elif segment != "..":
            output.append(segment)
        elif output:
            output.pop()
    if path.startswith("/") and (not output or output[0]):
        output.insert(0, "")
    if output and path.endswith(("/.", "/..")):
        output.append("")
    result = "/".join(output)
    if remove_consecutive_slashes:
        result = result.replace("//", "/")
    return result
