#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os

from smithy_core.interfaces.identity import Identity

from ....config import load_config
from ...components import AWSCredentialsIdentity
from ..ordering import Standard, StandardProvider
from ..provider import ChainSetup


class SharedConfigProvider:
    """Loads and selects the active AWS profile for downstream providers."""

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        return StandardProvider.SHARED_CONFIG.canonical_name

    @property
    def ordering(self) -> Standard:
        """Return the provider's standard chain position."""
        return Standard(slot=StandardProvider.SHARED_CONFIG)

    async def setup(self, identity_type: type[Identity], setup: ChainSetup) -> None:
        """Load and select the active profile for AWS credentials."""
        if identity_type is not AWSCredentialsIdentity:
            return

        config_file = setup.config_file
        if config_file is None:
            config_file = await load_config()
            setup.set_config_file(config_file)

        profile_name = setup.profile_name or os.getenv("AWS_PROFILE") or "default"
        setup.set_profile_name(profile_name)
