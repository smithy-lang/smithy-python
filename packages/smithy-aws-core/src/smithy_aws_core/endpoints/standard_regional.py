#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any

from smithy_core import URI
from smithy_core.aio.interfaces import EndpointResolver
from smithy_core.endpoints import Endpoint, EndpointResolverParams, resolve_static_uri
from smithy_core.exceptions import EndpointResolutionError

from . import REGIONAL_ENDPOINT_CONFIG


class StandardRegionalEndpointsResolver(EndpointResolver):
    """Resolves endpoints for services with standard regional endpoints."""

    def __init__(self, endpoint_prefix: str = "bedrock-runtime"):
        self._endpoint_prefix = endpoint_prefix

    async def resolve_endpoint(self, params: EndpointResolverParams[Any]) -> Endpoint:
        if (static_uri := resolve_static_uri(params)) is not None:
            return Endpoint(uri=static_uri)

        region_config = params.context.get(REGIONAL_ENDPOINT_CONFIG)
        if region_config is not None and region_config.region is not None:
            # TODO: use dns suffix determined from partition metadata
            dns_suffix = "amazonaws.com"
            hostname = f"{self._endpoint_prefix}.{region_config.region}.{dns_suffix}"

            return Endpoint(uri=URI(host=hostname))

        raise EndpointResolutionError(
            "Unable to resolve endpoint - either endpoint_url or region are required."
        )
