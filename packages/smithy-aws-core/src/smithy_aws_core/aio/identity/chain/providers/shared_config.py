#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from typing import Any

from smithy_core.aio._program import run_program_async
from smithy_core.interfaces.identity import Identity

from .....identity.chain.providers.shared_config import (
    _SharedConfigProviderBase,  # pyright: ignore[reportPrivateUsage]
)
from ....config import load_config_async
from ..provider import ChainSetup

__all__ = ["AsyncSharedConfigProvider"]


class AsyncSharedConfigProvider(_SharedConfigProviderBase):
    """Loads and selects the active AWS profile for downstream providers."""

    def _load_config(self) -> Any:
        return load_config_async()

    async def setup(self, identity_type: type[Identity], setup: ChainSetup) -> None:
        """Load and select the active profile for AWS credentials."""
        await run_program_async(self._setup(identity_type, setup))
