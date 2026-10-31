#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.types import PropertyKey

from .chain import IdentityChainError, UnclaimedSource
from .components import (
    AWSCredentialsIdentity,
    AWSCredentialsResolver,
    AWSIdentityConfig,
    AWSIdentityProperties,
)
from .environment import EnvironmentCredentialsResolver
from .static import StaticCredentialsResolver

__all__ = (
    "AWSCredentialsIdentity",
    "AWSCredentialsResolver",
    "AWSIdentityProperties",
    "EnvironmentCredentialsResolver",
    "IdentityChainError",
    "StaticCredentialsResolver",
    "UnclaimedSource",
)

AWS_IDENTITY_CONFIG = PropertyKey(key="config", value_type=AWSIdentityConfig)
