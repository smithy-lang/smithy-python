# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import datetime
import uuid
from collections.abc import Mapping
from typing import Protocol

type HEADER_VALUE = bool | int | bytes | str | datetime.datetime | uuid.UUID
"""A union of valid value types for event headers."""


type HEADERS_DICT = Mapping[str, HEADER_VALUE]
"""A dictionary of event headers."""


class EventMessage(Protocol):
    """A signable message that may be sent over an event stream."""

    headers: HEADERS_DICT
    """The headers present in the event message."""

    payload: bytes
    """The serialized bytes of the message payload."""

    def encode(self) -> bytes:
        """Encode heads and payload into bytes for transit."""
        ...


class EventHeaderEncoder(Protocol):
    """A utility class that encodes event headers into bytes."""

    def clear(self) -> None:
        """Clear all previously encoded headers."""
        ...

    def get_result(self) -> bytes:
        """Get all the encoded header bytes."""
        ...

    def encode_headers(self, headers: HEADERS_DICT) -> None:
        """Encode a map of headers."""
        ...
