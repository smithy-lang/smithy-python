#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

_DEFAULT_TIMEOUT = 2
_DEFAULT_RETRIES = 3


@dataclass
class ContainerCredentialsConfig:
    """Configuration for container credential retrieval operations."""

    timeout: int = _DEFAULT_TIMEOUT
    retries: int = _DEFAULT_RETRIES
