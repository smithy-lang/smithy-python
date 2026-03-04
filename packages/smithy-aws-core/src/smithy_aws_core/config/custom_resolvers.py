# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from smithy_core.config.resolver import ConfigResolver
from smithy_core.retries import RetryStrategyOptions

from smithy_aws_core.config.validators import validate_max_attempts, validate_retry_mode


def resolve_retry_strategy(
    resolver: ConfigResolver,
) -> tuple[RetryStrategyOptions | None, str | None]:
    """Resolve retry strategy from multiple config keys.

    Resolves both retry_mode and max_attempts from sources and constructs
    a RetryStrategyOptions object. This allows the retry strategy to be
    configured from multiple sources. Example: retry_mode from config file and
    max_attempts from environment variables.

    :param resolver: The config resolver to use for resolution

    :returns: Tuple of (RetryStrategyOptions, source_name) if both retry_mode and max_attempts
        are resolved. Returns (None, None) if both values are missing.

        For mixed sources, the source name includes both component sources:
        "retry_mode=environment, max_attempts=config_file"
    """

    retry_mode, mode_source = resolver.get("retry_mode")

    max_attempts, attempts_source = resolver.get("max_attempts")

    if retry_mode is None and max_attempts is None:
        return None, None

    if retry_mode is not None:
        retry_mode = validate_retry_mode(retry_mode, mode_source)

    if max_attempts is not None:
        max_attempts = validate_max_attempts(max_attempts, attempts_source)

    options = RetryStrategyOptions(
        retry_mode=retry_mode or "standard",  # type: ignore
        max_attempts=max_attempts or 3,
    )

    # Construct mixed source string showing where each component came from
    source = f"retry_mode={mode_source or 'default'}, max_attempts={attempts_source or 'default'}"

    return (options, source)
