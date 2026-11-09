#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import re
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Protocol, cast, runtime_checkable

from smithy_core.exceptions import SmithyError


@runtime_checkable
class Flushable(Protocol):
    """A protocol for objects that can be flushed."""

    def flush(self) -> None: ...


type JSONValue = (
    Mapping[str, "JSONValue"]
    | Sequence["JSONValue"]
    | str
    | int
    | Decimal
    | bool
    | None
)


class JSONValueError(SmithyError):
    """Raised when a parsed JSON value does not match the requested Smithy type."""

    def __init__(self, expected: str, value: JSONValue) -> None:
        super().__init__(
            f"Error parsing JSON. Expected value of type `{expected}`, "
            f"but found: `{type(value).__name__}`: {value}"
        )


# Grammars for string-encoded arbitrary precision numbers. These are matched with
# ``fullmatch``, so whitespace, leading zeros, a leading ``+``, ``1.``, ``.5``,
# ``NaN``, ``Infinity`` and the empty string are all rejected.
_BIG_INTEGER_PATTERN = re.compile(r"-?(0|[1-9][0-9]*)")
_BIG_DECIMAL_PATTERN = re.compile(r"-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?")


def parse_big_integer_string(value: object) -> int:
    """Parse a string-encoded bigInteger.

    :param value: The raw JSON value to parse.
    :returns: The parsed integer.
    :raises JSONValueError: If the value is not a string matching the bigInteger
        grammar.
    """
    if not isinstance(value, str) or _BIG_INTEGER_PATTERN.fullmatch(value) is None:
        raise JSONValueError("bigInteger string", cast(JSONValue, value))
    return int(value)


def parse_big_decimal_string(value: object) -> Decimal:
    """Parse a string-encoded bigDecimal.

    :param value: The raw JSON value to parse.
    :returns: The parsed decimal.
    :raises JSONValueError: If the value is not a string matching the bigDecimal
        grammar.
    """
    if not isinstance(value, str) or _BIG_DECIMAL_PATTERN.fullmatch(value) is None:
        raise JSONValueError("bigDecimal string", cast(JSONValue, value))
    return Decimal(value)
