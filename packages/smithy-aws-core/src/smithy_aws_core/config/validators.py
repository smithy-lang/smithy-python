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


def validate_host(host_name: Any, source: str | None = None) -> str:
    """Validate host name format.

    :param host_name: The value to validate
    :param source: The config source that provided this value

    :returns: The validated value

    :raises ConfigValidationError: If the value format is invalid
    """
    if not isinstance(host_name, str):
        raise ConfigValidationError(
            "host",
            host_name,
            f"Host must be a string, got {type(host_name).__name__}",
            source,
        )

    pattern = r"^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$"

    if not re.match(pattern, host_name):
        raise ConfigValidationError(
            "host",
            host_name,
            "Host doesn't match the pattern.",
            source,
        )
    return host_name


def validate_retry_mode(retry_mode: Any, source: str | None = None) -> str:
    """Validate retry mode.

    Valid values: 'standard', 'simple'

    :param retry_mode: The retry mode value to validate
    :param source: The source that provided this value

    :returns: The validated retry mode string

    :raises: ConfigValidationError: If the retry mode is invalid
    """
    if not isinstance(retry_mode, str):
        raise ConfigValidationError(
            "retry_mode",
            retry_mode,
            f"Retry mode must be a string, got {type(retry_mode).__name__}",
            source,
        )

    valid_modes = get_args(RetryStrategyType)

    if retry_mode not in valid_modes:
        raise ConfigValidationError(
            "retry_mode",
            retry_mode,
            f"Retry mode must be one of {valid_modes}, got {retry_mode}",
            source,
        )

    return retry_mode


def validate_max_attempts(max_attempts: str | int, source: str | None = None) -> int:
    """Validate and convert max_attempts to integer.

    :param max_attempts: The max attempts value (string or int)
    :param source: The source that provided this value

    :returns: The validated max_attempts as an integer

    :raises ConfigValidationError: If the value cannot be converted to an integer
    """
    try:
        return int(max_attempts)
    except (ValueError, TypeError):
        raise ConfigValidationError(
            "max_attempts",
            max_attempts,
            f"max_attempts must be a number, got {type(max_attempts).__name__}",
            source,
        )


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
