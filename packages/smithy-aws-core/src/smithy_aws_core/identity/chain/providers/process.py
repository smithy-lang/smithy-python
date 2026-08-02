#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import shlex

from smithy_core.interfaces.identity import Identity

from ...components import AWSCredentialsIdentity
from ...process import ProcessCredentialsResolver
from ..ordering import Standard, StandardProvider
from ..provider import ChainSetup

_CREDENTIAL_PROCESS = "credential_process"


class ProfileProcessCredentialsProvider:
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

        setup.add_terminal_resolver(ProcessCredentialsResolver(shlex.split(command)))
