# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os

from smithy_aws_core.config.source_info import SourceName


class EnvironmentSource:
    """Configuration from environment variables."""

    def __init__(self, prefix: str = "AWS_"):
        """Initialize the EnvironmentSource with environment variable prefix.

        :param prefix: Prefix for environment variables (default: 'AWS_')
        """
        self._prefix = prefix

    @property
    def name(self) -> str:
        """Returns the source name."""
        return SourceName.ENVIRONMENT

    def get(self, key: str) -> str | None:
        """Returns a configuration value from environment variables.

        The key is transformed to uppercase and prefixed (e.g., 'region' → 'AWS_REGION').

        :param key: The standard configuration key (e.g., 'region', 'retry_mode').

        :returns: The value from the environment variable (or empty string if set to empty),
              or None if the variable is not set.
        """
        env_var = f"{self._prefix}{key.upper()}"
        config_value = os.environ.get(env_var)
        if config_value is None:
            return None
        return config_value.strip()
