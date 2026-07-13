# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import re

from smithy_aws_core.config.exceptions import ConfigError
from smithy_core.retries import RetryStrategyOptions

_REGION_PATTERN = re.compile(r"^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{1,63}(?<!-)$")


def validate_region(value: object) -> None:
    """Validate that region is a non-empty string matching AWS region format.

    Region is required and must be explicitly set via env var, config file,
    or override.

    :param value: The resolved region value.
    :raises ConfigError: If the value is None or doesn't match the pattern.
    """
    if value is None:
        raise ConfigError(
            "Invalid value for 'region': None. Region is required and must be set."
        )
    if not isinstance(value, str) or not _REGION_PATTERN.match(value):
        raise ConfigError(
            f"Invalid value for 'region': {value!r}. "
            "Must be a valid AWS region identifier."
        )


def validate_retry_strategy_options(value: object) -> None:
    """Validate that retry_strategy_options is a RetryStrategyOptions instance.

    :param value: The resolved retry strategy options value.
    :raises ConfigError: If the value is not a RetryStrategyOptions instance.
    """
    if not isinstance(value, RetryStrategyOptions):
        raise ConfigError(
            f"Invalid value for 'retry_strategy_options': {value!r}. "
            f"Must be RetryStrategyOptions, got {type(value).__name__}."
        )
