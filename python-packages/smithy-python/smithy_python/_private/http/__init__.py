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
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlparse, urlunparse

from ... import interfaces
from ...interfaces.http import FieldPosition as FieldPosition  # re-export


class URI:
    def __init__(
        self,
        host: str,
        path: str | None = None,
        scheme: str | None = None,
        query: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        fragment: str | None = None,
    ):
        self.scheme: str = "https" if scheme is None else scheme
        self.host = host
        self.port = port
        self.path = path
        self.query = query
        self.username = username
        self.password = password
        self.fragment = fragment

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


class Request:
    def __init__(
        self,
        url: interfaces.http.URI,
        method: str = "GET",
        headers: interfaces.http.HeadersList | None = None,
        body: Any = None,
    ):
        self.url: interfaces.http.URI = url
        self.method: str = method
        self.body: Any = body
        self.headers: interfaces.http.HeadersList = []
        if headers is not None:
            self.headers = headers


class Response:
    def __init__(
        self,
        status_code: int,
        headers: interfaces.http.HeadersList,
        body: Any,
    ):
        self.status_code: int = status_code
        self.headers: interfaces.http.HeadersList = headers
        self.body: Any = body


class Field(interfaces.http.Field):
    """
    A name-value pair representing a single field in an HTTP Request or Response.

    The kind will dictate metadata placement within an HTTP message.

    All field names are case insensitive and case-variance must be treated as
    equivalent. Names may be normalized but should be preserved for accuracy during
    transmission.
    """

    def __init__(
        self,
        name: str,
        value: Iterable[str] | None = None,
        kind: FieldPosition = FieldPosition.HEADER,
    ):
        self.name = name
        self.value: list[str] = [val for val in value] if value is not None else []
        self.kind = kind

    def add(self, value: str) -> None:
        """Append a value to a field."""
        self.value.append(value)

    def set(self, value: list[str]) -> None:
        """Overwrite existing field values."""
        self.value = value

    def remove(self, value: str) -> None:
        """Remove all matching entries from list."""
        try:
            while True:
                self.value.remove(value)
        except ValueError:
            return

    def as_string(self) -> str:
        """
        Get comma-delimited string of all values.

        If the ``Field`` has zero values, the empty string is returned. If the ``Field``
        has exactly one value, the value is returned unmodified.

        For ``Field``s with more than one value, the values are joined by a comma and a
        space. For such multi-valued ``Field``s, any values that already contain
        commas or double quotes will be surrounded by double quotes. Within any values
        that get quoted, pre-existing double quotes and backslashes are escaped with a
        backslash.
        """
        value_count = len(self.value)
        if value_count == 0:
            return ""
        if value_count == 1:
            return self.value[0]
        return ", ".join(quote_and_escape_field_value(val) for val in self.value)

    def as_tuples(self) -> list[tuple[str, str]]:
        """
        Get list of ``name``, ``value`` tuples where each tuple represents one value.
        """
        return [(self.name, val) for val in self.value]

    def __eq__(self, other: object) -> bool:
        """Name, values, and kind must match. Values order must match."""
        if not isinstance(other, Field):
            return False
        return (
            self.name == other.name
            and self.kind is other.kind
            and self.value == other.value
        )

    def __repr__(self) -> str:
        return f"Field(name={self.name!r}, value={self.value!r}, kind={self.kind!r})"


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
        """
        Collection of header and trailer entries mapped by name.

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

    def _normalize_field_name(self, name: str) -> str:
        """Normalize field names. For use as key in ``entries``."""
        return name.lower()

    def __eq__(self, other: object) -> bool:
        """Encoding must match. Entries must match in values and order."""
        if not isinstance(other, Fields):
            return False
        return self.encoding == other.encoding and self.entries == other.entries

    def __iter__(self) -> Iterable[interfaces.http.Field]:
        yield from self.entries.values()


@dataclass
class Endpoint(interfaces.http.Endpoint):
    url: interfaces.http.URI
    headers: interfaces.http.HeadersList = field(default_factory=list)


@dataclass
class StaticEndpointParams:
    """
    Static endpoint params.

    :params url: A static URI to route requests to.
    """

    url: str | interfaces.http.URI


class StaticEndpointResolver(interfaces.http.EndpointResolver[StaticEndpointParams]):
    """A basic endpoint resolver that forwards a static url."""

    async def resolve_endpoint(self, params: StaticEndpointParams) -> Endpoint:
        # If it's not a string, it's already a parsed URL so just pass it along.
        if not isinstance(params.url, str):
            return Endpoint(url=params.url)

        # Does crt have implementations of these parsing methods? Using the standard
        # library is probably fine.
        parsed = urlparse(params.url)

        # This will end up getting wrapped in the client.
        if parsed.hostname is None:
            raise ValueError(
                f"Unable to parse hostname from provided url: {params.url}"
            )

        return Endpoint(
            url=URI(
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
    """
    Sets the endpoint resolver to the static endpoint resolver if not already set.

    :param config: A config object that has an endpoint_resolver property.
    """
    if config.endpoint_resolver is None:
        config.endpoint_resolver = StaticEndpointResolver()
