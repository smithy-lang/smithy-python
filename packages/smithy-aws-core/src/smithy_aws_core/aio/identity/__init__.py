#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from .chain import IdentityChain
from .chain.providers.environment import EnvironmentCredentialsProvider
from .chain.providers.process import ProfileCredentialProcessProvider
from .chain.providers.profile import (
    ProfileSessionCredentialsProvider,
    ProfileStaticCredentialsProvider,
)
from .chain.providers.shared_config import SharedConfigProvider
from .container import ContainerCredentialsResolver
from .environment import EnvironmentCredentialsResolver
from .imds import IMDSCredentialsResolver
from .process import ProcessCredentialsResolver
from .static import AsyncStaticCredentialsResolver

__all__ = (
    "AsyncStaticCredentialsResolver",
    "ContainerCredentialsResolver",
    "EnvironmentCredentialsProvider",
    "EnvironmentCredentialsResolver",
    "IMDSCredentialsResolver",
    "IdentityChain",
    "ProcessCredentialsResolver",
    "ProfileCredentialProcessProvider",
    "ProfileSessionCredentialsProvider",
    "ProfileStaticCredentialsProvider",
    "SharedConfigProvider",
)
