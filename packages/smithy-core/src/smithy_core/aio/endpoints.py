#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from typing import Any

from ..endpoints import BddEndpointResolver as _BddEndpointResolver
from ..endpoints import (
    Endpoint,
    EndpointBdd,
    EndpointResolverParams,
    RulesExtension,
    resolve_static_uri,
)
from ..exceptions import EndpointResolutionError
from ..interfaces import Endpoint as _Endpoint
from .interfaces import AsyncEndpointResolver as _AsyncEndpointResolver

__all__ = ["AsyncBddEndpointResolver", "AsyncStaticEndpointResolver"]


class AsyncStaticEndpointResolver(_AsyncEndpointResolver):
    """A basic endpoint resolver that forwards a static URI."""

    async def resolve_endpoint(self, params: EndpointResolverParams[Any]) -> _Endpoint:
        static_uri = resolve_static_uri(params)
        if static_uri is None:
            raise EndpointResolutionError(
                "Unable to resolve endpoint: endpoint_uri is required"
            )

        return Endpoint(uri=static_uri)


class AsyncBddEndpointResolver(_AsyncEndpointResolver):
    """Resolves endpoints by evaluating a service's endpoint binary decision diagram."""

    def __init__(
        self,
        bdd: EndpointBdd,
        *,
        extensions: Sequence[RulesExtension] = (),
    ) -> None:
        """Create a resolver for an endpoint BDD.

        :param bdd: The service's endpoint binary decision diagram.
        :param extensions: Functions and built-in bindings beyond the rules standard
            library, which is always included.
        """
        self._sync = _BddEndpointResolver(bdd, extensions=extensions)

    def __deepcopy__(self, memo: Any) -> "AsyncBddEndpointResolver":
        return self

    async def resolve_endpoint(self, params: EndpointResolverParams[Any]) -> _Endpoint:
        return self._sync.resolve_endpoint(params)
