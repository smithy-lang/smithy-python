#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping, Sequence
from typing import Any

from smithy_core.endpoints import (
    ENDPOINT_PARAMETERS,
    STATIC_ENDPOINT_CONFIG,
    EndpointResolverParams,
    RulesExtension,
)
from smithy_core.exceptions import EndpointResolutionError
from smithy_core.interfaces import EndpointResolver
from smithy_core.types import TypedProperties

from ._private.endpoints import (
    UNBOUND_OPERATION,
    UnboundConfig,
    check_endpoint,
    check_error,
)


def check_rules_case(
    resolver: EndpointResolver,
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
    :param extensions: The rules extensions the resolver uses. Their factories build
        the auth schemes in the expected endpoint.
    :raises AssertionError: If the result isn't the expected endpoint or error.
    """
    context = TypedProperties()
    context[STATIC_ENDPOINT_CONFIG] = UnboundConfig()
    context[ENDPOINT_PARAMETERS] = params
    try:
        endpoint = resolver.resolve_endpoint(
            EndpointResolverParams(
                operation=UNBOUND_OPERATION, input=None, context=context
            )
        )
    except EndpointResolutionError as e:
        check_error(expect, e)
    else:
        check_endpoint(expect, endpoint, extensions)
