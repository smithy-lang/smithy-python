# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""The endpoint resolvers: one that evaluates an endpoint BDD, one for a static URI."""

from collections.abc import Sequence
from typing import Any

from ..exceptions import EndpointResolutionError, ExpectationNotMetError
from ..interfaces import EndpointResolver as _EndpointResolver
from ..interfaces import TypedProperties as _TypedProperties
from ..interfaces import URI as _URI
from ..utils import parse_uri
from ._engine import RulesEngine
from ._params import ParamPlan
from ._types import (
    STATIC_ENDPOINT_CONFIG,
    Endpoint,
    EndpointBdd,
    EndpointResolverParams,
    RulesExtension,
)


def resolve_static_uri(
    properties: _TypedProperties | EndpointResolverParams[Any],
) -> _URI | None:
    """Attempt to resolve a static URI from the endpoint resolver params.

    :param properties: A TypedProperties bag or EndpointResolverParams to search.
    :raises EndpointResolutionError: If the configured endpoint URI is invalid.
    """
    properties = (
        properties.context
        if isinstance(properties, EndpointResolverParams)
        else properties
    )
    static_uri_config = properties.get(STATIC_ENDPOINT_CONFIG)
    if static_uri_config is None or static_uri_config.endpoint_uri is None:
        return None

    static_uri = static_uri_config.endpoint_uri

    # If it's not a string, it's already a parsed URI so just pass it along.
    if not isinstance(static_uri, str):
        return static_uri

    try:
        return parse_uri(static_uri)
    except ExpectationNotMetError as e:
        raise EndpointResolutionError(f"Invalid endpoint URI: {static_uri}") from e


class BddEndpointResolver(_EndpointResolver):
    """Resolves endpoints by evaluating a service's endpoint binary decision diagram."""

    def __init__(
        self,
        bdd: EndpointBdd,
        *,
        extensions: Sequence[RulesExtension] = (),
    ) -> None:
        """Create a resolver for an endpoint BDD.

        :param bdd: The service's endpoint binary decision diagram.
        :param extensions: Functions and built-in bindings beyond the rules standard
            library, which is always included.
        """
        self._engine = RulesEngine(bdd, extensions)
        self._plan = ParamPlan(bdd.parameters, extensions)
        # Without an SDK::Endpoint parameter, a configured endpoint_uri is used as is.
        self._uses_endpoint_builtin = any(
            builtin == "SDK::Endpoint" for *_, builtin, _ in bdd.parameters
        )
        # L1 cache: the last parameter values and their endpoint
        self._last: tuple[tuple[Any, ...], Endpoint] | None = None

    def __deepcopy__(self, memo: Any) -> "BddEndpointResolver":
        return self

    def resolve_endpoint(self, params: EndpointResolverParams[Any]) -> Endpoint:
        if not self._uses_endpoint_builtin:
            uri = resolve_static_uri(params)
            if uri is not None:
                return Endpoint(uri=uri)
        param_values = self._plan.bind(params)
        last = self._last
        if last is not None and last[0] == param_values:
            return last[1]
        endpoint = self._engine.evaluate(param_values)
        self._last = (param_values, endpoint)
        return endpoint


class StaticEndpointResolver(_EndpointResolver):
    """A basic endpoint resolver that forwards a static URI."""

    def resolve_endpoint(self, params: EndpointResolverParams[Any]) -> Endpoint:
        static_uri = resolve_static_uri(params)
        if static_uri is None:
            raise EndpointResolutionError(
                "Unable to resolve endpoint: endpoint_uri is required"
            )
        return Endpoint(uri=static_uri)
