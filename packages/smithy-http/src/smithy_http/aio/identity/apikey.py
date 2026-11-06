#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.exceptions import SmithyIdentityError

from ...identity import APIKeyIdentity, APIKeyIdentityProperties

__all__ = [
    "APIKeyIdentity",
    "APIKeyIdentityProperties",
    "AsyncAPIKeyIdentityResolver",
]


class AsyncAPIKeyIdentityResolver(
    AsyncIdentityResolver[APIKeyIdentity, APIKeyIdentityProperties]
):
    """Loads the API key identity from the configuration."""

    async def get_identity(
        self, *, properties: APIKeyIdentityProperties
    ) -> APIKeyIdentity:
        if (api_key := properties.get("api_key")) is not None:
            return APIKeyIdentity(api_key=api_key)
        raise SmithyIdentityError(
            "Attempted to use API key auth, but api_key was not set on the config."
        )
