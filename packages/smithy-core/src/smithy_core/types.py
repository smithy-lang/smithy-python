#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
import re
import sys
from collections import UserDict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from email.utils import format_datetime, parsedate_to_datetime
from enum import Enum
from typing import Any, overload

from .exceptions import ExpectationNotMetException
from .interfaces import PropertyKey as _PropertyKey
from .interfaces import TypedProperties as _TypedProperties
from .utils import (
    ensure_utc,
    epoch_seconds_to_datetime,
    expect_type,
    serialize_epoch_seconds,
    serialize_rfc3339,
)

_GREEDY_LABEL_RE = re.compile(r"\{(\w+)\+\}")

type Document = (
    Mapping[str, "Document"] | Sequence["Document"] | str | int | float | bool | None
)


class JsonString(str):
    """A string that contains json data which can be lazily loaded."""

    _json = None

    def as_json(self) -> Any:
        if not self._json:
            self._json = json.loads(self)
        return self._json

    @staticmethod
    def from_json(j: Any) -> "JsonString":
        json_string = JsonString(json.dumps(j))
        json_string._json = j
        return json_string


class JsonBlob(bytes):
    """Bytes that contain json data which can be lazily loaded."""

    _json = None

    def as_json(self) -> Any:
        if not self._json:
            self._json = json.loads(self.decode(encoding="utf-8"))
        return self._json

    @staticmethod
    def from_json(j: Any) -> "JsonBlob":
        json_string = JsonBlob(json.dumps(j).encode(encoding="utf-8"))
        json_string._json = j
        return json_string


class TimestampFormat(Enum):
    """Smithy-defined timestamp formats with serialization and deserialization helpers.

    See `Smithy's docs <https://smithy.io/2.0/spec/protocol-traits.html#smithy-api-timestampformat-trait>`_
    for more details.
    """

    DATE_TIME = "date-time"
    """RFC3339 section 5.6 datetime with optional millisecond precision but no UTC
    offset."""

    HTTP_DATE = "http-date"
    """An HTTP date as defined by the IMF-fixdate production in RFC 9110 section
    5.6.7."""

    EPOCH_SECONDS = "epoch-seconds"
    """Also known as Unix time, the number of seconds that have elapsed since 00:00:00
    Coordinated Universal Time (UTC), Thursday, 1 January 1970, with optional
    millisecond precision."""

    def serialize(self, value: datetime) -> str | float:
        """Serializes a datetime into the timestamp format.

        :param value: The timestamp to serialize.
        :returns: A formatted timestamp. This will be a float for EPOCH_SECONDS, or a
            string otherwise.
        """
        value = ensure_utc(value)
        match self:
            case TimestampFormat.EPOCH_SECONDS:
                return serialize_epoch_seconds(value)
            case TimestampFormat.HTTP_DATE:
                return format_datetime(value, usegmt=True)
            case TimestampFormat.DATE_TIME:
                return serialize_rfc3339(value)

    def deserialize(self, value: str | float) -> datetime:
        """Deserializes a datetime from a value of the format.

        :param value: The timestamp value to deserialize. If the format is
            EPOCH_SECONDS, the value must be an int or float, or a string containing an
            int or float. Otherwise, it must be a string.
        :returns: The provided value as a datetime instance.
        """
        match self:
            case TimestampFormat.EPOCH_SECONDS:
                if isinstance(value, str):
                    try:
                        value = float(value)
                    except ValueError as e:
                        raise ExpectationNotMetException from e
                return epoch_seconds_to_datetime(value=value)
            case TimestampFormat.HTTP_DATE:
                return ensure_utc(parsedate_to_datetime(expect_type(str, value)))
            case TimestampFormat.DATE_TIME:
                return ensure_utc(datetime.fromisoformat(expect_type(str, value)))


@dataclass(init=False, frozen=True)
class PathPattern:
    """A formattable URI path pattern.

    The pattern may contain formattable labels, which may be normal labels or greedy
    labels. Normal labels forbid path separators, greedy labels allow them.
    """

    pattern: str
    """The path component of the URI which is a formattable string."""

    greedy_labels: set[str]
    """The pattern labels whose values may contain path separators."""

    def __init__(self, pattern: str) -> None:
        object.__setattr__(self, "pattern", pattern)
        object.__setattr__(
            self, "greedy_labels", set(_GREEDY_LABEL_RE.findall(pattern))
        )

    def format(self, *args: object, **kwargs: str) -> str:
        if args:
            raise ValueError("PathPattern formatting requires only keyword arguments.")

        for key, value in kwargs.items():
            if "/" in value and key not in self.greedy_labels:
                raise ValueError(
                    'Non-greedy labels must not contain path separators ("/").'
                )

        result = self.pattern.replace("+}", "}").format(**kwargs)
        if "//" in result:
            raise ValueError(
                f'Path must not contain empty segments, but was "{result}".'
            )
        return result


