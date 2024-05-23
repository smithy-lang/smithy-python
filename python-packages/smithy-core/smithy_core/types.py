#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from email.utils import format_datetime, parsedate_to_datetime
from enum import Enum
from typing import Any, TypeAlias

from .exceptions import ExpectationNotMetException
from .utils import (
    ensure_utc,
    epoch_seconds_to_datetime,
    expect_type,
    serialize_epoch_seconds,
    serialize_rfc3339,
)

Document: TypeAlias = (
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
