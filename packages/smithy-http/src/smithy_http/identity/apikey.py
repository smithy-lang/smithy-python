#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces.identity import IdentityResolver

from . import APIKeyIdentity, APIKeyIdentityProperties

__all__ = [
    "APIKeyIdentity",
    "APIKeyIdentityProperties",
    "APIKeyIdentityResolver",
]


class APIKeyIdentityResolver(
    IdentityResolver[APIKeyIdentity, APIKeyIdentityProperties]
):
    """Loads the API key identity from the configuration."""

    def get_identity(self, *, properties: APIKeyIdentityProperties) -> APIKeyIdentity:
        if (api_key := properties.get("api_key")) is not None:
            return APIKeyIdentity(api_key=api_key)
        raise SmithyIdentityError(
            "Attempted to use API key auth, but api_key was not set on the config."
        )
