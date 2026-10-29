#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os
from typing import Any

from smithy_core._program import Program, run_program
from smithy_core.interfaces.identity import Identity

from ....config.context import load_config
from ...components import AWSCredentialsIdentity
from ..ordering import Standard, StandardProvider
from ..provider import ChainSetup

__all__ = ["SharedConfigProvider"]


class _SharedConfigProviderBase:
    """Loads and selects the active AWS profile for downstream providers."""

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        return StandardProvider.SHARED_CONFIG.canonical_name

    @property
    def ordering(self) -> Standard:
        """Return the provider's standard chain position."""
        return Standard(slot=StandardProvider.SHARED_CONFIG)

    def _load_config(self) -> Any:
        raise NotImplementedError

    def _setup(self, identity_type: type[Identity], setup: Any) -> Program[None]:
        if identity_type is not AWSCredentialsIdentity:
            return

        config_file = setup.config_file
        if config_file is None:
            config_file = yield self._load_config
            setup.set_config_file(config_file)

        profile_name = setup.profile_name or os.getenv("AWS_PROFILE") or "default"
        setup.set_profile_name(profile_name)


class SharedConfigProvider(_SharedConfigProviderBase):
    """Loads and selects the active AWS profile for downstream providers."""

    def _load_config(self) -> Any:
        return load_config()

    def setup(self, identity_type: type[Identity], setup: ChainSetup) -> None:
        """Load and select the active profile for AWS credentials."""
        run_program(self._setup(identity_type, setup))
