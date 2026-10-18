# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import re
from collections.abc import Collection
from typing import get_args

from smithy_core.retries import RetryStrategyType

from .exceptions import ConfigValidationError, ProfileNotFoundError
from .types import ConfigSource

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

    Valid values: 'standard', 'adaptive'

    :param retry_mode: The retry mode value to validate
    :raises: ConfigValidationError: If the retry mode is invalid
    """
    # NOTE: RetryStrategyType includes 'simple' for direct config use, but it isn't a
    # valid string mode here. 'legacy' is intentionally rejected as a direct override
    # (it is not recommended and never will be). When 'legacy' comes from the
    # environment or a config file, resolve_retry_mode() warns and maps it to 'standard'.

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
    source: ConfigSource,
) -> None:
    """Validate that a requested profile exists in the config files.

    :param profile_name: The active profile name to check.
    :param available_profiles: Profile names defined in the config files.
    :param source: Where the profile name came from, used to format the error.
    :raises ProfileNotFoundError: If the profile is not defined.
    """
    if profile_name not in available_profiles:
        # Only OVERRIDE and ENV reach here; a DEFAULT profile is never validated.
        source_str = (
            "profile argument"
            if source is ConfigSource.OVERRIDE
            else "AWS_PROFILE environment variable"
        )
        raise ProfileNotFoundError(
            f"Profile {profile_name!r} from {source_str} was not found in config file."
        )


def validate_disable_request_compression(value: object) -> None:
    """Require an explicit boolean for the compression disable switch."""
    if not isinstance(value, bool):
        raise ConfigValidationError("disable_request_compression must be a boolean")


def validate_request_min_compression_size_bytes(value: object) -> None:
    """Validate the standard inclusive compression threshold range."""
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 10485760
    ):
        raise ConfigValidationError(
            "request_min_compression_size_bytes must be an integer between 0 and 10485760"
        )


def validate_request_compression_encoding(value: object) -> None:
    """Only the gzip codec is currently modeled by Smithy."""
    if value not in (None, "gzip"):
        raise ConfigValidationError(
            "request_compression_encoding must be None or 'gzip'"
        )
