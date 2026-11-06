#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver

from ...business_metrics import AwsFeatureId, add_feature_id
from ...identity.components import AWSCredentialsIdentity, AWSIdentityProperties
from ...identity.environment import EnvironmentCredentialsResolver

__all__ = ["AsyncEnvironmentCredentialsResolver"]


class AsyncEnvironmentCredentialsResolver(
    AsyncIdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
):
    """Resolves AWS Credentials from system environment variables.

    The resolution is synchronous; this defers to the sync component without
    awaiting.
    """

    _FEATURE_ID = AwsFeatureId.CREDENTIALS_ENV_VARS
    """Recorded when used directly; in the credential chain, the provider's are used."""

    def __init__(self):
        self._sync = EnvironmentCredentialsResolver()

    async def get_identity(
        self, *, properties: AWSIdentityProperties
    ) -> AWSCredentialsIdentity:
        identity = self._sync.get_identity(properties=properties)
        features = properties.get("_feature_ids")
        if features is not None:
            add_feature_id(features, self._FEATURE_ID)
        return identity
