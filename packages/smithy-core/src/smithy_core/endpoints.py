# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlparse

from . import URI
from .exceptions import EndpointResolutionError
from .interfaces import Endpoint as _Endpoint
from .interfaces import TypedProperties as _TypedProperties
from .interfaces import URI as _URI
from .schemas import APIOperation
from .serializers import SerializeableShape
from .types import PropertyKey, TypedProperties


@dataclass(kw_only=True)
class Endpoint(_Endpoint):
    """A resolved endpoint."""

    uri: _URI
    """The endpoint URI."""

    properties: _TypedProperties = field(default_factory=TypedProperties)
    """Properties required to interact with the endpoint.

    For example, in some AWS use cases this might contain HTTP headers to add to each
    request.
    """


@dataclass(kw_only=True)
class EndpointResolverParams[I: SerializeableShape]:
    """Parameters passed into an Endpoint Resolver's resolve_endpoint method."""

    operation: APIOperation[I, Any]
    """The operation to resolve an endpoint for."""

    input: I
    """The input to the operation."""

    context: _TypedProperties
    """The context of the operation invocation."""


class StaticEndpointConfig(Protocol):
    """A config that has a static endpoint."""

    endpoint_uri: str | URI | None
    """A static endpoint to use for the request."""


STATIC_ENDPOINT_CONFIG = PropertyKey(key="config", value_type=StaticEndpointConfig)
"""Property containing a config that has a static endpoint."""


def resolve_static_uri(
    properties: _TypedProperties | EndpointResolverParams[Any],
) -> _URI | None:
    """Attempt to resolve a static URI from the endpoint resolver params.

    :param properties: A TypedProperties bag or EndpointResolverParams to search.
    """
    properties = (
        properties.context
        if isinstance(properties, EndpointResolverParams)
        else properties
    )
    static_uri_config = properties.get(STATIC_ENDPOINT_CONFIG)
    if static_uri_config is None or static_uri_config.endpoint_uri is None:
        return None

    static_uri = static_uri_config.endpoint_uri

    # If it's not a string, it's already a parsed URI so just pass it along.
    if not isinstance(static_uri, str):
        return static_uri

    parsed = urlparse(static_uri)
    if parsed.hostname is None:
        raise EndpointResolutionError(
            f"Unable to parse hostname from provided URI: {static_uri}"
        )

    return URI(
        host=parsed.hostname,
        path=parsed.path,
        scheme=parsed.scheme,
        query=parsed.query,
        port=parsed.port,
    )
