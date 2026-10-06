#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_core.config.exceptions import ConfigError, ConfigValidationError

__all__ = [
    "ConfigError",
    "ConfigParseError",
    "ConfigValidationError",
    "ProfileNotFoundError",
]


class ConfigParseError(ConfigError):
    """Raised when a config file cannot be parsed due to invalid syntax."""


class ProfileNotFoundError(ConfigError):
    """Raised when an explicitly requested profile is not defined in the config files."""
