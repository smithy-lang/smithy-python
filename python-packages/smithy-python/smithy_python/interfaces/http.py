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
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, TypeVar

# Defining headers as a list instead of a mapping to avoid ambiguity and
# the nuances of multiple fields in a mapping style interface
HeadersList = list[tuple[str, str]]
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
    A name-value pair representing a single field in a request or response

    The kind will dictate metadata placement within an the message, for example as
    header or trailer field in a HTTP request as defined in RFC 9114 Section 4.2.

    All field names are case insensitive and case-variance must be treated as
    equivalent. Names may be normalized but should be preserved for accuracy during
    transmission.
    """

    name: str
    value: list[str] | None = None
    kind: FieldPosition = FieldPosition.HEADER

    def add(self, value: str) -> None:
        """Append a value to a field."""
        ...

    def set(self, value: list[str]) -> None:
        """Overwrite existing field values."""
        ...

    def remove(self, value: str) -> None:
        """Remove all matching entries from list."""
        ...

    def get_value(self) -> str:
        """Get comma-delimited string.

        Values containing commas or quotes are double-quoted.
        """
        ...

    def get_value_list(self) -> list[str]:
        """Get string values as a list."""
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


class URI(Protocol):
    """Universal Resource Identifier, target location for a :py:class:`Request`."""

    scheme: str
    """For example ``http`` or ``https``."""

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


class Request(Protocol):
    url: URI
    method: str  # GET, PUT, etc
    headers: HeadersList
    body: Any


class Response(Protocol):
    status_code: int  # HTTP status code
    headers: HeadersList
    body: Any


class Endpoint(Protocol):
    url: URI
    headers: HeadersList


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
class HttpRequestConfiguration:
    """Request-level HTTP configuration.

    :param read_timeout: How long, in seconds, the client will attempt to read the
    first byte over an established, open connection before timing out.
    """

    read_timeout: float | None = None


class HttpClient(Protocol):
    """A synchronous HTTP client interface."""

    def send(
        self, request: Request, request_config: HttpRequestConfiguration
    ) -> Response:
        pass


class AsyncHttpClient(Protocol):
    """An asynchronous HTTP client interface."""

    async def send(
        self, request: Request, request_config: HttpRequestConfiguration
    ) -> Response:
        pass
