#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver

from ...identity.components import AWSCredentialsIdentity, AWSIdentityProperties
from ...identity.environment import EnvironmentCredentialsResolver

__all__ = ["AsyncEnvironmentCredentialsResolver"]


class AsyncEnvironmentCredentialsResolver(
    AsyncIdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
):
    """Resolves AWS Credentials from system environment variables.

    The resolution is synchronous; this defers to the sync component without
    awaiting.
    """

    def __init__(self):
        self._sync = EnvironmentCredentialsResolver()

    async def get_identity(
        self, *, properties: AWSIdentityProperties
    ) -> AWSCredentialsIdentity:
        return self._sync.get_identity(properties=properties)
