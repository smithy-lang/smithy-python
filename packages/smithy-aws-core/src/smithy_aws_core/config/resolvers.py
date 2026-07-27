# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import warnings
from collections.abc import Sequence

from .context import SharedConfigContext
from .exceptions import ConfigValidationError
from .types import UNSET, ConfigSource, Resolved


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


async def resolve_retry_mode(ctx: SharedConfigContext) -> Resolved[str | None]:
    """
    Resolve the AWS retry mode from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved retry mode value with source.
    """
    result = await _resolve_str(
        ctx,
        env_vars=("AWS_RETRY_MODE",),
        profile_keys=("retry_mode",),
    )
    if result.value == "legacy":
        warnings.warn(
            "'legacy' retry mode is not supported, using 'standard' instead.",
            UserWarning,
            stacklevel=2,
        )
        return Resolved(value="standard", source=result.source)
    elif result.value == "adaptive":
        warnings.warn(
            "'adaptive' retry mode is not supported, using 'standard' instead.",
            UserWarning,
            stacklevel=2,
        )
        return Resolved(value="standard", source=result.source)
    return result


async def resolve_max_attempts(ctx: SharedConfigContext) -> Resolved[int | None]:
    """Resolve the maximum number of retry attempts from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved max attempts value with source.
    """
    return await _resolve_int(
        ctx,
        env_vars=("AWS_MAX_ATTEMPTS",),
        profile_keys=("max_attempts",),
    )
