#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Async checks for generated clients' ``smithy.rules#endpointTests`` cases.

A case's ``params`` and ``expect`` are passed as they appear in the trait: ``expect``
is ``{"endpoint": {"url": ..., "headers": ..., "properties": ...}}`` or
``{"error": ...}``.
"""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, Concatenate

from smithy_core.endpoints import RulesExtension
from smithy_core.exceptions import EndpointResolutionError
from smithy_core.interceptors import Interceptor

from .._private.endpoints import (
    CaptureEndpoint,
    EndpointCaptured,
    check_destination,
    check_endpoint,
    check_error,
)


async def check_client_case_async[C](
    client: Callable[[Interceptor[Any, Any, Any, Any]], Awaitable[C]],
    operation: Callable[Concatenate[C, ...], Awaitable[Any]],
    input: Mapping[str, Any],
    expect: Mapping[str, Any],
    *,
    extensions: Sequence[RulesExtension] = (),
) -> None:
    """Call a case's operation through a client and check the endpoint it resolves.

    :param client: Builds the client with an interceptor added to its config, which
        stops the call once its endpoint is applied to the request, so nothing is
        signed or sent.
    :param operation: The client's operation method, which takes the members of its
        input as keyword arguments.
    :param input: The keyword arguments of the call, by parameter name. The values are
        passed as they are, so a nested value may be a model or a dictionary.
    :param expect: The case's expected endpoint or error.
    :param extensions: The rules extensions the client's endpoint resolver uses. Their
        factories build the auth schemes in the expected endpoint.
    :raises AssertionError: If the call doesn't resolve the expected endpoint or error,
        or doesn't send its request to the endpoint's host, under its path and query.
    """
    instance = await client(CaptureEndpoint())
    try:
        await operation(instance, **input)
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
