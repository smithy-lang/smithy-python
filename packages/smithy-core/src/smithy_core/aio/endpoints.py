#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any

from ..endpoints import EndpointResolverParams, StaticEndpointResolver
from ..interfaces import Endpoint as _Endpoint
from .interfaces import AsyncEndpointResolver

__all__ = ["AsyncStaticEndpointResolver"]

_STATIC = StaticEndpointResolver()


class AsyncStaticEndpointResolver(AsyncEndpointResolver):
    """A basic endpoint resolver that forwards a static URI."""

    async def resolve_endpoint(self, params: EndpointResolverParams[Any]) -> _Endpoint:
        return _STATIC.resolve_endpoint(params)
