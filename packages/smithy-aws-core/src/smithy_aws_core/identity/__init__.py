#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.types import PropertyKey

from .components import (
    AWSCredentialsIdentity,
    AWSCredentialsResolver,
    AWSIdentityConfig,
    AWSIdentityProperties,
)
from .container import ContainerCredentialsResolver
from .environment import EnvironmentCredentialsResolver
from .imds import IMDSCredentialsResolver
from .process import ProcessCredentialsConfig, ProcessCredentialsResolver
from .static import StaticCredentialsResolver

__all__ = (
    "AWSCredentialsIdentity",
    "AWSCredentialsResolver",
    "AWSIdentityProperties",
    "ContainerCredentialsResolver",
    "EnvironmentCredentialsResolver",
    "IMDSCredentialsResolver",
    "ProcessCredentialsConfig",
    "ProcessCredentialsResolver",
    "StaticCredentialsResolver",
)

AWS_IDENTITY_CONFIG = PropertyKey(key="config", value_type=AWSIdentityConfig)
