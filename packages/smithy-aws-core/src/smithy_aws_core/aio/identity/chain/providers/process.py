#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.interfaces.identity import Identity

from .....identity.chain.ordering import Standard, StandardProvider
from .....identity.chain.providers.process import (
    _split_process_command,  # type: ignore[reportPrivateUsage]
)
from .....identity.components import AWSCredentialsIdentity
from ....identity.process import ProcessCredentialsResolver
from ..provider import ChainSetup

_CREDENTIAL_PROCESS = "credential_process"
_ACCOUNT_ID = "aws_account_id"


class ProfileCredentialProcessProvider:
    """Adds a process credential resolver configured by the active profile."""

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        return StandardProvider.PROFILE_CREDENTIAL_PROCESS.canonical_name

    @property
    def ordering(self) -> Standard:
        """Return the provider's standard chain position."""
        return Standard(slot=StandardProvider.PROFILE_CREDENTIAL_PROCESS)

    async def setup(self, identity_type: type[Identity], setup: ChainSetup) -> None:
        """Add a resolver when the active profile configures a credential process."""
        if identity_type is not AWSCredentialsIdentity:
            return

        config_file = setup.config_file
        profile_name = setup.profile_name
        if config_file is None or profile_name is None:
            return

        command = config_file.get(profile_name, _CREDENTIAL_PROCESS)
        if not command:
            return

        # The process output's AccountId takes precedence; the profile's
        # aws_account_id is only used as a fallback.
        setup.add_terminal_resolver(
            ProcessCredentialsResolver(
                _split_process_command(command),
                account_id=config_file.get(profile_name, _ACCOUNT_ID),
            )
        )
