# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

# TODO: move all of this out of _private


from collections import Counter, OrderedDict
from collections.abc import AsyncIterable, Iterable, Iterator
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlparse, urlunparse

from ... import interfaces
from ...interfaces.http import FieldPosition as FieldPosition  # re-export


@dataclass(kw_only=True)
class URI(interfaces.URI):
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
        if self.username is not None:
            password = "" if self.password is None else f":{self.password}"
            userinfo = f"{self.username}{password}@"
        else:
            userinfo = ""
        port = "" if self.port is None else f":{self.port}"
        return f"{userinfo}{self.host}{port}"

    def build(self) -> str:
        """Construct URI string representation.

        Returns a string of the form
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


@dataclass(kw_only=True)
class HTTPRequest(interfaces.http.HTTPRequest):
    """HTTP primitives for an Exchange to construct a version agnostic HTTP message."""

    destination: interfaces.URI
    body: AsyncIterable[bytes]
    method: str
    fields: interfaces.http.Fields

    async def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        body = b""
        async for chunk in self.body:
            body += chunk
        return body


# HTTPResponse implements interfaces.http.HTTPResponse but cannot be explicitly
# annotated to reflect this because doing so causes Python to raise an AttributeError.
# See https://github.com/python/typing/discussions/903#discussioncomment-4866851 for
# details.
@dataclass(kw_only=True)
class HTTPResponse:
    """Basic implementation of :py:class:`...interfaces.http.HTTPResponse`.

    Implementations of :py:class:`...interfaces.http.HTTPClient` may return instances of
    this class or of custom response implementatinos.
    """

    body: AsyncIterable[bytes]
    """The response payload as iterable of chunks of bytes."""

    status: int
    """The 3 digit response status code (1xx, 2xx, 3xx, 4xx, 5xx)."""

    fields: interfaces.http.Fields
    """HTTP header and trailer fields."""

    reason: str | None = None
    """Optional string provided by the server explaining the status."""

    async def consume_body(self) -> bytes:
        """Iterate over response body and return as bytes."""
        body = b""
        async for chunk in self.body:
            body += chunk
        return body


class Field(interfaces.http.Field):
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
        kind: FieldPosition = FieldPosition.HEADER,
    ):
        self.name = name
        self.values: list[str] = [val for val in values] if values is not None else []
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

    def as_string(self) -> str:
        """Get comma-delimited string of all values.

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
        return ", ".join(quote_and_escape_field_value(val) for val in self.values)

    def as_tuples(self) -> list[tuple[str, str]]:
        """Get list of ``name``, ``value`` tuples where each tuple represents one
        value."""
        return [(self.name, val) for val in self.values]

    def __eq__(self, other: object) -> bool:
        """Checks equality.

        Name, values, and kind must match. Values order must match.
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


class Fields(interfaces.http.Fields):
    def __init__(
        self,
        initial: Iterable[interfaces.http.Field] | None = None,
        *,
        encoding: str = "utf-8",
    ):
        """Collection of header and trailer entries mapped by name.

        :param initial: Initial list of ``Field`` objects. ``Field``s can alse be added
        with :func:`set_field` and later removed with :func:`remove_field`.
        :param encoding: The string encoding to be used when converting the ``Field``
        name and value from ``str`` to ``bytes`` for transmission.
        """
        init_fields = [fld for fld in initial] if initial is not None else []
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
        self.entries: OrderedDict[str, interfaces.http.Field] = OrderedDict(init_tuples)
        self.encoding: str = encoding

    def set_field(self, field: interfaces.http.Field) -> None:
        """Set entry for a Field name."""
        normalized_name = self._normalize_field_name(field.name)
        self.entries[normalized_name] = field

    def get_field(self, name: str) -> interfaces.http.Field:
        """Retrieve Field entry."""
        normalized_name = self._normalize_field_name(name)
        return self.entries[normalized_name]

    def remove_field(self, name: str) -> None:
        """Delete entry from collection."""
        normalized_name = self._normalize_field_name(name)
        del self.entries[normalized_name]

    def get_by_type(self, kind: FieldPosition) -> list[interfaces.http.Field]:
        """Helper function for retrieving specific types of fields.

        Used to grab all headers or all trailers.
        """
        return [entry for entry in self.entries.values() if entry.kind is kind]

    def extend(self, other: interfaces.http.Fields) -> None:
        """Merges ``entries`` of ``other`` into the current ``entries``.

        For every `Field` in the ``entries`` of ``other``: If the normalized name
        already exists in the current ``entries``, the values from ``other`` are
        appended. Otherwise, the ``Field`` is added to the list of ``entries``.
        """
        for other_field in other:
            try:
                cur_field = self.get_field(name=other_field.name)
                for other_value in other_field.values:
                    cur_field.add(other_value)
            except KeyError:
                self.set_field(other_field)

    def _normalize_field_name(self, name: str) -> str:
        """Normalize field names.

        For use as key in ``entries``.
        """
        return name.lower()

    def __eq__(self, other: object) -> bool:
        """Checks equality.

        Encoding must match. Entries must match in values and order.
        """
        if not isinstance(other, Fields):
            return False
        return self.encoding == other.encoding and self.entries == other.entries

    def __iter__(self) -> Iterator[interfaces.http.Field]:
        yield from self.entries.values()


def tuples_to_fields(
    tuples: Iterable[tuple[str, str]], *, kind: FieldPosition | None = None
) -> Fields:
    """Convert ``name``, ``value`` tuples to ``Fields`` object. Each tuple represents
    one Field value.

    :param kind: The Field kind to define for all tuples.
    """
    fields = Fields()
    for name, value in tuples:
        try:
            fields.get_field(name).add(value)
        except KeyError:
            fields.set_field(
                Field(name=name, values=[value], kind=kind or FieldPosition.HEADER)
            )

    return fields


@dataclass
class Endpoint(interfaces.http.Endpoint):
    uri: interfaces.URI
    headers: interfaces.http.Fields = field(default_factory=Fields)


@dataclass
class StaticEndpointParams:
    """Static endpoint params.

    :param uri: A static URI to route requests to.
    """

    uri: str | interfaces.URI


class StaticEndpointResolver(interfaces.http.EndpointResolver[StaticEndpointParams]):
    """A basic endpoint resolver that forwards a static URI."""

    async def resolve_endpoint(self, params: StaticEndpointParams) -> Endpoint:
        # If it's not a string, it's already a parsed URI so just pass it along.
        if not isinstance(params.uri, str):
            return Endpoint(uri=params.uri)

        # Does crt have implementations of these parsing methods? Using the standard
        # library is probably fine.
        parsed = urlparse(params.uri)

        # This will end up getting wrapped in the client.
        if parsed.hostname is None:
            raise ValueError(
                f"Unable to parse hostname from provided URI: {params.uri}"
            )

        return Endpoint(
            uri=URI(
                host=parsed.hostname,
                path=parsed.path,
                scheme=parsed.scheme,
                query=parsed.query,
                port=parsed.port,
            )
        )


class _StaticEndpointConfig(Protocol):
    endpoint_resolver: interfaces.http.EndpointResolver[StaticEndpointParams] | None


def set_static_endpoint_resolver(config: _StaticEndpointConfig) -> None:
    """Sets the endpoint resolver to the static endpoint resolver if not already set.

    :param config: A config object that has an endpoint_resolver property.
    """
    if config.endpoint_resolver is None:
        config.endpoint_resolver = StaticEndpointResolver()
