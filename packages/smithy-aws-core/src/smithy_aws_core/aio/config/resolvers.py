# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import warnings
from collections.abc import Sequence

from ...config.exceptions import ConfigValidationError
from ...config.types import UNSET, ConfigSource, Resolved
from .context import AsyncSharedConfigContext

__all__ = [
    "EndpointUriResolver",
    "resolve_account_id_endpoint_mode",
    "resolve_bool",
    "resolve_endpoint_uri",
    "resolve_max_attempts",
    "resolve_region",
    "resolve_response_checksum_validation",
    "resolve_retry_mode",
    "resolve_sdk_ua_app_id",
    "resolve_use_dualstack_endpoint",
    "resolve_use_fips_endpoint",
]


async def _lookup(
    ctx: AsyncSharedConfigContext,
    env_vars: Sequence[str],
    profile_keys: Sequence[str],
) -> tuple[str, str, ConfigSource] | None:
    """Find the first set value: env vars first, then config file profile keys.

    :returns: The value, the env var or profile key it was read from, and its source,
        or None if none is set.
    """
    for var_name in env_vars:
        value: str | None = os.environ.get(var_name)
        if value:
            return value, var_name, ConfigSource.ENV

    if profile_keys:
        config_file = await ctx.parsed_profiles()
        for key in profile_keys:
            value = config_file.get(ctx.profile_name, key)
            if value:
                return value, key, ConfigSource.PROFILE

    return None


