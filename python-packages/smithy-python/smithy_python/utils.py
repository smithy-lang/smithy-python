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

import re
from datetime import datetime, timezone
from typing import Any, TypeVar

from .exceptions import ExpectationNotMetException
from .interfaces import http as http_interface

IPV4_PAT: str = r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}"
IPV4_RE: re.Pattern[str] = re.compile("^" + IPV4_PAT + "$")
HEX_PAT: str = "[0-9A-Fa-f]{1,4}"
LS32_PAT: str = "(?:{hex}:{hex}|{ipv4})".format(hex=HEX_PAT, ipv4=IPV4_PAT)
_subs: dict[str, str] = {"hex": HEX_PAT, "ls32": LS32_PAT}
_variations: list[str] = [
    #                            6( h16 ":" ) ls32
    "(?:%(hex)s:){6}%(ls32)s",
    #                       "::" 5( h16 ":" ) ls32
    "::(?:%(hex)s:){5}%(ls32)s",
    # [               h16 ] "::" 4( h16 ":" ) ls32
    "(?:%(hex)s)?::(?:%(hex)s:){4}%(ls32)s",
    # [ *1( h16 ":" ) h16 ] "::" 3( h16 ":" ) ls32
    "(?:(?:%(hex)s:)?%(hex)s)?::(?:%(hex)s:){3}%(ls32)s",
    # [ *2( h16 ":" ) h16 ] "::" 2( h16 ":" ) ls32
    "(?:(?:%(hex)s:){0,2}%(hex)s)?::(?:%(hex)s:){2}%(ls32)s",
    # [ *3( h16 ":" ) h16 ] "::"    h16 ":"   ls32
    "(?:(?:%(hex)s:){0,3}%(hex)s)?::%(hex)s:%(ls32)s",
    # [ *4( h16 ":" ) h16 ] "::"              ls32
    "(?:(?:%(hex)s:){0,4}%(hex)s)?::%(ls32)s",
    # [ *5( h16 ":" ) h16 ] "::"              h16
    "(?:(?:%(hex)s:){0,5}%(hex)s)?::%(hex)s",
    # [ *6( h16 ":" ) h16 ] "::"
    "(?:(?:%(hex)s:){0,6}%(hex)s)?::",
]

UNRESERVED_PAT: str = (
    r"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._!\-~"
)
IPV6_PAT: str = "(?:" + "|".join([x % _subs for x in _variations]) + ")"
ZONE_ID_PAT: str = "(?:%25|%)(?:[" + UNRESERVED_PAT + "]|%[a-fA-F0-9]{2})+"
IPV6_ADDRZ_PAT: str = r"\[" + IPV6_PAT + r"(?:" + ZONE_ID_PAT + r")?\]"
IPV6_ADDRZ_RE: re.Pattern[str] = re.compile("^" + IPV6_ADDRZ_PAT + "$")

# These are the characters that are stripped by post-bpo-43882 urlparse().
UNSAFE_URL_CHARS: frozenset[str] = frozenset("\t\r\n")

DEFAULT_PORTS: dict[str, int] = {"http": 80, "https": 443}


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


def is_valid_ipv6_endpoint_url(endpoint_url: http_interface.URI) -> bool:
    if UNSAFE_URL_CHARS.intersection(endpoint_url.build()):
        return False
    return IPV6_ADDRZ_RE.match(f"[{endpoint_url.host}]") is not None


def host_from_url(url: http_interface.URI) -> str:
    host = url.host
    if is_valid_ipv6_endpoint_url(url):
        host = f"[{host}]"
    if url.port is not None and DEFAULT_PORTS.get(url.scheme) != url.port:
        host += f":{url.port}"
    return host
