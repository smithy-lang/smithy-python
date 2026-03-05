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


def validate_region(region: str | None, source: str | None = None) -> str:
    """Validate region name format.

    :param region: The value to validate
    :param source: The config source that provided this value

    :returns: The validated value

    :raises ConfigValidationError: If the value format is invalid
    """
    if region is None:
        raise ConfigValidationError(
            "region",
            region,
            "region not found. It is required and must be explicitly set.",
            source,
        )

    pattern = r"^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{1,63}(?<!-)$"

    if not re.match(pattern, region):
        raise ConfigValidationError(
            "region",
            region,
            "region doesn't match the pattern.",
            source,
        )
    return region


def validate_retry_mode(retry_mode: str, source: str | None = None) -> str:
    """Validate retry mode.

    Valid values: 'standard'

    :param retry_mode: The retry mode value to validate
    :param source: The source that provided this value

    :returns: The validated retry mode string

    :raises: ConfigValidationError: If the retry mode is invalid
    """
    # TODO: Remove this block once 'simple' is removed from RetryStrategyType
    # RetryStrategyType currently supports 'standard' and 'simple' modes. Since 'simple'
    # will be deprecated soon, we're restricting config to only support 'standard' for now.
    # This code block will be removed once 'simple' is deprecated and 'adaptive' mode is added.
    all_modes = list(get_args(RetryStrategyType))
    if "simple" in all_modes:
        all_modes.remove("simple")
    valid_modes = tuple(all_modes)

    if retry_mode not in valid_modes:
        raise ConfigValidationError(
            "retry_mode",
            retry_mode,
            f"retry_mode must be one of {valid_modes}, got {retry_mode}",
            source,
        )

    return retry_mode


def validate_max_attempts(max_attempts: str | int, source: str | None = None) -> int:
    """Validate and convert max_attempts to integer.

    :param max_attempts: The max attempts value (string or int)
    :param source: The source that provided this value

    :returns: The validated max_attempts as an integer

    :raises ConfigValidationError: If the value is less than 1 or cannot be converted to an integer
    """
    try:
        max_attempts = int(max_attempts)
    except (ValueError, TypeError):
        raise ConfigValidationError(
            "max_attempts",
            max_attempts,
            f"max_attempts must be a number, got {type(max_attempts).__name__}",
            source,
        )

    if max_attempts < 1:
        raise ConfigValidationError(
            "max_attempts",
            max_attempts,
            f"max_attempts must be a positive integer, got {max_attempts}",
            source,
        )

    return max_attempts


def validate_retry_strategy(
    value: Any, source: str | None = None
) -> RetryStrategy | RetryStrategyOptions:
    """Validate retry strategy configuration.

    :param value: The retry strategy value to validate
    :param source: The source that provided this value

    :returns: The validated retry strategy (RetryStrategy or RetryStrategyOptions)

    :raises: ConfigValidationError: If the value is not a valid retry strategy type
    """

    if isinstance(value, RetryStrategy | RetryStrategyOptions):
        return value

    raise ConfigValidationError(
        "retry_strategy",
        value,
        f"retry_strategy must be RetryStrategy or RetryStrategyOptions, got {type(value).__name__}",
        source,
    )
