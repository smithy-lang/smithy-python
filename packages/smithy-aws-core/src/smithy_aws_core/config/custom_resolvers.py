# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import cast

from smithy_core.config.resolver import ConfigResolver
from smithy_core.retries import RetryStrategyOptions, RetryStrategyType

from smithy_aws_core.config.validators import validate_retry_mode


def resolve_retry_strategy(
    resolver: ConfigResolver,
) -> tuple[RetryStrategyOptions | None, str | None]:
    """Resolve retry strategy from multiple config keys.

    Resolves both retry_mode and max_attempts from sources and constructs
    a RetryStrategyOptions object. This allows the retry strategy to be
    configured from multiple sources. Example: retry_mode from config file and
    max_attempts from environment variables.

    :param resolver: The config resolver to use for resolution

    :returns: Tuple of (RetryStrategyOptions or None, source_name or None).
        Returns (None, None) if neither retry_mode nor max_attempts is set.

        For mixed sources, the source string includes both component sources:
        "retry_mode=environment, max_attempts=config_file"
    """
    # Get retry_mode
    retry_mode, mode_source = resolver.get("retry_mode")

    # Get max_attempts
    max_attempts, attempts_source = resolver.get("max_attempts")

    # If neither is set, return None
    if retry_mode is None and max_attempts is None:
        return (None, None)

    if retry_mode is not None:
        retry_mode = validate_retry_mode(retry_mode, mode_source)
        retry_mode = cast(RetryStrategyType, retry_mode)

    # Construct options with defaults
    options = RetryStrategyOptions(
        retry_mode=retry_mode or "standard",
        max_attempts=int(max_attempts) if max_attempts else None,
    )

    # Construct mixed source string showing where each component came from
    source = f"retry_mode={mode_source or 'unresolved'}, max_attempts={attempts_source or 'unresolved'}"

    return (options, source)
