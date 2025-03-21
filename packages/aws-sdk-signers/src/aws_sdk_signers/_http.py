# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
NOTE TO THE READER:

This file is _strictly_ temporary and subject to abrupt breaking changes
including unannounced removal. For typing information, please rely on the
__all__ attributes provided in the types/__init__.py file.
"""

from __future__ import annotations

from collections import Counter, OrderedDict
from collections.abc import AsyncIterable, Iterable, Iterator
from copy import deepcopy
from dataclasses import dataclass
from functools import cached_property
from typing import TypedDict
from urllib.parse import urlunparse

import aws_sdk_signers.interfaces.http as interfaces_http


class Field(interfaces_http.Field):
    """A name-value pair representing a single field in an HTTP Request or Response.

    The kind will dictate metadata placement within an HTTP message.

    All field names are case insensitive and case-variance must be treated as
    equivalent. Names may be normalized but should be preserved for accuracy during
    transmission.
    """

    def __init__(
        self,
        *,
        name: str,
        values: Iterable[str] | None = None,
        kind: interfaces_http.FieldPosition = interfaces_http.FieldPosition.HEADER,
    ):
        self.name = name
        self.values: list[str] = list(values) if values is not None else []
        self.kind = kind

    def add(self, value: str) -> None:
        """Append a value to a field."""
        self.values.append(value)

    def set(self, values: list[str]) -> None:
        """Overwrite existing field values."""
        self.values = values

    def remove(self, value: str) -> None:
        """Remove all matching entries from list."""
        try:
            while True:
                self.values.remove(value)
        except ValueError:
            return

    def as_string(self, delimiter: str = ",") -> str:
        """Get delimited string of all values. A comma followed by a space is used by
        default.

        If the ``Field`` has zero values, the empty string is returned. If the ``Field``
        has exactly one value, the value is returned unmodified.

        For ``Field``s with more than one value, the values are joined by a comma and a
        space. For such multi-valued ``Field``s, any values that already contain
        commas or double quotes will be surrounded by double quotes. Within any values
        that get quoted, pre-existing double quotes and backslashes are escaped with a
        backslash.
        """
        value_count = len(self.values)
        if value_count == 0:
            return ""
        if value_count == 1:
            return self.values[0]
        return delimiter.join(quote_and_escape_field_value(val) for val in self.values)

    def as_tuples(self) -> list[tuple[str, str]]:
        """Get list of ``name``, ``value`` tuples where each tuple represents one
        value."""
        return [(self.name, val) for val in self.values]

    def __eq__(self, other: object) -> bool:
        """Name, values, and kind must match.

        Values order must match.
        """
        if not isinstance(other, Field):
            return False
        return (
            self.name == other.name
            and self.kind is other.kind
            and self.values == other.values
        )

    def __repr__(self) -> str:
        return f"Field(name={self.name!r}, value={self.values!r}, kind={self.kind!r})"


class Fields(interfaces_http.Fields):
    def __init__(
        self,
        initial: Iterable[interfaces_http.Field] | None = None,
        *,
        encoding: str = "utf-8",
    ):
        """Collection of header and trailer entries mapped by name.

        :param initial: Initial list of ``Field`` objects. ``Field``s can also be added
        and later removed.
        :param encoding: The string encoding to be used when converting the ``Field``
        name and value from ``str`` to ``bytes`` for transmission.
        """
        init_fields = list(initial) if initial is not None else []
        init_field_names = [self._normalize_field_name(fld.name) for fld in init_fields]
        fname_counter = Counter(init_field_names)
        repeated_names_exist = (
            len(init_fields) > 0 and fname_counter.most_common(1)[0][1] > 1
        )
        if repeated_names_exist:
            non_unique_names = [name for name, num in fname_counter.items() if num > 1]
            raise ValueError(
                "Field names of the initial list of fields must be unique. The "
                "following normalized field names appear more than once: "
                f"{', '.join(non_unique_names)}."
            )
        init_tuples = zip(init_field_names, init_fields)
        self.entries: OrderedDict[str, interfaces_http.Field] = OrderedDict(init_tuples)
        self.encoding: str = encoding

    def set_field(self, field: interfaces_http.Field) -> None:
        """Alias for __setitem__ to utilize the field.name for the entry key."""
        self.__setitem__(field.name, field)

    def __setitem__(self, name: str, field: interfaces_http.Field) -> None:
        """Set or override entry for a Field name."""
        normalized_name = self._normalize_field_name(name)
        normalized_field_name = self._normalize_field_name(field.name)
        if normalized_name != normalized_field_name:
            raise ValueError(
                f"Supplied key {name} does not match Field.name "
                f"provided: {normalized_field_name}"
            )
        self.entries[normalized_name] = field

    def get(
        self, key: str, default: interfaces_http.Field | None = None
    ) -> interfaces_http.Field | None:
        return self[key] if key in self else default

    def __getitem__(self, name: str) -> interfaces_http.Field:
        """Retrieve Field entry."""
        normalized_name = self._normalize_field_name(name)
        return self.entries[normalized_name]

    def __delitem__(self, name: str) -> None:
        """Delete entry from collection."""
        normalized_name = self._normalize_field_name(name)
        del self.entries[normalized_name]

    def get_by_type(
        self, kind: interfaces_http.FieldPosition
    ) -> list[interfaces_http.Field]:
        """Helper function for retrieving specific types of fields.

        Used to grab all headers or all trailers.
        """
        return [entry for entry in self.entries.values() if entry.kind is kind]

    def extend(self, other: interfaces_http.Fields) -> None:
        """Merges ``entries`` of ``other`` into the current ``entries``.

        For every `Field` in the ``entries`` of ``other``: If the normalized name
        already exists in the current ``entries``, the values from ``other`` are
        appended. Otherwise, the ``Field`` is added to the list of ``entries``.
        """
        for other_field in other:
            try:
                cur_field = self.__getitem__(other_field.name)
                for other_value in other_field.values:
                    cur_field.add(other_value)
            except KeyError:
                self.__setitem__(other_field.name, other_field)

    def _normalize_field_name(self, name: str) -> str:
        """Normalize field names.

        For use as key in ``entries``.
        """
        return name.lower()

    def __eq__(self, other: object) -> bool:
        """Encoding must match.

        Entries must match in values and order.
        """
        if not isinstance(other, Fields):
            return False
        return self.encoding == other.encoding and self.entries == other.entries

    def __iter__(self) -> Iterator[interfaces_http.Field]:
        yield from self.entries.values()

    def __len__(self) -> int:
        return len(self.entries)

    def __repr__(self) -> str:
        return f"Fields({self.entries})"

    def __contains__(self, key: str) -> bool:
        return self._normalize_field_name(key) in self.entries


@dataclass(kw_only=True, frozen=True)
class URI(interfaces_http.URI):
    """Universal Resource Identifier, target location for a :py:class:`HTTPRequest`."""

    scheme: str = "https"
    """For example ``http`` or ``https``."""

    username: str | None = None
    """Username part of the userinfo URI component."""

    password: str | None = None
    """Password part of the userinfo URI component."""

    host: str
    """The hostname, for example ``amazonaws.com``."""

    port: int | None = None
    """An explicit port number."""

    path: str | None = None
    """Path component of the URI."""

    query: str | None = None
    """Query component of the URI as string."""

    fragment: str | None = None
    """Part of the URI specification, but may not be transmitted by a client."""

    @property
    def netloc(self) -> str:
        """Construct netloc string in format ``{username}:{password}@{host}:{port}``

        ``username``, ``password``, and ``port`` are only included if set. ``password``
        is ignored, unless ``username`` is also set.
        """
        return self._netloc

    # cached_property does NOT behave like property, it actually allows for setting.
    # Therefore we need a layer of indirection.
    @cached_property
    def _netloc(self) -> str:
        if self.username is not None:
            password = "" if self.password is None else f":{self.password}"
            userinfo = f"{self.username}{password}@"
        else:
            userinfo = ""

        if self.port is not None:
            port = f":{self.port}"
        else:
            port = ""

        host = self.host

        return f"{userinfo}{host}{port}"

    def build(self) -> str:
        """Construct URI string representation.

        Validate host. Returns a string of the form
        ``{scheme}://{username}:{password}@{host}:{port}{path}?{query}#{fragment}``
        """
        components = (
            self.scheme,
            self.netloc,
            self.path or "",
            "",  # params
            self.query,
            self.fragment,
        )
        return urlunparse(components)

    def to_dict(self) -> URIParameters:
        return {
            "scheme": self.scheme,
            "host": self.host,
            "port": self.port,
            "path": self.path,
            "query": self.query,
            "username": self.username,
            "password": self.password,
            "fragment": self.fragment,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, URI):
            return False
        return (
            self.scheme == other.scheme
            and self.host == other.host
            and self.port == other.port
            and self.path == other.path
            and self.query == other.query
            and self.username == other.username
            and self.password == other.password
            and self.fragment == other.fragment
        )


class URIParameters(TypedDict):
    """TypedDict representing the parameters for the URI class.

    These need to be kept in sync for the `to_dict` method.
    """

    # TODO: Unpack doesn't seem to do what we want, so we need a way to represent
    # returning a class' parameters as a dict. There must be a better way to do this.

    scheme: str
    username: str | None
    password: str | None
    host: str
    port: int | None
    path: str | None
    query: str | None
    fragment: str | None


class AWSRequest(interfaces_http.Request):
    def __init__(
        self,
        *,
        destination: URI,
        method: str,
        body: AsyncIterable[bytes] | Iterable[bytes] | None,
        fields: Fields,
    ):
        self.destination = destination
        self.method = method
        self.body = body
        self.fields = fields

    def __deepcopy__(self, memo: dict[int, AWSRequest] | None = None) -> AWSRequest:
        if memo is None:
            memo = {}

        if id(self) in memo:
            return memo[id(self)]

        # the destination doesn't need to be copied because it's immutable
        # the body can't be copied because it's an iterator
        new_instance = self.__class__(
            destination=self.destination,  # pyright: ignore [reportArgumentType]
            body=self.body,
            method=self.method,
            fields=deepcopy(self.fields, memo),
        )
        memo[id(new_instance)] = new_instance
        return new_instance


def quote_and_escape_field_value(value: str) -> str:
    """Escapes and quotes a single :class:`Field` value if necessary.

    See :func:`Field.as_string` for quoting and escaping logic.
    """
    chars_to_quote = (",", '"')
    if any(char in chars_to_quote for char in value):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    else:
        return value
