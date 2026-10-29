#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.interfaces.identity import Identity

from .....identity.chain.providers.profile import (
    _ProfileSessionCredentialsProviderBase,  # pyright: ignore[reportPrivateUsage]
    _ProfileStaticCredentialsProviderBase,  # pyright: ignore[reportPrivateUsage]
)
from .....identity.components import AWSCredentialsIdentity
from ...static import AsyncStaticCredentialsResolver
from ..provider import ChainSetup

__all__ = [
    "AsyncProfileSessionCredentialsProvider",
    "AsyncProfileStaticCredentialsProvider",
]


class AsyncProfileSessionCredentialsProvider(_ProfileSessionCredentialsProviderBase):
    """Adds a resolver for session credentials from the active profile."""

    def _new_resolver(
        self, identity: AWSCredentialsIdentity
    ) -> AsyncStaticCredentialsResolver:
        return AsyncStaticCredentialsResolver(identity)

    async def setup(self, identity_type: type[Identity], setup: ChainSetup) -> None:
        """Add a resolver for complete session credentials from the active profile."""
        self._setup(identity_type, setup)


class AsyncProfileStaticCredentialsProvider(_ProfileStaticCredentialsProviderBase):
    """Adds a resolver for static credentials from the active profile."""

    def _new_resolver(
        self, identity: AWSCredentialsIdentity
    ) -> AsyncStaticCredentialsResolver:
        return AsyncStaticCredentialsResolver(identity)

    async def setup(self, identity_type: type[Identity], setup: ChainSetup) -> None:
        """Add a resolver for complete static credentials from the active profile."""
        self._setup(identity_type, setup)
