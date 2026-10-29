#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.interfaces.identity import Identity

from .....identity.chain.providers.process import (
    _ProfileCredentialProcessProviderBase,  # pyright: ignore[reportPrivateUsage]
)
from ....identity.process import AsyncProcessCredentialsResolver
from ..provider import ChainSetup


class AsyncProfileCredentialProcessProvider(_ProfileCredentialProcessProviderBase):
    """Adds a process credential resolver configured by the active profile."""

    def _new_resolver(
        self, command: list[str], account_id: str | None
    ) -> AsyncProcessCredentialsResolver:
        return AsyncProcessCredentialsResolver(command, account_id=account_id)

    async def setup(self, identity_type: type[Identity], setup: ChainSetup) -> None:
        """Add a resolver when the active profile configures a credential process."""
        self._setup(identity_type, setup)
