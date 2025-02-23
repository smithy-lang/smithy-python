#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from urllib.parse import urlparse

from smithy_core import URI

from .. import interfaces as http_interfaces
from ..endpoints import Endpoint, StaticEndpointParams
from . import interfaces as http_aio_interfaces


class StaticEndpointResolver(
    http_aio_interfaces.EndpointResolver[StaticEndpointParams]
):
    """A basic endpoint resolver that forwards a static URI."""

    async def resolve_endpoint(
        self, params: StaticEndpointParams
    ) -> http_interfaces.Endpoint:
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
            uri=URI(
                host=parsed.hostname,
                path=parsed.path,
                scheme=parsed.scheme,
                query=parsed.query,
                port=parsed.port,
            )
        )
