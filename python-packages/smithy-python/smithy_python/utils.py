import re
from datetime import datetime, timezone
from typing import Any, TypeVar

from .exceptions import ExpectationNotMetException


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
            [+-]? # The exponent may have a positive or negave sign.
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

    Unlike float(), this forbids the use of "inf" and case-sensitively matches
    Infinity and NaN.

    :param given: A string that is expected to contain a float.
    :returns: The given string parsed to a float.
    :raises ExpectationNotMetException: If the given string isn't a float.
    """
    if _FLOAT_REGEX.fullmatch(given):
        return float(given)
    raise ExpectationNotMetException(f"Expected float, found: {given}")
