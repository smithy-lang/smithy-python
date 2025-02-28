# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections import OrderedDict
from collections.abc import AsyncIterable, Iterable, Iterator
from enum import Enum
from typing import Protocol, runtime_checkable


class FieldPosition(Enum):
    """The type of a field.

    Defines its placement in a request or response.
    """

    HEADER = 0
    """Header field.

    In HTTP this is a header as defined in RFC 9110 Section 6.3. Implementations of
    other protocols may use this FieldPosition for similar types of metadata.
    """

    TRAILER = 1
    """Trailer field.

    In HTTP this is a trailer as defined in RFC 9110 Section 6.5. Implementations of
    other protocols may use this FieldPosition for similar types of metadata.
    """


class Field(Protocol):
    """A name-value pair representing a single field in a request or response.

    The kind will dictate metadata placement within a message, for example as a header
    or trailer field in an HTTP request as defined in RFC 9110 Section 5.

    All field names are case insensitive and case-variance must be treated as
    equivalent. Names may be normalized but should be preserved for accuracy during
    transmission.
    """

    name: str
    values: list[str]
    kind: FieldPosition = FieldPosition.HEADER

    def add(self, value: str) -> None:
        """Append a value to a field."""
        ...

    def set(self, values: list[str]) -> None:
        """Overwrite existing field values."""
        ...

    def remove(self, value: str) -> None:
        """Remove all matching entries from list."""
        ...

    def as_string(self, delimiter: str = ", ") -> str:
        """Serialize the ``Field``'s values into a single line string."""
        ...

    def as_tuples(self) -> list[tuple[str, str]]:
        """Get list of ``name``, ``value`` tuples where each tuple represents one
        value."""
        ...


class Fields(Protocol):
    """Protocol agnostic mapping of key-value pair request metadata, such as HTTP
    fields."""

    # Entries are keyed off the name of a provided Field
    entries: OrderedDict[str, Field]
    encoding: str = "utf-8"

    def set_field(self, field: Field) -> None:
        """Alias for __setitem__ to utilize the field.name for the entry key."""
        ...

    def __setitem__(self, name: str, field: Field) -> None:
        """Set entry for a Field name."""
        ...

    def __getitem__(self, name: str) -> Field:
        """Retrieve Field entry."""
        ...

    def __delitem__(self, name: str) -> None:
        """Delete entry from collection."""
        ...

    def __iter__(self) -> Iterator[Field]:
        """Allow iteration over entries."""
        ...

    def __len__(self) -> int:
        """Get total number of Field entries."""
        ...

    def get_by_type(self, kind: FieldPosition) -> list[Field]:
        """Helper function for retrieving specific types of fields.

        Used to grab all headers or all trailers.
        """
        ...

    def extend(self, other: Fields) -> None:
        """Merges ``entries`` of ``other`` into the current ``entries``.

        For every `Field` in the ``entries`` of ``other``: If the normalized name
        already exists in the current ``entries``, the values from ``other`` are
        appended. Otherwise, the ``Field`` is added to the list of ``entries``.
        """
        ...


class Request(Protocol):
    """Protocol-agnostic representation of a request."""

    destination: URI
    body: AsyncIterable[bytes] | Iterable[bytes] | None


@runtime_checkable
class URI(Protocol):
    """Universal Resource Identifier, target location for a :py:class:`Request`."""

    scheme: str
    """For example ``http`` or ``mqtts``."""

    username: str | None
    """Username part of the userinfo URI component."""

    password: str | None
    """Password part of the userinfo URI component."""

    host: str
    """The hostname, for example ``amazonaws.com``."""

    port: int | None
    """An explicit port number."""

    path: str | None
    """Path component of the URI."""

    query: str | None
    """Query component of the URI as string."""

    fragment: str | None
    """Part of the URI specification, but may not be transmitted by a client."""

    def build(self) -> str:
        """Construct URI string representation.

        Returns a string of the form
        ``{scheme}://{username}:{password}@{host}:{port}{path}?{query}#{fragment}``
        """
        ...

    @property
    def netloc(self) -> str:
        """Construct netloc string in format ``{username}:{password}@{host}:{port}``"""
        ...