@dataclass(kw_only=True, frozen=True, slots=True, init=False)
class PropertyKey[T](_PropertyKey[T]):
    """A typed property key.

    Note that unions and other special types cannot easily be used here due to being
    incompatible with ``type[T]``. PEP747 proposes a fix to this case, but it has not
    yet been accepted. In the meantime, there is a workaround. The PropertyKey must
    be assigned to an explicitly typed variable, and the ``value_type`` parameter of
    the constructor must have a ``# type: ignore`` comment, like so:

    .. code-block:: python

        UNION_PROPERTY: PropertyKey[str | int] = PropertyKey(
            key="union",
            value_type=str | int,  # type: ignore
        )

    Type checkers will be able to use such a property as expected.
    """

    key: str
    """The string key used to access the value."""

    value_type: type[T]
    """The type of the associated value in the property bag."""

    def __init__(self, *, key: str, value_type: type[T]) -> None:
        # Intern the key to speed up dict access
        object.__setattr__(self, "key", sys.intern(key))
        object.__setattr__(self, "value_type", value_type)


class TypedProperties(UserDict[str, Any], _TypedProperties):
    """A map with typed setters and getters.

    Keys can be either a string or a :py:class:`smithy_core.interfaces.PropertyKey`.
    Using a PropertyKey instead of a string enables type checkers to narrow to the
    associated value type rather than having to use Any.

    Letting the value be either a string or PropertyKey allows consumers who care about
    typing to get it, and those who don't care about typing to not have to think about
    it.

    No runtime type assertion is performed.

    ..code-block:: python

        foo = PropertyKey(key="foo", value_type=str)
        properties = TypedProperties()
        properties[foo] = "bar"

        assert assert_type(properties[foo], str) == "bar"
        assert assert_type(properties["foo"], Any) == "bar"

    Note that unions and other special types cannot easily be used here due to being
    incompatible with ``type[T]``. PEP747 proposes a fix to this case, but it has not
    yet been accepted. In the meantime, there is a workaround. The PropertyKey must
    be assigned to an explicitly typed variable, and the ``value_type`` parameter of
    the constructor must have a ``# type: ignore`` comment, like so:

    .. code-block:: python

        UNION_PROPERTY: PropertyKey[str | int] = PropertyKey(
            key="union",
            value_type=str | int,  # type: ignore
        )

        properties = TypedProperties()
        properties[UNION_PROPERTY] = "foo"

        assert assert_type(properties[UNION_PROPERTY], str | int) == "foo"

    Type checkers will be able to use such a property as expected.
    """

    @overload
    def __getitem__[T](self, key: _PropertyKey[T]) -> T: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def __getitem__(self, key: str | _PropertyKey[Any]) -> Any:
        return self.data[key if isinstance(key, str) else key.key]

    @overload
    def __setitem__[T](self, key: _PropertyKey[T], value: T) -> None: ...
    @overload
    def __setitem__(self, key: str, value: Any) -> None: ...
    def __setitem__(self, key: str | _PropertyKey[Any], value: Any) -> None:
        self.data[key if isinstance(key, str) else key.key] = value

    def __delitem__(self, key: str | _PropertyKey[Any]) -> None:
        del self.data[key if isinstance(key, str) else key.key]

    def __contains__(self, key: object) -> bool:
        return super().__contains__(key.key if isinstance(key, _PropertyKey) else key)

    @overload
    def get[T](self, key: _PropertyKey[T], default: None = None) -> T | None: ...
    @overload
    def get[T](self, key: _PropertyKey[T], default: T) -> T: ...
    @overload
    def get[T, DT](self, key: _PropertyKey[T], default: DT) -> T | DT: ...
    @overload
    def get(self, key: str, default: None = None) -> Any | None: ...
    @overload
    def get[T](self, key: str, default: T) -> Any | T: ...

    # pyright has trouble detecting compatible overrides when both the superclass
    # and subclass have overloads.
    def get(self, key: str | _PropertyKey[Any], default: Any = None) -> Any:  # type: ignore
        return self.data.get(key if isinstance(key, str) else key.key, default)

    @overload
    def pop[T](self, key: _PropertyKey[T], default: None = None) -> T | None: ...
    @overload
    def pop[T](self, key: _PropertyKey[T], default: T) -> T: ...
    @overload
    def pop[T, DT](self, key: _PropertyKey[T], default: DT) -> T | DT: ...
    @overload
    def pop(self, key: str, default: None = None) -> Any | None: ...
    @overload
    def pop[T](self, key: str, default: T) -> Any | T: ...

    # pyright has trouble detecting compatible overrides when both the superclass
    # and subclass have overloads.
    def pop(self, key: str | _PropertyKey[Any], default: Any = None) -> Any:  # type: ignore
        return self.data.pop(key if isinstance(key, str) else key.key, default)
