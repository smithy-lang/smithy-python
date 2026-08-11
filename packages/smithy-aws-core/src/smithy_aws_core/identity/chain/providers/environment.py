#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os

from smithy_core.interfaces.identity import Identity

from ....config import load_config
from ...components import AWSCredentialsIdentity
from ...environment import EnvironmentCredentialsResolver
from ..ordering import Standard, StandardProvider
from ..provider import ChainSetup

_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"  # noqa: S105
_ROLE_ARN = "role_arn"
_CREDENTIAL_SOURCE = "credential_source"


class EnvironmentCredentialsProvider:
    """Adds an environment resolver when credentials are configured in the environment."""

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        return StandardProvider.ENVIRONMENT.canonical_name

    @property
    def ordering(self) -> Standard:
        """Return the provider's standard chain position."""
        return Standard(slot=StandardProvider.ENVIRONMENT)

    async def setup(
        self,
        identity_type: type[Identity],
        setup: ChainSetup,
    ) -> None:
        """Add an environment resolver when env credentials are configured."""
        if identity_type is not AWSCredentialsIdentity:
            return

        if not os.getenv(_ACCESS_KEY_ID) or not os.getenv(_SECRET_ACCESS_KEY):
            return

        # Skip environment provider if a profile is explicitly provided and
        # that profile configures assume role credentials with 'Environment' as the
        # credential source
        profile_name = setup.profile_name
        if profile_name:
            config = setup.config_file or await load_config()
            role_arn = config.get(profile_name, _ROLE_ARN)
            credential_source = config.get(profile_name, _CREDENTIAL_SOURCE)
            if role_arn is not None and credential_source == "Environment":
                return

        setup.add_terminal_resolver(EnvironmentCredentialsResolver())
