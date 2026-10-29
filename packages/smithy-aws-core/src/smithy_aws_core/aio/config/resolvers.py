# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from smithy_core.aio._program import run_program_async

from ...config.resolvers import (
    _endpoint_uri,  # pyright: ignore[reportPrivateUsage]
    _EndpointUriResolverBase,  # pyright: ignore[reportPrivateUsage]
    _max_attempts,  # pyright: ignore[reportPrivateUsage]
    _region,  # pyright: ignore[reportPrivateUsage]
    _retry_mode,  # pyright: ignore[reportPrivateUsage]
    _sdk_ua_app_id,  # pyright: ignore[reportPrivateUsage]
)
from ...config.types import Resolved
from .context import AsyncSharedConfigContext

__all__ = [
    "EndpointUriResolver",
    "resolve_endpoint_uri",
    "resolve_max_attempts",
    "resolve_region",
    "resolve_retry_mode",
    "resolve_sdk_ua_app_id",
]


async def resolve_region(ctx: AsyncSharedConfigContext) -> Resolved[str | None]:
    """Resolve the AWS region from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved region value with source.
    """
    return await run_program_async(_region(ctx))


async def resolve_retry_mode(ctx: AsyncSharedConfigContext) -> Resolved[str | None]:
    """
    Resolve the AWS retry mode from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved retry mode value with source.
    """
    return await run_program_async(_retry_mode(ctx))


async def resolve_max_attempts(ctx: AsyncSharedConfigContext) -> Resolved[int | None]:
    """Resolve the maximum number of retry attempts from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved max attempts value with source.
    """
    return await run_program_async(_max_attempts(ctx))


async def resolve_endpoint_uri(ctx: AsyncSharedConfigContext) -> Resolved[str | None]:
    """Resolve the endpoint URI from global environment or config file.

    This is the base resolver that only checks global sources.
    For service-specific resolution, use EndpointUriResolver().

    :param ctx: The shared resolution context.
    :returns: Resolved endpoint URI value with source.
    """
    return await run_program_async(_endpoint_uri(ctx))


async def resolve_sdk_ua_app_id(ctx: AsyncSharedConfigContext) -> Resolved[str | None]:
    """Resolve the SDK user-agent app ID from environment or config file.

    :param ctx: The shared resolution context.
    :returns: Resolved app ID value with source.
    """
    return await run_program_async(_sdk_ua_app_id(ctx))


class EndpointUriResolver(_EndpointUriResolverBase):
    """Service-aware endpoint URI resolver.

    Resolution order (first match wins):
    1. Service-specific env var (AWS_ENDPOINT_URL_<SERVICE_ID>)
    2. Global env var (AWS_ENDPOINT_URL)
    3. Service-specific config file (services section -> service_id -> endpoint_url)
    4. Global config file (profile -> endpoint_url)
    """

    async def __call__(self, ctx: AsyncSharedConfigContext) -> Resolved[str | None]:
        """Resolve the endpoint URI from all sources.

        :param ctx: The shared resolution context.
        :returns: Resolved endpoint URI value with source.
        """
        return await run_program_async(self._resolve(ctx))
