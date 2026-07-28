# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import re
from collections.abc import Collection
from typing import get_args

from smithy_core.retries import RetryStrategyType

from .exceptions import ConfigValidationError, ProfileNotFoundError

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


def validate_retry_mode(retry_mode: str):
    """Validate retry mode.

    Valid values: 'standard'

    :param retry_mode: The retry mode value to validate
    :raises: ConfigValidationError: If the retry mode is invalid
    """
    # NOTE: RetryStrategyType includes 'simple' for direct config use, but the only valid
    # string mode accepted here is 'standard'. 'adaptive' and 'legacy' are intentionally
    # rejected as direct overrides ('adaptive' support may be added later; 'legacy' is not
    # recommended and never will be). When 'adaptive' or 'legacy' come from the environment
    # or a config file, resolve_retry_mode() warns and maps them to 'standard'.

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
    max_attempts: object,
):
    """Validate max_attempts

    :param max_attempts: The max attempts value.

    :raises ConfigValidationError: If the value is not an integer or is less than 1.
    """
    if max_attempts is None:
        return

    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool):
        raise ConfigValidationError(
            f"max_attempts must be an integer, got {type(max_attempts).__name__}",
        )

    if max_attempts < 1:
        raise ConfigValidationError(
            f"max_attempts must be a positive integer, got {max_attempts}",
        )


def validate_profile(
    profile_name: str,
    available_profiles: Collection[str],
    origin: str,
) -> None:
    """Validate that a requested profile exists in the config files.

    :param profile_name: The active profile name to check.
    :param available_profiles: Profile names defined in the config files.
    :param origin: Where the profile name came from, used in the error message.
    :raises ProfileNotFoundError: If the profile is not defined.
    """
    if profile_name not in available_profiles:
        raise ProfileNotFoundError(
            f"Profile {profile_name!r} (from {origin}) not found in config file."
        )
