#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver

from ...identity.components import AWSCredentialsIdentity, AWSIdentityProperties
from ...identity.static import StaticCredentialsResolver

__all__ = ["AsyncStaticCredentialsResolver"]


class AsyncStaticCredentialsResolver(
    AsyncIdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
):
    """Resolves static AWS credentials from a fixed identity or request properties.

    The resolution is synchronous; this defers to the sync component without
    awaiting.
    """

    def __init__(self, identity: AWSCredentialsIdentity | None = None) -> None:
        self._sync = StaticCredentialsResolver(identity)

    async def get_identity(
        self, *, properties: AWSIdentityProperties
    ) -> AWSCredentialsIdentity:
        return self._sync.get_identity(properties=properties)
