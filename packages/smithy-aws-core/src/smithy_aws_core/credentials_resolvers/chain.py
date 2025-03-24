#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence

from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.exceptions import SmithyIdentityException
from smithy_core.interfaces.identity import IdentityProperties

from smithy_aws_core.credentials_resolvers.environment import (
    EnvironmentCredentialsSource,
)
from smithy_aws_core.credentials_resolvers.imds import IMDSCredentialsSource
from smithy_aws_core.credentials_resolvers.interfaces import (
    AwsCredentialsConfig,
    CredentialsSource,
)
from smithy_aws_core.identity import AWSCredentialsIdentity, AWSCredentialsResolver

_DEFAULT_SOURCES: Sequence[CredentialsSource] = (
    EnvironmentCredentialsSource(),
    IMDSCredentialsSource(),
)


class CredentialsResolverChain(
    IdentityResolver[AWSCredentialsIdentity, IdentityProperties]
):
    """Resolves AWS Credentials from system environment variables."""

    def __init__(
        self,
        *,
        config: AwsCredentialsConfig,
        sources: Sequence[CredentialsSource] = _DEFAULT_SOURCES,
    ):
        self._config = config
        self._sources: Sequence[CredentialsSource] = sources
        self._credentials_resolver: AWSCredentialsResolver | None = None

    async def get_identity(
        self, *, identity_properties: IdentityProperties
    ) -> AWSCredentialsIdentity:
        if self._credentials_resolver is not None:
            return await self._credentials_resolver.get_identity(
                identity_properties=identity_properties
            )

        for source in self._sources:
            if source.is_available(config=self._config):
                self._credentials_resolver = source.build_resolver(config=self._config)
                return await self._credentials_resolver.get_identity(
                    identity_properties=identity_properties
                )

        raise SmithyIdentityException(
            "None of the configured credentials sources were able to resolve credentials."
        )