async def _resolve_str(
    ctx: AsyncSharedConfigContext,
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
    found = await _lookup(ctx, env_vars, profile_keys)
    if found is None:
        return Resolved(value=UNSET, source=ConfigSource.DEFAULT)  # type: ignore[arg-type]
    value, _, source = found
    return Resolved(value=value, source=source)


async def _resolve_int(
    ctx: AsyncSharedConfigContext,
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


async def resolve_bool(
    ctx: AsyncSharedConfigContext,
    *,
    env_vars: Sequence[str] = (),
    profile_keys: Sequence[str] = (),
) -> Resolved[bool | None]:
    """Resolve a boolean value from the environment, then the shared config file.

    Accepts ``true`` and ``false`` in any case. Generated clients use it to resolve
    their service-specific boolean fields.

    :param ctx: The shared resolution context.
    :param env_vars: Environment variable names to check, in order.
    :param profile_keys: Config file profile keys to check, in order.
    :returns: Resolved bool value with source, or Resolved(value=UNSET) if not found.
    """
    found = await _lookup(ctx, env_vars, profile_keys)
    if found is None:
        return Resolved(value=UNSET, source=ConfigSource.DEFAULT)  # type: ignore[arg-type]
    value, name, source = found
    match value.lower():
        case "true":
            return Resolved(value=True, source=source)
        case "false":
            return Resolved(value=False, source=source)
        case _:
            raise ConfigValidationError(
                f"Invalid boolean value {value!r} for {name}. Expected true or false."
            )


async def resolve_region(ctx: AsyncSharedConfigContext) -> Resolved[str | None]:
    """Resolve the AWS region from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved region value with source.
    """
    return await _resolve_str(
        ctx,
        env_vars=("AWS_REGION", "AWS_DEFAULT_REGION"),
        profile_keys=("region",),
    )


async def resolve_retry_mode(ctx: AsyncSharedConfigContext) -> Resolved[str | None]:
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
    return result


async def resolve_response_checksum_validation(
    ctx: AsyncSharedConfigContext,
) -> Resolved[str | None]:
    """Resolve when response checksums are validated from environment or config file.

    Values are case-insensitive and are returned in lowercase.

    :param ctx: The shared resolution context.
    :returns: Resolved value with source.
    """
    result = await _resolve_str(
        ctx,
        env_vars=("AWS_RESPONSE_CHECKSUM_VALIDATION",),
        profile_keys=("response_checksum_validation",),
    )
    if result.value is UNSET:
        return result
    return Resolved(value=result.value.lower(), source=result.source)


async def resolve_max_attempts(ctx: AsyncSharedConfigContext) -> Resolved[int | None]:
    """Resolve the maximum number of retry attempts from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved max attempts value with source.
    """
    return await _resolve_int(
        ctx,
        env_vars=("AWS_MAX_ATTEMPTS",),
        profile_keys=("max_attempts",),
    )


async def resolve_endpoint_uri(ctx: AsyncSharedConfigContext) -> Resolved[str | None]:
    """Resolve the endpoint URI from global environment or config file.

    This is the base resolver that only checks global sources.
    For service-specific resolution, use EndpointUriResolver().

    :param ctx: The shared resolution context.
    :returns: Resolved endpoint URI value with source.
    """
    return await _resolve_str(
        ctx,
        env_vars=("AWS_ENDPOINT_URL",),
        profile_keys=("endpoint_url",),
    )


async def resolve_sdk_ua_app_id(ctx: AsyncSharedConfigContext) -> Resolved[str | None]:
    """Resolve the SDK user-agent app ID from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved app ID value with source.
    """
    return await _resolve_str(
        ctx,
        env_vars=("AWS_SDK_UA_APP_ID",),
        profile_keys=("sdk_ua_app_id",),
    )


async def resolve_use_fips_endpoint(
    ctx: AsyncSharedConfigContext,
) -> Resolved[bool | None]:
    """Resolve whether to use FIPS endpoints from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved use FIPS endpoint value with source.
    """
    return await resolve_bool(
        ctx,
        env_vars=("AWS_USE_FIPS_ENDPOINT",),
        profile_keys=("use_fips_endpoint",),
    )


async def resolve_use_dualstack_endpoint(
    ctx: AsyncSharedConfigContext,
) -> Resolved[bool | None]:
    """Resolve whether to use dual-stack endpoints from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved use dual-stack endpoint value with source.
    """
    return await resolve_bool(
        ctx,
        env_vars=("AWS_USE_DUALSTACK_ENDPOINT",),
        profile_keys=("use_dualstack_endpoint",),
    )


async def resolve_account_id_endpoint_mode(
    ctx: AsyncSharedConfigContext,
) -> Resolved[str | None]:
    """Resolve the account ID endpoint mode from environment or config file.

    The value is read in any case and lowercased.

    :param ctx: The shared resolution context.
    :returns: Resolved account ID endpoint mode value with source.
    """
    result = await _resolve_str(
        ctx,
        env_vars=("AWS_ACCOUNT_ID_ENDPOINT_MODE",),
        profile_keys=("account_id_endpoint_mode",),
    )
    if result.value is UNSET:
        return result
    return Resolved(value=result.value.lower(), source=result.source)


class EndpointUriResolver:
    """Service-aware endpoint URI resolver.

    Resolution order (first match wins):
    1. Service-specific env var (AWS_ENDPOINT_URL_<SERVICE_ID>)
    2. Global env var (AWS_ENDPOINT_URL)
    3. Service-specific config file (services section -> service_id -> endpoint_url)
    4. Global config file (profile -> endpoint_url)
    """

    def __init__(self, service_id: str):
        """Initialize with a service identifier.

        :param service_id: The service identifier (e.g., "bedrock_runtime").
            Used to construct the service-specific env var and config lookup key.
        """
        self._service_env_var = (
            f"AWS_ENDPOINT_URL_{service_id.replace(' ', '_').replace('-', '_').upper()}"
        )

        self._service_key = service_id.replace(" ", "_").replace("-", "_").lower()

    async def __call__(self, ctx: AsyncSharedConfigContext) -> Resolved[str | None]:
        """Resolve the endpoint URI from all sources.

        :param ctx: The shared resolution context.
        :returns: Resolved endpoint URI value with source.
        """
        value = os.environ.get(self._service_env_var)
        if value:
            return Resolved(value=value, source=ConfigSource.ENV)

        value = os.environ.get("AWS_ENDPOINT_URL")
        if value:
            return Resolved(value=value, source=ConfigSource.ENV)

        config_file = await ctx.parsed_profiles()
        value = config_file.get_service_config(
            ctx.profile_name, self._service_key, "endpoint_url"
        )
        if value:
            return Resolved(value=value, source=ConfigSource.PROFILE)

        value = config_file.get(ctx.profile_name, "endpoint_url")
        if value:
            return Resolved(value=value, source=ConfigSource.PROFILE)

        return Resolved(value=UNSET, source=ConfigSource.DEFAULT)  # type: ignore[arg-type]
