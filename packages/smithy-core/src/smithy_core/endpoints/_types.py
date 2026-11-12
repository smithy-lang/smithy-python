# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""The data types endpoint resolution shares: the BDD a resolver evaluates, the
extensions its rules call, what it is given and returns, and the properties that
carry them."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final, NamedTuple, Protocol

from .. import URI
from ..interfaces import Endpoint as _Endpoint
from ..interfaces import TypedProperties as _TypedProperties
from ..interfaces import URI as _URI
from ..schemas import APIOperation
from ..serializers import SerializeableShape
from ..shapes import ShapeID
from ..types import PropertyKey, TypedProperties


@dataclass(slots=True)
class EndpointAuthScheme:
    """An auth scheme an endpoint supports, with the signer properties it overrides."""

    scheme_id: ShapeID
    """The ID of the auth scheme."""

    properties: _TypedProperties = field(default_factory=TypedProperties)
    """Signer property overrides for the auth scheme at this endpoint."""


@dataclass(kw_only=True)
class Endpoint(_Endpoint):
    """A resolved endpoint."""

    uri: _URI
    """The endpoint URI."""

    properties: _TypedProperties = field(default_factory=TypedProperties)
    """Properties required to interact with the endpoint.

    For example, in some AWS use cases this might contain HTTP headers to add to each
    request.
    """

    auth_schemes: Sequence[EndpointAuthScheme] = ()
    """The auth schemes the endpoint supports, in order of preference.

    Empty when the endpoint has no special auth settings.
    """


ENDPOINT_HEADERS: PropertyKey[Mapping[str, tuple[str, ...]]] = PropertyKey(
    key="endpoint_headers",
    value_type=Mapping[str, tuple[str, ...]],
)
"""An endpoint property holding the headers its rules add, by header name."""

RESOLVED_ENDPOINT: PropertyKey[_Endpoint] = PropertyKey(
    key="resolved_endpoint",
    value_type=_Endpoint,
)
"""A call context property holding the endpoint resolved for the current attempt.

Resolvers cache endpoints, so other calls may share this object: don't modify it.
"""

HOST_PREFIX: PropertyKey[str] = PropertyKey(key="host_prefix", value_type=str)
"""A call context property holding the operation's expanded endpoint host prefix.

It's prepended to the host of every attempt's resolved endpoint. It's unset when the
operation has no host prefix or the config sets ``disable_host_prefix_injection``.
"""

ENDPOINT_PARAMETERS: PropertyKey[Mapping[str, Any]] = PropertyKey(
    key="endpoint_parameters",
    value_type=Mapping[str, Any],
)
"""A call context property holding endpoint parameter values by rules name.

They override the values bound from the config, the input and the operation's traits.
None unsets a parameter, so it takes its default. Names the rules don't declare are
ignored.
"""


@dataclass(kw_only=True)
class EndpointResolverParams[I: SerializeableShape]:
    """Parameters passed into an Endpoint Resolver's resolve_endpoint method."""

    operation: APIOperation[I, Any] = field(repr=False)
    """The operation to resolve an endpoint for."""

    input: I
    """The input to the operation."""

    context: _TypedProperties
    """The context of the operation invocation."""


class StaticEndpointConfig(Protocol):
    """A config that has a static endpoint."""

    endpoint_uri: str | URI | None
    """A static endpoint to use for the request."""


STATIC_ENDPOINT_CONFIG = PropertyKey(key="config", value_type=StaticEndpointConfig)
"""Property containing a config that has a static endpoint."""


class Tag:
    """The integers that lead expression and result tuples in an endpoint BDD.

    Generated modules write them as literals, so each BDD stays one constant.
    """

    REF: Final = 0
    ATTR: Final = 1
    CALL: Final = 2
    LIST: Final = 3
    MAP: Final = 4
    ERROR: Final = 5
    ENDPOINT: Final = 6


class EndpointBdd(NamedTuple):
    """A service's endpoint rules, lowered from its ``endpointBdd`` trait.

    Generated ``_private/endpoints.py`` modules hold one as data. Its parts are
    positional tuples, and expressions and results start with an integer tag:
    ``REF`` 0, ``ATTR`` 1, ``CALL`` 2, ``LIST`` 3, ``MAP`` 4, ``ERROR`` 5 and
    ``ENDPOINT`` 6.

    - Parameter: ``(name, type, required, default, builtin, client_context_attribute)``,
      where ``type`` is ``"string"``, ``"boolean"`` or ``"stringArray"``, and
      ``client_context_attribute`` is the config attribute a client context parameter
      reads, else None.
    - Condition: ``(expression, assign target or None)``.
    - Result: ``(ERROR, message)`` or ``(ENDPOINT, url, properties, headers)``,
      where ``properties`` is a map or None and ``headers`` is a tuple of
      ``(name, (expression, ...))``.
    - Expression: a bool or int literal, a template string, ``(REF, name)``,
      ``(ATTR, expression, path)``, ``(CALL, function, *arguments)``,
      ``(LIST, *items)`` or ``(MAP, keys, *values)``.

    Templates and getAttr paths are written as in the trait. In a template,
    ``{name}`` and ``{name#path}`` are placeholders and ``{{`` and ``}}`` are literal
    braces. A path is keys separated by ``.``, each optionally followed by an index
    ``[i]`` that counts from the end when negative.
    """

    parameters: tuple[tuple[Any, ...], ...]
    """The rules parameters, in trait order, minus optional ones no rule reads."""

    functions: tuple[str, ...]
    """Every function a condition or result calls, sorted."""

    conditions: tuple[tuple[Any, ...], ...]
    """The trait's conditions, in order."""

    results: tuple[tuple[Any, ...] | None, ...]
    """None, the no-match result, followed by the trait's results in order."""

    root: int
    """The trait's root reference."""

    nodes: tuple[int, ...]
    """The trait's nodes, three ints per node."""


type BuiltinGetter = Callable[[Any, _TypedProperties], Any]
"""Computes a built-in parameter's value from the config and the call context."""

type BuiltinBinding = str | BuiltinGetter
"""How a built-in parameter gets its value: a config attribute name, or a getter."""

type EndpointAuthSchemeFactory = Callable[[Mapping[str, Any]], EndpointAuthScheme]
"""Builds an endpoint's auth scheme from an ``authSchemes`` entry of its rules."""


@dataclass(frozen=True, slots=True)
class RulesExtension:
    """Functions, built-in parameter bindings and auth schemes contributed to the
    rules engine."""

    functions: Mapping[str, Callable[..., Any]] = field(
        default_factory=dict[str, Callable[..., Any]]
    )
    """Rules library functions by rules-language name.

    Their result must depend only on their arguments, with no side effects, because
    resolved endpoints are cached by parameter values. Given None for an unset value,
    they return None. The standard library's names are reserved: a resolver given an
    extension that defines one raises.
    """

    builtins: Mapping[str, BuiltinBinding] = field(
        default_factory=dict[str, BuiltinBinding]
    )
    """Built-in parameter IDs mapped to a config attribute name, or to a getter
    receiving (config, call context).

    ``SDK::Endpoint`` is reserved: a resolver given an extension that binds it raises.
    """

    auth_schemes: Mapping[str, EndpointAuthSchemeFactory] = field(
        default_factory=dict[str, EndpointAuthSchemeFactory]
    )
    """Auth scheme names, as endpoint rules write them in ``authSchemes``, mapped to
    factories that build the endpoint's auth scheme from the rules' entry.

    A factory gives the scheme ID and turns the entry's properties into the scheme's
    signer property overrides.
    """
