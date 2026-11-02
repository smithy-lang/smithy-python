#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Checks for generated clients' ``smithy.rules#endpointTests`` cases.

A case's ``params`` and ``expect`` are passed as they appear in the trait: ``expect``
is ``{"endpoint": {"url": ..., "headers": ..., "properties": ...}}`` or
``{"error": ...}``.
"""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any

from smithy_core.aio.interfaces import AsyncEndpointResolver
from smithy_core.endpoints import (
    ENDPOINT_PARAMETERS,
    STATIC_ENDPOINT_CONFIG,
    EndpointResolverParams,
    RulesExtension,
)
from smithy_core.exceptions import EndpointResolutionError
from smithy_core.interceptors import Interceptor
from smithy_core.types import TypedProperties

from .._private.endpoints import (
    UNBOUND_OPERATION,
    CaptureEndpoint,
    EndpointCaptured,
    UnboundConfig,
    check_destination,
    check_endpoint,
    check_error,
)


async def check_rules_case_async(
    resolver: AsyncEndpointResolver,
    params: Mapping[str, Any],
    expect: Mapping[str, Any],
    *,
    extensions: Sequence[RulesExtension] = (),
) -> None:
    """Resolve a case's parameter values with an endpoint resolver and check the result.

    The values are set under ``ENDPOINT_PARAMETERS`` for an operation and a config
    that bind no parameter, so only they reach the rules.

    :param resolver: The client's endpoint resolver.
    :param params: The case's parameter values, by rules name.
    :param expect: The case's expected endpoint or error.
    :param extensions: The rules extensions the resolver uses. They map the auth scheme
        names in the expected endpoint to scheme IDs.
    :raises AssertionError: If the result isn't the expected endpoint or error.
    """
    context = TypedProperties()
    context[STATIC_ENDPOINT_CONFIG] = UnboundConfig()
    context[ENDPOINT_PARAMETERS] = params
    try:
        endpoint = await resolver.resolve_endpoint(
            EndpointResolverParams(
                operation=UNBOUND_OPERATION, input=None, context=context
            )
        )
    except EndpointResolutionError as e:
        check_error(expect, e)
    else:
        check_endpoint(expect, endpoint, extensions)


async def check_client_case_async[C, I](
    client: Callable[[Interceptor[Any, Any, Any, Any]], Awaitable[C]],
    operation: Callable[[C, I], Awaitable[Any]],
    input: I,
    expect: Mapping[str, Any],
    *,
    extensions: Sequence[RulesExtension] = (),
) -> None:
    """Call a case's operation through a client and check the endpoint it resolves.

    :param client: Builds the client with an interceptor added to its config, which
        stops the call once its endpoint is applied to the request, so nothing is
        signed or sent.
    :param operation: The client's operation method.
    :param input: The operation input.
    :param expect: The case's expected endpoint or error.
    :param extensions: The rules extensions the client's endpoint resolver uses. They map
        the auth scheme names in the expected endpoint to scheme IDs.
    :raises AssertionError: If the call doesn't resolve the expected endpoint or error,
        or doesn't send its request to the endpoint's host, under its path and query.
    """
    instance = await client(CaptureEndpoint())
    try:
        await operation(instance, input)
    except EndpointCaptured as captured:
        check_endpoint(expect, captured.endpoint, extensions)
        check_destination(captured.endpoint, captured.request)
    except EndpointResolutionError as e:
        check_error(expect, e)
    else:
        raise AssertionError("The call completed without resolving an endpoint")
    finally:
        # Clients hold their transport until they're closed.
        close = getattr(instance, "close", None)
        if close is not None:
            await close()
