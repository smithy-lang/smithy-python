#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.interfaces import TypedProperties

from ...business_metrics import (
    AwsFeatureId,
    normalize_feature_ids,
    register_feature_id,
)
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

    def __init__(
        self,
        *,
        feature_ids: tuple[AwsFeatureId, ...] = (AwsFeatureId.CREDENTIALS_ENV_VARS,),
    ) -> None:
        """Initialize the resolver.

        :param feature_ids: The features recorded for each call that uses the
            credentials. Defaults to ``CREDENTIALS_ENV_VARS``. Pass ``()`` when another
            component, such as the credential chain, already records them.
        """
        self._sync = EnvironmentCredentialsResolver()
        self._feature_ids = normalize_feature_ids(feature_ids)

    async def get_identity(
        self,
        *,
        properties: AWSIdentityProperties,
        context: TypedProperties | None = None,
    ) -> AWSCredentialsIdentity:
        identity = self._sync.get_identity(properties=properties, context=context)
        if context is not None:
            for feature_id in self._feature_ids:
                register_feature_id(context, feature_id)
        return identity
