#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.types import PropertyKey

from .chain import IdentityChain, IdentityChainError, UnclaimedSource
from .chain.providers.environment import EnvironmentCredentialsProvider
from .chain.providers.profile import (
    ProfileSessionCredentialsProvider,
    ProfileStaticCredentialsProvider,
)
from .chain.providers.shared_config import SharedConfigProvider
from .components import (
    AWSCredentialsIdentity,
    AWSCredentialsResolver,
    AWSIdentityConfig,
    AWSIdentityProperties,
)
from .container import ContainerCredentialsResolver
from .environment import EnvironmentCredentialsResolver
from .imds import IMDSCredentialsResolver
from .static import StaticCredentialsResolver

__all__ = (
    "AWSCredentialsIdentity",
    "AWSCredentialsResolver",
    "AWSIdentityProperties",
    "ContainerCredentialsResolver",
    "EnvironmentCredentialsProvider",
    "EnvironmentCredentialsResolver",
    "IMDSCredentialsResolver",
    "IdentityChain",
    "IdentityChainError",
    "ProfileSessionCredentialsProvider",
    "ProfileStaticCredentialsProvider",
    "SharedConfigProvider",
    "StaticCredentialsResolver",
    "UnclaimedSource",
)

AWS_IDENTITY_CONFIG = PropertyKey(key="config", value_type=AWSIdentityConfig)
