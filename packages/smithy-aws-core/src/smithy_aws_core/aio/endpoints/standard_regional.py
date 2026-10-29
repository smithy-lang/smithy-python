#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any

from smithy_core.aio.interfaces import AsyncEndpointResolver
from smithy_core.endpoints import Endpoint, EndpointResolverParams

from ...endpoints.standard_regional import StandardRegionalEndpointsResolver

__all__ = ["AsyncStandardRegionalEndpointsResolver"]


class AsyncStandardRegionalEndpointsResolver(AsyncEndpointResolver):
    """Resolves endpoints for services with standard regional endpoints."""

    def __init__(self, endpoint_prefix: str = "bedrock-runtime"):
        self._sync = StandardRegionalEndpointsResolver(endpoint_prefix)

    async def resolve_endpoint(self, params: EndpointResolverParams[Any]) -> Endpoint:
        return self._sync.resolve_endpoint(params)
