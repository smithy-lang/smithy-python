#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver

from ...identity import (
    APIKeyIdentity,
    APIKeyIdentityProperties,
    APIKeyIdentityResolver,
)

__all__ = [
    "APIKeyIdentity",
    "APIKeyIdentityProperties",
    "AsyncAPIKeyIdentityResolver",
]

_SYNC_RESOLVER = APIKeyIdentityResolver()


class AsyncAPIKeyIdentityResolver(
    AsyncIdentityResolver[APIKeyIdentity, APIKeyIdentityProperties]
):
    """Loads the API key identity from the configuration."""

    async def get_identity(
        self, *, properties: APIKeyIdentityProperties
    ) -> APIKeyIdentity:
        return _SYNC_RESOLVER.get_identity(properties=properties)
