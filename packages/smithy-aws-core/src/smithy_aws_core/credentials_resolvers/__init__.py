#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from .environment_credentials_resolver import EnvironmentCredentialsResolver
from .static_credentials_resolver import StaticCredentialsResolver

__all__ = ("EnvironmentCredentialsResolver", "StaticCredentialsResolver")
