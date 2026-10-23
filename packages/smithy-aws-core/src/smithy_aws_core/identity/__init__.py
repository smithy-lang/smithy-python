#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core.types import PropertyKey

# TODO(sync-api): The shipped public name smithy_aws_core.identity.EnvironmentCredentialsResolver
# TODO(sync-api): is the ASYNC resolver -- the async client pipeline awaits its get_identity, and
# TODO(sync-api): aws-sdk-python's hand-written integration harness imports it from this path and
# TODO(sync-api): passes it to an async client. The sync twin lives at .environment and is NOT
# TODO(sync-api): re-exported here to avoid shadowing that awaitable contract.
# TODO(sync-api): This re-export makes a non-aio module import aio, which the sync-renames design
# TODO(sync-api): forbids; it is the same pre-existing root->aio dependency the branch defers, not a
# TODO(sync-api): new one. Repoint this to the sync twin and drop the aio import once the SDK harness
# TODO(sync-api): imports an async-aware resolver from smithy_aws_core.aio.identity instead.
from ..aio.identity.environment import (
    AsyncEnvironmentCredentialsResolver as EnvironmentCredentialsResolver,
)
from .chain import IdentityChainError, UnclaimedSource
from .components import (
    AWSCredentialsIdentity,
    AWSCredentialsResolver,
    AWSIdentityConfig,
    AWSIdentityProperties,
)
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
