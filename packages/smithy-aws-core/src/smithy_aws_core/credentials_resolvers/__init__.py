#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from .container import ContainerCredentialResolver
from .environment import EnvironmentCredentialsResolver
from .imds import IMDSCredentialsResolver
from .static import StaticCredentialsResolver

__all__ = (
    "ContainerCredentialResolver",
    "EnvironmentCredentialsResolver",
    "IMDSCredentialsResolver",
    "StaticCredentialsResolver",
)
