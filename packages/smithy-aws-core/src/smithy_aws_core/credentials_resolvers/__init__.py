#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from .environment import EnvironmentCredentialsResolver
from .static import StaticCredentialsResolver

__all__ = ("EnvironmentCredentialsResolver", "StaticCredentialsResolver")
