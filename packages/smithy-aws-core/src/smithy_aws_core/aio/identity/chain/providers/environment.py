#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.interfaces.identity import Identity

from .....identity.chain.providers.environment import (
    _EnvironmentCredentialsProviderBase,  # pyright: ignore[reportPrivateUsage]
)
from ...environment import AsyncEnvironmentCredentialsResolver
from ..provider import ChainSetup

__all__ = ["AsyncEnvironmentCredentialsProvider"]


class AsyncEnvironmentCredentialsProvider(_EnvironmentCredentialsProviderBase):
    """Adds an environment resolver unless an explicit profile is selected."""

    def _new_resolver(self) -> AsyncEnvironmentCredentialsResolver:
        return AsyncEnvironmentCredentialsResolver()

    async def setup(
        self,
        identity_type: type[Identity],
        setup: ChainSetup,
    ) -> None:
        """Add an environment resolver when env credentials are configured."""
        self._setup(identity_type, setup)
