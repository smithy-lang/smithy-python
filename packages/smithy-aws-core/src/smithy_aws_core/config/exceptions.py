#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_core.exceptions import SmithyError


class ConfigError(SmithyError):
    """Raised when a config value cannot be constructed directly"""


class ConfigParseError(ConfigError):
    """Raised when a config file cannot be parsed due to invalid syntax."""


class ConfigValidationError(ConfigError):
    """Raised when a config value cannot be validated"""
