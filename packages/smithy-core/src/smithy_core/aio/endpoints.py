#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any

from ..endpoints import Endpoint, EndpointResolverParams, resolve_static_uri
from ..exceptions import EndpointResolutionError
from ..interfaces import Endpoint as _Endpoint
from .interfaces import EndpointResolver


class StaticEndpointResolver(EndpointResolver):
    """A basic endpoint resolver that forwards a static URI."""

    async def resolve_endpoint(self, params: EndpointResolverParams[Any]) -> _Endpoint:
        static_uri = resolve_static_uri(params)
        if static_uri is None:
            raise EndpointResolutionError(
                "Unable to resolve endpoint: endpoint_uri is required"
            )

        return Endpoint(uri=static_uri)
