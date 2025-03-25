#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityError
from smithy_core.interfaces.identity import Identity


@dataclass(kw_only=True)
class APIKeyIdentity(Identity):
    """The identity for auth that uses an api key."""

    api_key: str
    """The API Key to add to requests."""

    expiration: datetime | None = None


class APIKeyIdentityProperties(TypedDict, total=False):
    api_key: str


class APIKeyIdentityResolver(
    IdentityResolver[APIKeyIdentity, APIKeyIdentityProperties]
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
