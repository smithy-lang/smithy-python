#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os
from typing import Any

from smithy_core.interfaces.identity import Identity
from smithy_core.program import Program

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
        """Load and select the active profile for every identity type.

        This step registers no resolvers; it only makes the shared config and the
        active profile name available to the profile-based providers that follow it,
        whatever identity type the chain resolves (for example ``TokenIdentity``
        chains read ``sso_session`` from the same profile).
        """
        return setup._run(self._setup(setup))  # pyright: ignore[reportPrivateUsage]

    def _setup(self, setup: _ChainSetupBase) -> Program[None]:
        config_file = setup.config_file
        if config_file is None:
            config_file = yield setup._load_config  # pyright: ignore[reportPrivateUsage]
            setup.set_config_file(config_file)

        profile_name = setup.profile_name or os.getenv("AWS_PROFILE") or "default"
        setup.set_profile_name(profile_name)
