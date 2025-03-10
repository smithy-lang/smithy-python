#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import Protocol, Self
from urllib.parse import urlparse

import smithy_core
from smithy_core import URI
from smithy_http.aio.interfaces import (
    EndpointResolver,
    EndpointParameters,
)
from smithy_http.endpoints import Endpoint
from smithy_http.exceptions import EndpointResolutionError


class _RegionUriConfig(Protocol):
    endpoint_uri: str | smithy_core.interfaces.URI | None
    region: str | None


@dataclass(kw_only=True)
class RegionalEndpointParameters(EndpointParameters[_RegionUriConfig]):
    """Endpoint parameters for services with standard regional endpoints."""

    sdk_endpoint: str | smithy_core.interfaces.URI | None
    region: str | None

    @classmethod
    def build(cls, config: _RegionUriConfig) -> Self:
        return cls(sdk_endpoint=config.endpoint_uri, region=config.region)


class StandardRegionalEndpointsResolver(EndpointResolver[RegionalEndpointParameters]):
    """Resolves endpoints for services with standard regional endpoints."""

    def __init__(self, endpoint_prefix: str = "bedrock-runtime"):
        self._endpoint_prefix = endpoint_prefix

    async def resolve_endpoint(self, params: RegionalEndpointParameters) -> Endpoint:
        if params.sdk_endpoint is not None:
            # If it's not a string, it's already a parsed URI so just pass it along.
            if not isinstance(params.sdk_endpoint, str):
                return Endpoint(uri=params.sdk_endpoint)

            parsed = urlparse(params.sdk_endpoint)

            # This will end up getting wrapped in the client.
            if parsed.hostname is None:
                raise EndpointResolutionError(
                    f"Unable to parse hostname from provided URI: {params.sdk_endpoint}"
                )

            return Endpoint(
                uri=URI(
                    host=parsed.hostname,
                    path=parsed.path,
                    scheme=parsed.scheme,
                    query=parsed.query,
                    port=parsed.port,
                )
            )

        if params.region is not None:
            # TODO: use dns suffix determined from partition metadata
            dns_suffix = "amazonaws.com"
            hostname = f"{self._endpoint_prefix}.{params.region}.{dns_suffix}"

            return Endpoint(uri=URI(host=hostname))

        raise EndpointResolutionError(
            "Unable to resolve endpoint - either endpoint_url or region are required."
        )
