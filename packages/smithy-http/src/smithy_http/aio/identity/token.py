#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver

from ...identity import TokenIdentity, TokenIdentityProperties
from ...identity.token import StaticTokenResolver

__all__ = [
    "AsyncStaticTokenResolver",
    "TokenIdentity",
    "TokenIdentityProperties",
]


class AsyncStaticTokenResolver(
    AsyncIdentityResolver[TokenIdentity, TokenIdentityProperties]
):
    """Resolves a bearer token from a fixed identity or request properties.

    The resolution is synchronous; this defers to the sync component without
    awaiting.
    """

    def __init__(self, identity: TokenIdentity | None = None) -> None:
        self._sync = StaticTokenResolver(identity)

    async def get_identity(
        self, *, properties: TokenIdentityProperties
    ) -> TokenIdentity:
        return self._sync.get_identity(properties=properties)
