# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from smithy_core.exceptions import SmithyError


class ConfigError(SmithyError):
    """Base error for client configuration failures."""


class ConfigValidationError(ConfigError):
    """Raised when a config value cannot be validated."""
