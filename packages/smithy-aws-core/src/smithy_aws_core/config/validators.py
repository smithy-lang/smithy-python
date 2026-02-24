# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import re
from typing import Any, get_args

from smithy_core.interfaces.retries import RetryStrategy
from smithy_core.retries import RetryStrategyOptions, RetryStrategyType


class ConfigValidationError(ValueError):
    """Raised when a configuration value fails validation."""

    def __init__(self, key: str, value: Any, reason: str, source: str | None = None):
        self.key = key
        self.value = value
        self.reason = reason
        self.source = source

        msg = f"Invalid value for '{key}': {value!r}. {reason}"
        if source:
            msg += f" (from source: {source})"
        super().__init__(msg)


def validate_region(region_name: Any, source: str | None = None) -> str | None:
    """Validate AWS region format.

    Valid formats:
    - us-east-1, us-west-2, eu-west-1, etc.
    - Pattern: {partition}-{region}-{number}

    :param region_name: The region value to validate
    :param source: The config source that provided this value

    :returns: The validated region string, or None if value is None

    :raises ConfigValidationError: If the region format is invalid
    """
    if not isinstance(region_name, str):
        raise ConfigValidationError(
            "region",
            region_name,
            f"Region must be a string, got {type(region_name).__name__}",
            source,
        )

    pattern = r"^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$"

    if not re.match(pattern, region_name):
        raise ConfigValidationError(
            "region",
            region_name,
            "Region doesn't match the pattern (e.g., 'us-west-2', 'eu-central-1')",
            source,
        )
    return region_name


def validate_retry_mode(retry_mode: Any, source: str | None = None) -> str | None:
    """Validate retry mode.

    Valid values: 'standard', 'simple'

    :param retry_mode: The retry mode value to validate
    :param source: The source that provided this value

    :returns: The validated retry mode string, or None if value is None

    :raises: ConfigValidationError: If the retry mode is invalid
    """
    if not isinstance(retry_mode, str):
        raise ConfigValidationError(
            "retry_mode",
            retry_mode,
            f"Retry mode must be a string, got {type(retry_mode).__name__}",
            source,
        )

    valid_modes = set(get_args(RetryStrategyType))

    if retry_mode not in valid_modes:
        raise ConfigValidationError(
            "retry_mode",
            retry_mode,
            f"Retry mode must be one of {RetryStrategyType}, got {retry_mode}",
            source,
        )

    return retry_mode


def validate_retry_strategy(value: Any, source: str | None = None) -> Any:
    """Validate retry strategy configuration.

    :param value: The retry strategy value to validate (None is allowed and returns None)
    :param source: The source that provided this value (for error messages)

    :returns: The validated retry strategy (RetryStrategy or RetryStrategyOptions)

    :raises: ConfigValidationError: If the value is not a valid retry strategy type
    """
    # Allow RetryStrategy instances
    if isinstance(value, RetryStrategy):
        return value

    # Allow RetryStrategyOptions instances
    if isinstance(value, RetryStrategyOptions):
        return value

    raise ConfigValidationError(
        "retry_strategy",
        value,
        f"Retry strategy must be a RetryStrategy or RetryStrategyOptions got {type(value).__name__}",
        source,
    )
