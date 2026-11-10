#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from aws_sdk_signers.interfaces.identity import AWSIdentityProperties
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver

from ...identity.components import AWSCredentialsIdentity
from .chain import AsyncIdentityChain
from .container import AsyncContainerCredentialsResolver
from .environment import AsyncEnvironmentCredentialsResolver
from .imds import AsyncIMDSCredentialsResolver
from .process import AsyncProcessCredentialsResolver
from .static import AsyncStaticCredentialsResolver

type AsyncAWSCredentialsResolver = AsyncIdentityResolver[
    AWSCredentialsIdentity, AWSIdentityProperties
]

__all__ = (
    "AsyncAWSCredentialsResolver",
    "AsyncContainerCredentialsResolver",
    "AsyncEnvironmentCredentialsResolver",
    "AsyncIMDSCredentialsResolver",
    "AsyncIdentityChain",
    "AsyncProcessCredentialsResolver",
    "AsyncStaticCredentialsResolver",
)
