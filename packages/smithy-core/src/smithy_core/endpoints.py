# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any
from dataclasses import dataclass, field
from urllib.parse import urlparse

from . import URI
from .serializers import SerializeableShape
from .schemas import APIOperation
from .interfaces import TypedProperties as _TypedProperties
from .interfaces import Endpoint as _Endpoint
from .interfaces import URI as _URI
from .types import TypedProperties, PropertyKey
from .exceptions import EndpointResolutionError


STATIC_URI: PropertyKey[str | _URI] = PropertyKey(
    key="endpoint_uri",
    # Python currently has problems expressing parametric types that can be
    # unions, literals, or other special types in addition to a class. So
    # we have to ignore the type below. PEP 747 should resolve the issue.
    # TODO: update this when PEP 747 lands
    value_type=str | _URI,  # type: ignore
)
"""The property key for a statically defined URI."""


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
    static_uri = properties.get(STATIC_URI)
    if static_uri is None:
        return None

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
