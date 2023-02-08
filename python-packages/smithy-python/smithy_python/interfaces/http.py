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
from collections import OrderedDict
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypeVar

from . import URI, Request, Response

QueryParamsList = list[tuple[str, str]]


class FieldPosition(Enum):
    """
    The type of a field. Defines its placement in a request or response.
    """

    HEADER = 0
    """
    Header field. In HTTP this is a header as defined in RFC 9114 Section 6.3.
    Implementations of other protocols may use this FieldPosition for similar types
    of metadata.
    """

    TRAILER = 1
    """
    Trailer field. In HTTP this is a trailer as defined in RFC 9114 Section 6.5.
    Implementations of other protocols may use this FieldPosition for similar types
    of metadata.
    """


class Field(Protocol):
    """
    A name-value pair representing a single field in a request or response.

    The kind will dictate metadata placement within an the message, for example as
    header or trailer field in a HTTP request as defined in RFC 9114 Section 4.2.

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

    def as_string(self) -> str:
        """Serialize the ``Field``'s values into a single line string."""
        ...

    def as_tuples(self) -> list[tuple[str, str]]:
        """
        Get list of ``name``, ``value`` tuples where each tuple represents one value.
        """
        ...


class Fields(Protocol):
    """
    Protocol agnostic mapping of key-value pair request metadata, such as HTTP fields.
    """

    # Entries are keyed off the name of a provided Field
    entries: OrderedDict[str, Field]
    encoding: str | None = "utf-8"

    def set_field(self, field: Field) -> None:
        """Set entry for a Field name."""
        ...

    def get_field(self, name: str) -> Field:
        """Retrieve Field entry."""
        ...

    def remove_field(self, name: str) -> None:
        """Delete entry from collection."""
        ...

    def get_by_type(self, kind: FieldPosition) -> list[Field]:
        """Helper function for retrieving specific types of fields.

        Used to grab all headers or all trailers.
        """
        ...

    def extend(self, other: "Fields") -> None:
        """Merges ``entries`` of ``other`` into the current ``entries``.

        For every `Field` in the ``entries`` of ``other``: If the normalized name
        already exists in the current ``entries``, the values from ``other`` are
        appended. Otherwise, the ``Field`` is added to the list of ``entries``.
        """
        ...

    def __iter__(self) -> Iterator[Field]:
        """Allow iteration over entries."""
        ...


class HttpRequest(Request, Protocol):
    """
    HTTP primitive for an Exchange to construct a version agnostic HTTP message.

    :param destination: The URI where the request should be sent to.
    :param method: The HTTP method of the request, for example "GET".
    :param fields: List of HTTP header fields.
    :param body: A streamable collection of bytes.
    """

    method: str
    fields: Fields


class HttpResponse(Response, Protocol):
    """
    HTTP primitives returned from an Exchange, used to construct a client response.
    """

    @property
    def status(self) -> int:
        """The 3 digit response status code (1xx, 2xx, 3xx, 4xx, 5xx)."""
        ...

    @property
    def fields(self) -> Fields:
        """HTTP header and trailer fields."""
        ...

    @property
    def reason(self) -> str | None:
        """Optional string provided by the server explaining the status."""
        ...


class Endpoint(Protocol):
    url: URI
    headers: Fields


# EndpointParams are defined in the generated client, so we use a TypeVar here.
# More specific EndpointParams implementations are subtypes of less specific ones. But
# consumers of less specific EndpointParams implementations are subtypes of consumers
# of more specific ones.
EndpointParams = TypeVar("EndpointParams", contravariant=True)


class EndpointResolver(Protocol[EndpointParams]):
    """Resolves an operation's endpoint based given parameters."""

    async def resolve_endpoint(self, params: EndpointParams) -> Endpoint:
        raise NotImplementedError()


@dataclass(kw_only=True)
class HttpClientConfiguration:
    """Client-level HTTP configuration.

    :param force_http_2: Whether to require HTTP/2.
    """

    force_http_2: bool = False


@dataclass(kw_only=True)
class HttpRequestConfiguration:
    """Request-level HTTP configuration.

    :param read_timeout: How long, in seconds, the client will attempt to read the
    first byte over an established, open connection before timing out.
    """

    read_timeout: float | None = None


class HttpClient(Protocol):
    """An asynchronous HTTP client interface."""

    def __init__(self, *, client_config: HttpRequestConfiguration | None) -> None:
        """
        :param client_config: Configuration that applies to all requests made with this
        client.
        """
        ...

    async def send(
        self, *, request: HttpRequest, request_config: HttpRequestConfiguration | None
    ) -> HttpResponse:
        """
        Send HTTP request over the wire and return the response.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        ...
