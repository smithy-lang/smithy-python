#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from smithy_core.interfaces import Request, Response
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeID
from smithy_core.utils import read_streaming_blob

__all__ = [
    "Field",
    "FieldPosition",
    "Fields",
    "HTTPClient",
    "HTTPClientConfiguration",
    "HTTPErrorIdentifier",
    "HTTPRequest",
    "HTTPRequestConfiguration",
    "HTTPResponse",
    "QueryParamsList",
]

FieldPosition = Literal["header", "trailer"]
"""The type of a field.

Defines its placement in a request or response.

header: Header field. In HTTP this is a header as defined in RFC 9110 Section 6.3.
trailer: Trailer field. In HTTP this is a trailer as defined in RFC 9110 Section 6.5.

Implementations of other protocols may use this FieldPosition for similar types of metadata.
"""


class Field(Protocol):
    """A name-value pair representing a single field in a request or response.

    The kind will dictate metadata placement within an the message, for example as
    header or trailer field in a HTTP request as defined in RFC 9110 Section 5.

    All field names are case insensitive and case-variance must be treated as
    equivalent. Names may be normalized but should be preserved for accuracy during
    transmission.
    """

    name: str
    values: list[str]
    kind: FieldPosition = "header"

    def add(self, value: str) -> None:
        """Append a value to a field."""
        ...

    def set(self, values: list[str]) -> None:
        """Overwrite existing field values."""
        ...

    def remove(self, value: str) -> None:
        """Remove all matching entries from list."""
        ...

    def as_string(self, delimiter: str = ",") -> str:
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
    entries: dict[str, Field]
    encoding: str = "utf-8"

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

    def __contains__(self, key: str) -> bool:
        """Allows in/not in checks on Field entries."""
        ...

    def set_field(self, field: Field) -> None:
        """Alias for __setitem__ to utilize the field.name for the entry key."""
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


class HTTPRequest(Request, Protocol):
    """HTTP primitive for an Exchange to construct a version agnostic HTTP message.

    :param destination: The URI where the request should be sent to.
    :param method: The HTTP method of the request, for example "GET".
    :param fields: ``Fields`` object containing HTTP headers and trailers.
    :param body: A streamable collection of bytes.
    """

    method: str
    fields: Fields

    def consume_body(self) -> bytes:
        """Read the request body into bytes."""
        return read_streaming_blob(self.body)


class HTTPResponse(Response, Protocol):
    """HTTP primitives returned from an Exchange, used to construct a client
    response."""

    @property
    def status(self) -> int:
        """The 3 digit response status code (1xx, 2xx, 3xx, 4xx, 5xx)."""
        ...

    @property
    def fields(self) -> Fields:
        """``Fields`` object containing HTTP headers and trailers."""
        ...

    @property
    def reason(self) -> str | None:
        """Optional string provided by the server explaining the status."""
        ...

    def consume_body(self) -> bytes:
        """Read the response body into bytes."""
        return read_streaming_blob(self.body)


class HTTPErrorIdentifier:
    """A class that uses HTTP response metadata to identify errors.

    The body of the response SHOULD NOT be touched by this. The payload codec will be
    used instead to check for an ID in the body.
    """

    def identify(
        self,
        *,
        operation: APIOperation[Any, Any],
        response: HTTPResponse,
    ) -> ShapeID | None:
        """Idenitfy the ShapeID of an error from an HTTP response."""


QueryParamsList = list[tuple[str, str]]


@dataclass(kw_only=True)
class HTTPClientConfiguration:
    """Client-level HTTP configuration.

    :param force_http_2: Whether to require HTTP/2.
    """

    force_http_2: bool = False


@dataclass(kw_only=True)
class HTTPRequestConfiguration:
    """Request-level HTTP configuration.

    :param read_timeout: How long, in seconds, the client will attempt to read the first
        byte over an established, open connection before timing out.
    """

    read_timeout: float | None = None


class HTTPClient(Protocol):
    """A synchronous HTTP client interface.

    Header field names and values are not validated before reaching this layer.
    Implementations of ``HTTPClient`` are responsible for validating and handling those
    invalid and dangerous characters (such as CR, LF, or NUL) as defined in `RFC 9110,
    Section 5.5 <https://www.rfc-editor.org/rfc/rfc9110#section-5.5>`_.
    """

    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...]

    def __init__(self, *, client_config: HTTPClientConfiguration | None) -> None:
        """
        :param client_config: Configuration that applies to all requests made with this
        client.
        """
        ...

    def send(
        self,
        request: HTTPRequest,
        *,
        request_config: HTTPRequestConfiguration | None = None,
    ) -> HTTPResponse:
        """Send HTTP request over the wire and return the response.

        :param request: The request including destination URI, fields, payload.
        :param request_config: Configuration specific to this request.
        """
        ...
