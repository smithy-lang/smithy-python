#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.aio.identity import ChainedIdentityResolver
from smithy_http.aio.interfaces import HTTPClient

from .components import (
    AWSCredentialsIdentity,
    AWSCredentialsResolver,
    AWSIdentityProperties,
)
from .environment import EnvironmentCredentialsResolver
from .imds import IMDSCredentialsResolver
from .static import StaticCredentialsResolver


def create_default_chain(http_client: HTTPClient) -> AWSCredentialsResolver:
    """Creates the default AWS credential provider chain."""
    return ChainedIdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties](
        resolvers=(
            StaticCredentialsResolver(),
            EnvironmentCredentialsResolver(),
            IMDSCredentialsResolver(http_client=http_client),
        )
    )
