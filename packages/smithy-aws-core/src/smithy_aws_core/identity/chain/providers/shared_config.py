#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os
from typing import Any

from smithy_core.interfaces.identity import Identity
from smithy_core.program import Program

from ...components import AWSCredentialsIdentity
from ..ordering import Standard, StandardProvider
from ..provider import _ChainSetupBase  # pyright: ignore[reportPrivateUsage]

__all__ = ["SharedConfigProvider"]


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

    def setup(self, identity_type: type[Identity], setup: _ChainSetupBase) -> Any:
        """Load and select the active profile for AWS credentials."""
        return setup._run(self._setup(identity_type, setup))  # pyright: ignore[reportPrivateUsage]

    def _setup(
        self, identity_type: type[Identity], setup: _ChainSetupBase
    ) -> Program[None]:
        if identity_type is not AWSCredentialsIdentity:
            return

        config_file = setup.config_file
        if config_file is None:
            config_file = yield setup._load_config  # pyright: ignore[reportPrivateUsage]
            setup.set_config_file(config_file)

        profile_name = setup.profile_name or os.getenv("AWS_PROFILE") or "default"
        setup.set_profile_name(profile_name)
