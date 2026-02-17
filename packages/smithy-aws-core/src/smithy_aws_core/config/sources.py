# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os
from typing import Any


class EnvironmentSource:
    """Configuration from environment variables."""

    SOURCE = "environment"

    def __init__(self, prefix: str = "AWS_"):
        """Initialize the EnvironmentSource with environment variable prefix.

        :param prefix: Prefix for environment variables (default: 'AWS_')
        """
        self._prefix = prefix

    @property
    def name(self) -> str:
        """Returns the source name."""
        return self.SOURCE

    def get(self, key: str) -> Any | None:
        """Returns a configuration value from environment variables.

        :param key: The standard configuration key (e.g., 'region', 'retry_mode').

        :returns: The value from the corresponding environment variable, or None if not set or empty.
        """
        env_var = f"{self._prefix}{key.upper()}"
        config_value = os.environ.get(env_var)
        if config_value is None:
            return None
        return config_value.strip()
