#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os

from smithy_core.interfaces.identity import Identity

from ...components import AWSCredentialsIdentity
from ...environment import EnvironmentCredentialsResolver
from ..ordering import Standard, StandardProvider
from ..provider import ChainSetup

_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"  # noqa: S105


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

        setup.add_terminal_resolver(EnvironmentCredentialsResolver())
