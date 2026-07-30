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


async def resolve_endpoint_uri(ctx: SharedConfigContext) -> Resolved[str | None]:
    """Resolve the endpoint URI from global environment or config file.

    This is the base resolver that only checks global sources.
    For service-specific resolution, use make_endpoint_uri_resolver().

    :param ctx: The shared resolution context.
    :returns: Resolved endpoint URI value with source.
    """
    return await _resolve_str(
        ctx,
        env_vars=("AWS_ENDPOINT_URL",),
        profile_keys=("endpoint_url",),
    )


async def resolve_aws_access_key_id(ctx: SharedConfigContext) -> Resolved[str | None]:
    """Resolve the AWS access key ID from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved access key ID value with source.
    """
    return await _resolve_str(
        ctx,
        env_vars=("AWS_ACCESS_KEY_ID",),
        profile_keys=("aws_access_key_id",),
    )


async def resolve_aws_secret_access_key(
    ctx: SharedConfigContext,
) -> Resolved[str | None]:
    """Resolve the AWS secret access key from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved secret access key value with source.
    """
    return await _resolve_str(
        ctx,
        env_vars=("AWS_SECRET_ACCESS_KEY",),
        profile_keys=("aws_secret_access_key",),
    )


async def resolve_aws_session_token(ctx: SharedConfigContext) -> Resolved[str | None]:
    """Resolve the AWS session token from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved session token value with source.
    """
    return await _resolve_str(
        ctx,
        env_vars=("AWS_SESSION_TOKEN",),
        profile_keys=("aws_session_token",),
    )


async def resolve_sdk_ua_app_id(ctx: SharedConfigContext) -> Resolved[str | None]:
    """Resolve the SDK user-agent app ID from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved app ID value with source.
    """
    return await _resolve_str(
        ctx,
        env_vars=("AWS_SDK_UA_APP_ID",),
        profile_keys=("sdk_ua_app_id",),
    )


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
            f"AWS_ENDPOINT_URL_{service_id.replace('-', '_').upper()}"
        )
        self._service_key = service_id.replace("-", "_").lower()

    async def __call__(self, ctx: SharedConfigContext) -> Resolved[str | None]:
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


def make_endpoint_uri_resolver(service_id: str) -> EndpointUriResolver:
    """Create a service-aware endpoint URI resolver.

    :param service_id: The service identifier (e.g., "bedrock_runtime").
    :returns: An EndpointUriResolver instance for use in FieldSpec.
    """
    return EndpointUriResolver(service_id)
