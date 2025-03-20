#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from .environment import EnvironmentCredentialsResolver
from .static import StaticCredentialsResolver
from .imds import IMDSCredentialsResolver

__all__ = (
    "EnvironmentCredentialsResolver",
    "StaticCredentialsResolver",
    "IMDSCredentialsResolver",
)
