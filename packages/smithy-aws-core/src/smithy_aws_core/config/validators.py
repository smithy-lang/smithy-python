# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import re
from typing import get_args

from smithy_core.exceptions import ConfigValidationError
from smithy_core.retries import RetryStrategyOptions, RetryStrategyType

_REGION_PATTERN = re.compile(r"^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{1,63}(?<!-)$")


def validate_region(value: object) -> None:
    """Validate that region is a non-empty string matching AWS region format.

    Region is required and must be explicitly set via env var, config file,
    or override.

    :param value: The resolved region value.
    :raises ConfigValidationError: If the value is None or doesn't match the pattern.
    """
    if value is None:
        raise ConfigValidationError(
            "Invalid value for 'region': None. Region is required and must be set."
        )
    if not isinstance(value, str) or not _REGION_PATTERN.match(value):
        raise ConfigValidationError(
            f"Invalid value for 'region': {value!r}. "
            "Must be a valid AWS region identifier."
        )


def validate_retry_strategy_options(value: object) -> None:
    """Validate that retry_strategy_options is a RetryStrategyOptions instance.

    :param value: The resolved retry strategy options value.
    :raises ConfigValidationError: If the value is not a RetryStrategyOptions instance.
    """
    if not isinstance(value, RetryStrategyOptions):
        raise ConfigValidationError(
            f"Invalid value for 'retry_strategy_options': {value!r}. "
            f"Must be RetryStrategyOptions, got {type(value).__name__}."
        )


def validate_retry_mode(retry_mode: str):
    """Validate retry mode.

    Valid values: 'standard'

    :param retry_mode: The retry mode value to validate
    :raises: ConfigValidationError: If the retry mode is invalid
    """

    all_modes = list(get_args(RetryStrategyType))
    if "simple" in all_modes:
        all_modes.remove("simple")
    valid_modes = tuple(all_modes)

    if retry_mode not in valid_modes:
        raise ConfigValidationError(
            f"Invalid value for 'retry_mode': {retry_mode!r}. "
            f"Must be one of {valid_modes}."
        )


def validate_max_attempts(
    max_attempts: str | int,
):
    """Validate max_attempts

    :param max_attempts: The max attempts value (string or int)

    :raises ConfigValidationError: If the value is less than 1 or cannot be converted to an integer
    """
    try:
        max_attempts = int(max_attempts)
    except (ValueError, TypeError):
        raise ConfigValidationError(
            f"max_attempts must be a number, got {type(max_attempts).__name__}",
        )

    if max_attempts < 1:
        raise ConfigValidationError(
            f"max_attempts must be a positive integer, got {max_attempts}",
        )
