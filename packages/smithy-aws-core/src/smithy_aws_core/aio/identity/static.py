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
from ...identity.static import StaticCredentialsResolver

__all__ = ["AsyncStaticCredentialsResolver"]


class AsyncStaticCredentialsResolver(
    AsyncIdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]
):
    """Resolves static AWS credentials from a fixed identity or request properties.

    The resolution is synchronous; this defers to the sync component without
    awaiting.
    """

    def __init__(
        self,
        identity: AWSCredentialsIdentity | None = None,
        *,
        feature_ids: tuple[AwsFeatureId, ...] = (AwsFeatureId.CREDENTIALS_CODE,),
    ) -> None:
        """Initialize the resolver.

        :param identity: The credentials to return, if fixed.
        :param feature_ids: The features recorded for each call that uses the
            credentials. Defaults to ``CREDENTIALS_CODE``, for credentials provided in
            code. Pass ``()`` when another component, such as the credential chain,
            already records how the credentials were provided.
        """
        self._sync = StaticCredentialsResolver(identity)
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
