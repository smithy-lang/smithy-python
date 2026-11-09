#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import os

from smithy_core.interfaces.identity import Identity

from ....business_metrics import AwsFeatureId
from ...components import AWSCredentialsIdentity
from ..ordering import Standard, StandardProvider
from ..provider import _ChainSetupBase  # pyright: ignore[reportPrivateUsage]

__all__ = ["EnvironmentCredentialsProvider"]

_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"  # noqa: S105


class EnvironmentCredentialsProvider:
    """Adds an environment resolver unless an explicit profile is selected."""

    feature_ids = (AwsFeatureId.CREDENTIALS_ENV_VARS,)
    """The features recorded when this provider's resolver returns credentials."""

    @property
    def name(self) -> str:
        """Return the canonical provider name."""
        return StandardProvider.ENVIRONMENT.canonical_name

    @property
    def ordering(self) -> Standard:
        """Return the provider's standard chain position."""
        return Standard(slot=StandardProvider.ENVIRONMENT)

    def setup(self, identity_type: type[Identity], setup: _ChainSetupBase) -> None:
        """Add an environment resolver when env credentials are configured."""
        if identity_type is not AWSCredentialsIdentity:
            return

        if setup.profile_name is not None:
            return

        if not os.getenv(_ACCESS_KEY_ID) or not os.getenv(_SECRET_ACCESS_KEY):
            return

        setup._add_terminal(setup._environment_resolver())  # pyright: ignore[reportPrivateUsage]
