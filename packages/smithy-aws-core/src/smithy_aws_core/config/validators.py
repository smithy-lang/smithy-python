# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import re
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from smithy_core.interfaces.retries import RetryStrategy
from smithy_core.retries import RetryStrategyOptions

T = TypeVar("T")


def allow_none(validator: Callable[[Any, str | None], T]) -> Callable[..., T | None]:
    """Decorator that allows None values to pass through validators.

    If the value is None, returns None without calling the validator.
    Otherwise, calls the validator with the value.

    :param validator: The validation function to wrap

    :returns: Wrapped validator that allows None values
    """

    @wraps(validator)
    def wrapper(value: Any, source: str | None = None) -> T | None:
        if value is None:
            return None
        return validator(value, source)

    return wrapper


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


@allow_none
def validate_region(value: Any, source: str | None = None) -> str | None:
    """Validate AWS region format.

    Valid formats:
    - us-east-1, us-west-2, eu-west-1, etc.
    - Pattern: {partition}-{region}-{number}

    :param value: The region value to validate
    :param source: The config source that provided this value

    :returns: The validated region string, or None if value is None

    :raises ConfigValidationError: If the region format is invalid
    """
    if not isinstance(value, str):
        raise ConfigValidationError(
            "region",
            value,
            f"Region must be a string, got {type(value).__name__}",
            source,
        )

    # AWS region pattern: partition-region-number
    pattern = r"^[a-z]{2}-[a-z]+-\d+$"

    if not re.match(pattern, value):
        raise ConfigValidationError(
            "region",
            value,
            "Region must match pattern '{partition}-{region}-{number}' (e.g., 'us-west-2', 'eu-central-1')",
            source,
        )
    return value


@allow_none
def validate_retry_mode(value: Any, source: str | None = None) -> str | None:
    """Validate retry mode.

    Valid values: 'standard', 'simple'

    :param value: The retry mode value to validate
    :param source: The source that provided this value

    :returns: The validated retry mode string, or None if value is None

    :raises: ConfigValidationError: If the retry mode is invalid
    """
    if not isinstance(value, str):
        raise ConfigValidationError(
            "retry_mode",
            value,
            f"Retry mode must be a string, got {type(value).__name__}",
            source,
        )

    valid_modes = {"standard", "simple"}

    if value not in valid_modes:
        raise ConfigValidationError(
            "retry_mode",
            value,
            f"Retry mode must be one of {valid_modes}, got {value!r}",
            source,
        )

    return value


@allow_none
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
