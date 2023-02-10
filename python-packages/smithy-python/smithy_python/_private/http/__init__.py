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


from collections.abc import AsyncIterable
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlparse

from ...interfaces import URI, Fields
from ...interfaces.http import Endpoint as EndpointInterface
from ...interfaces.http import EndpointResolver as EndpointResolverInterface
from ...interfaces.http import HTTPRequest as HTTPRequestInterface
from .. import URI as _URI
from .. import Fields as _Fields


@dataclass(kw_only=True)
class HTTPRequest(HTTPRequestInterface):
    """HTTP primitives for an Exchange to construct a version agnostic HTTP message."""

    destination: URI
    body: AsyncIterable[bytes]
    method: str
    fields: Fields

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

    fields: Fields
    """HTTP header and trailer fields."""

    reason: str | None = None
    """Optional string provided by the server explaining the status."""

    async def consume_body(self) -> bytes:
        """Iterate over response body and return as bytes."""
        body = b""
        async for chunk in self.body:
            body += chunk
        return body


@dataclass
class Endpoint(EndpointInterface):
    uri: URI
    headers: Fields = field(default_factory=_Fields)


@dataclass
class StaticEndpointParams:
    """Static endpoint params.

    :param uri: A static URI to route requests to.
    """

    uri: str | URI


class StaticEndpointResolver(EndpointResolverInterface[StaticEndpointParams]):
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
            uri=_URI(
                host=parsed.hostname,
                path=parsed.path,
                scheme=parsed.scheme,
                query=parsed.query,
                port=parsed.port,
            )
        )


class _StaticEndpointConfig(Protocol):
    endpoint_resolver: EndpointResolverInterface[StaticEndpointParams] | None


def set_static_endpoint_resolver(config: _StaticEndpointConfig) -> None:
    """Sets the endpoint resolver to the static endpoint resolver if not already set.

    :param config: A config object that has an endpoint_resolver property.
    """
    if config.endpoint_resolver is None:
        config.endpoint_resolver = StaticEndpointResolver()
