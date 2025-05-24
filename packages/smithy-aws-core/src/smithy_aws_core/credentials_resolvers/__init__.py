#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from .chain import CredentialsResolverChain
from .environment import EnvironmentCredentialsResolver
from .imds import IMDSCredentialsResolver
from .static import StaticCredentialsResolver

__all__ = (
    "CredentialsResolverChain",
    "EnvironmentCredentialsResolver",
    "IMDSCredentialsResolver",
    "StaticCredentialsResolver",
)
