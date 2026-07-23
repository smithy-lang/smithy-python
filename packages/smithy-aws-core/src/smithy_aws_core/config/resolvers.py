# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
from collections.abc import Sequence
from typing import Any

from smithy_core.exceptions import ConfigValidationError
from smithy_core.retries import RetryStrategyOptions

from smithy_aws_core.config.context import SharedConfigContext
from smithy_aws_core.config.types import UNSET, ConfigSource, Resolved
from smithy_aws_core.config.validators import validate_max_attempts, validate_retry_mode


async def _resolve_str(
    ctx: SharedConfigContext,
    *,
    env_vars: Sequence[str] = (),
    profile_keys: Sequence[str] = (),
) -> Resolved[str]:
    """Resolve a string value by checking providers in priority order.

    Priority: env vars (first match) > config file (profile keys, first match) > unresolved.

    :param ctx: The shared resolution context.
    :param env_vars: Environment variable names to check, in order.
    :param profile_keys: Config file profile keys to check, in order.
    :returns: Resolved value with source, or Resolved(value=UNSET) if not found.
    """
    # Check environment variables first
    for var_name in env_vars:
        value: str | None = os.environ.get(var_name)
        if value:
            return Resolved(value=value, source=ConfigSource.ENV)

    # Check config file profile keys
    if profile_keys:
        config_file = await ctx.parsed_profiles()
        for key in profile_keys:
            value = config_file.get(ctx.profile_name, key)
            if value:
                return Resolved(value=value, source=ConfigSource.PROFILE)

    return Resolved(value=UNSET, source=ConfigSource.DEFAULT)  # type: ignore[arg-type]


async def _resolve_int(
    ctx: SharedConfigContext,
    *,
    env_vars: Sequence[str] = (),
    profile_keys: Sequence[str] = (),
) -> Resolved[int | None]:
    """Resolve an integer value by checking providers in priority order.

    :param ctx: The shared resolution context.
    :param env_vars: Environment variable names to check, in order.
    :param profile_keys: Config file profile keys to check, in order.
    :returns: Resolved int value with source, or Resolved(value=UNSET) if not found.
    """
    result = await _resolve_str(ctx, env_vars=env_vars, profile_keys=profile_keys)
    if result.value is UNSET:
        return Resolved(value=UNSET, source=ConfigSource.DEFAULT)  # type: ignore[arg-type]
    try:
        return Resolved(value=int(result.value), source=result.source)
    except (ValueError, TypeError) as e:
        raise ConfigValidationError(
            f"Invalid integer value {result.value!r} for config key. "
            "Expected a valid integer."
        ) from e


def _strongest_source(*sources: ConfigSource) -> ConfigSource:
    """Return the highest-priority source among multiple resolved values.

    Priority: ENV > PROFILE > DEFAULT
    """
    priority = {ConfigSource.ENV: 3, ConfigSource.PROFILE: 2, ConfigSource.DEFAULT: 1}
    return max(sources, key=lambda s: priority.get(s, 0))


async def resolve_region(ctx: SharedConfigContext) -> Resolved[str | None]:
    """Resolve the AWS region from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved region value with source.
    """
    return await _resolve_str(
        ctx,
        env_vars=("AWS_REGION", "AWS_DEFAULT_REGION"),
        profile_keys=("region",),
    )


async def resolve_retry_config(
    ctx: SharedConfigContext,
) -> Resolved[RetryStrategyOptions]:
    """Resolve retry configuration from environment and config file.

    Combines retry_mode and max_attempts into a single RetryStrategyOptions.
    Each sub-value is resolved independently with its own priority chain.

    :param ctx: The shared resolution context.
    :returns: Resolved RetryStrategyOptions with the strongest source.
    """
    mode_result = await _resolve_str(
        ctx,
        env_vars=("AWS_RETRY_MODE",),
        profile_keys=("retry_mode",),
    )
    attempts_result = await _resolve_int(
        ctx,
        env_vars=("AWS_MAX_ATTEMPTS",),
        profile_keys=("max_attempts",),
    )

    # Build kwargs for values that were resolved
    kwargs: dict[str, Any] = {}
    sources_found: list[ConfigSource] = []

    if mode_result.value is not UNSET:
        validate_retry_mode(mode_result.value)
        kwargs["retry_mode"] = mode_result.value
        sources_found.append(mode_result.source)

    if attempts_result.value is not UNSET and attempts_result.value is not None:
        validate_max_attempts(attempts_result.value)
        kwargs["max_attempts"] = attempts_result.value
        sources_found.append(attempts_result.source)

    source = (
        _strongest_source(*sources_found) if sources_found else ConfigSource.DEFAULT
    )

    return Resolved(
        value=RetryStrategyOptions(**kwargs),
        source=source,
    )
