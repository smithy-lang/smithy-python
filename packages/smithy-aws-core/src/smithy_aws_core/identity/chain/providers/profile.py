#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.interfaces.identity import Identity

from ...components import AWSCredentialsIdentity
from ...static import StaticCredentialsResolver
from ..ordering import Standard, StandardProvider
from ..provider import ChainSetup

_ACCESS_KEY_ID = "aws_access_key_id"
_SECRET_ACCESS_KEY = "aws_secret_access_key"  # noqa: S105
_SESSION_TOKEN = "aws_session_token"  # noqa: S105
_ACCOUNT_ID = "aws_account_id"
_ROLE_ARN = "role_arn"


class ProfileSessionCredentialsProvider:
    """Adds a resolver for session credentials from the active profile."""

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        return StandardProvider.PROFILE_SESSION_KEYS.canonical_name

    @property
    def ordering(self) -> Standard:
        """Return the provider's standard chain position."""
        return Standard(slot=StandardProvider.PROFILE_SESSION_KEYS)

    async def setup(self, identity_type: type[Identity], setup: ChainSetup) -> None:
        """Add a resolver for complete session credentials from the active profile."""
        if identity_type is not AWSCredentialsIdentity:
            return

        config_file = setup.config_file
        profile_name = setup.profile_name
        if config_file is None or profile_name is None:
            return

        if config_file.get(profile_name, _ROLE_ARN) is not None:
            return

        access_key_id = config_file.get(profile_name, _ACCESS_KEY_ID)
        secret_access_key = config_file.get(profile_name, _SECRET_ACCESS_KEY)
        session_token = config_file.get(profile_name, _SESSION_TOKEN)
        if access_key_id is None or secret_access_key is None or session_token is None:
            return

        identity = AWSCredentialsIdentity(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
            account_id=config_file.get(profile_name, _ACCOUNT_ID),
        )
        setup.add_terminal_resolver(StaticCredentialsResolver(identity))


class ProfileStaticCredentialsProvider:
    """Adds a resolver for static credentials from the active profile."""

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        return StandardProvider.PROFILE_STATIC_KEYS.canonical_name

    @property
    def ordering(self) -> Standard:
        """Return the provider's standard chain position."""
        return Standard(slot=StandardProvider.PROFILE_STATIC_KEYS)

    async def setup(self, identity_type: type[Identity], setup: ChainSetup) -> None:
        """Add a resolver for complete static credentials from the active profile."""
        if identity_type is not AWSCredentialsIdentity:
            return

        config_file = setup.config_file
        profile_name = setup.profile_name
        if config_file is None or profile_name is None:
            return

        if config_file.get(profile_name, _ROLE_ARN) is not None:
            return

        access_key_id = config_file.get(profile_name, _ACCESS_KEY_ID)
        secret_access_key = config_file.get(profile_name, _SECRET_ACCESS_KEY)
        if access_key_id is None or secret_access_key is None:
            return

        identity = AWSCredentialsIdentity(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            account_id=config_file.get(profile_name, _ACCOUNT_ID),
        )
        setup.add_terminal_resolver(StaticCredentialsResolver(identity))
