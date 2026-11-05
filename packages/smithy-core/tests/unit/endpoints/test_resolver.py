# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Endpoint resolvers: parameter binding, caching, and the async resolver."""

from dataclasses import dataclass
from typing import Any

import pytest
from smithy_core import URI
from smithy_core.aio.endpoints import AsyncBddEndpointResolver
from smithy_core.endpoints import (
    ENDPOINT_PARAMETERS,
    BddEndpointResolver,
    EndpointBdd,
    EndpointResolverParams,
    RulesExtension,
)
from smithy_core.endpoints._types import Tag
from smithy_core.exceptions import EndpointResolutionError
from smithy_core.shapes import ShapeType
from smithy_core.types import TypedProperties

from ._bdds import (
    Config,
    Input,
    chain,
    echo,
    endpoint,
    error,
    make_operation,
    resolve,
    string,
)

STRING = ShapeType.STRING.value
CONTEXT = "smithy.rules#contextParam"
STATIC = "smithy.rules#staticContextParams"
OPERATION_CONTEXT = "smithy.rules#operationContextParams"
REQUIRED = "smithy.api#required"

# One parameter per source, plus parameters several sources feed.
PARAMETERS: list[tuple[Any, ...]] = [
    ("Static", "string", False, None, "X::Static", "static"),
    ("Context", "string", False, "default", "X::Context", "context"),
    ("Path", "string", False, None, "X::Path", "path"),
    ("Client", "string", False, None, "X::Client", "client"),
    ("Builtin", "string", False, "default", "X::Builtin", None),
    ("Getter", "string", False, None, "X::Getter", None),
    ("Default", "string", True, "default", None, None),
    ("Tables", "stringArray", False, None, None, None),
]


def _getter(config: Any, context: Any) -> Any:
    return getattr(config, "getter_source", None)


EXTENSION = RulesExtension(
    builtins={
        "X::Static": "static_builtin",
        "X::Context": "context_builtin",
        "X::Path": "path_builtin",
        "X::Client": "client_builtin",
        "X::Builtin": "builtin_attribute",
        "X::Getter": _getter,
    }
)

OPERATION = make_operation(
    "Everything",
    {
        "Static": (STRING, {CONTEXT: {"name": "Static"}}),
        "ContextMember": (STRING, {CONTEXT: {"name": "Context"}}),
        "Nested": (
            (
                ShapeType.STRUCTURE.value,
                "com.example",
                "Nested",
                0,
                ("Value",),
                ((STRING, 0),),
            ),
            0,
        ),
        "Key": (STRING, {CONTEXT: {"name": "Key"}, REQUIRED: {}}),
        "Names": (
            (
                ShapeType.LIST.value,
                "com.example",
                "Names",
                0,
                ("member",),
                ((STRING, 0),),
            ),
            0,
        ),
    },
    {
        STATIC: {"Static": {"value": "static"}, "Unknown": {"value": "x"}},
        OPERATION_CONTEXT: {
            "Context": {"path": "Nested.Value"},
            "Path": {"path": "Nested.Value"},
            "Tables": {"path": "Names"},
        },
    },
)


def _bound(
    config: Any,
    input: Any = None,
    *,
    parameters: dict[str, Any] | None = None,
    bdd: EndpointBdd | None = None,
    extensions: list[RulesExtension] | None = None,
) -> dict[str, Any]:
    """The parameter values one call of OPERATION binds, by name."""
    resolver = BddEndpointResolver(
        bdd or echo(PARAMETERS),
        extensions=[EXTENSION] if extensions is None else extensions,
    )
    endpoint = resolve(
        resolver,
        parameters=parameters,
        config=config,
        operation=OPERATION,
        input=input or Input(key="k"),
    )
    return dict(endpoint.properties.items())


# --------------------------------------------------------------- binding


def test_sources_by_precedence() -> None:
    everything = Config(
        static=1,
        context="client",
        path="client",
        client="client",
        static_builtin="b",
        context_builtin="b",
        builtin_attribute="builtin",
        getter_source="got",
    )
    bound = _bound(
        everything,
        Input(
            static="input", context_member="input", key="k", nested=Input(value="path")
        ),
    )
    assert bound == {
        "Static": "static",
        "Context": "input",
        "Path": "path",
        "Client": "client",
        "Builtin": "builtin",
        "Getter": "got",
        "Default": "default",
        "Tables": None,
    }

    # None never overrides a lower-precedence source.
    bound = _bound(everything, Input(key="k", nested=Input()))
    assert bound["Context"] == "client"
    assert bound["Path"] == "client"
    # Client is both a built-in and a client context parameter, so it reads only
    # its client context attribute.
    bound = _bound(Config(client_builtin="builtin"))
    assert bound["Context"] == "default"
    assert bound["Builtin"] == "default"
    assert bound["Client"] is None
    assert bound["Getter"] is None


def test_endpoint_parameters_override_every_source() -> None:
    bound = _bound(
        Config(context="client", builtin_attribute="builtin"),
        Input(context_member="input", key="k", nested=Input(value="path")),
        parameters={
            "Static": "given",
            "Context": None,
            "Builtin": "given",
            "Tables": ["a", None],
            "Undeclared": "ignored",
        },
    )
    assert bound == {
        # Over staticContextParams, the highest-precedence trait source.
        "Static": "given",
        # None unsets the parameter, which then takes its default.
        "Context": "default",
        "Path": "path",
        "Client": None,
        "Builtin": "given",
        "Getter": None,
        "Default": "default",
        "Tables": ("a",),
    }


def test_string_arrays_become_tuples_without_none() -> None:
    assert _bound(Config(), Input(key="k", names=["a", None, "b"]))["Tables"] == (
        "a",
        "b",
    )


REGION: list[tuple[Any, ...]] = [("Region", "string", True, None, "X::Region", None)]
REGION_EXTENSION = RulesExtension(builtins={"X::Region": "region"})


def test_required_parameters() -> None:
    resolver = BddEndpointResolver(echo(REGION), extensions=[REGION_EXTENSION])
    with pytest.raises(EndpointResolutionError, match="parameter: Region"):
        resolve(resolver)
    assert resolve(resolver, config=Config(region="r")).properties["Region"] == "r"
    # A static value satisfies a required parameter.
    static = make_operation("Static", {}, {STATIC: {"Region": {"value": "s"}}})
    assert resolve(resolver, operation=static).properties["Region"] == "s"


def test_operations_bind_their_own_sources() -> None:
    resolver = BddEndpointResolver(echo([("Name", "string", False, None, None, None)]))
    with_name = make_operation(
        "WithName", {"Name": (STRING, {CONTEXT: {"name": "Name"}})}
    )
    without = make_operation("WithoutName", {"Name": (STRING, 0)})
    for _ in range(2):
        bound = resolve(resolver, operation=with_name, input=Input(name="n"))
        assert bound.properties["Name"] == "n"
        bound = resolve(resolver, operation=without, input=Input(name="n"))
        assert bound.properties["Name"] is None


def test_client_context_parameters_read_the_attribute_the_bdd_names() -> None:
    bdd = echo([("EnableTracing", "string", False, None, None, "trace_requests")])
    config = Config(trace_requests="v", enable_tracing="other")
    assert _bound(config, bdd=bdd) == {"EnableTracing": "v"}


# --------------------------------------------------------------- resolving

NAMED = chain(
    [
        ("Name", "string", True, None, None, None),
        ("Endpoint", "string", False, None, "SDK::Endpoint", None),
    ],
    [((Tag.CALL, "isSet", (Tag.REF, "Endpoint")), None)],
    [
        endpoint("{Endpoint}/{Name}"),
        endpoint("https://{Name}.example.com"),
    ],
)

THING_OPERATION = make_operation(
    "GetThing",
    {
        "Name": (STRING, {CONTEXT: {"name": "Name"}, REQUIRED: {}}),
        "Key": (STRING, {CONTEXT: {"name": "Key"}, REQUIRED: {}}),
    },
)


@dataclass
class ThingInput:
    name: str | None
    key: str = "k"


def _get_thing(
    resolver: BddEndpointResolver, input: ThingInput, config: Any = None
) -> Any:
    return resolve(resolver, config=config, operation=THING_OPERATION, input=input)


def test_resolver_resolves_endpoints() -> None:
    resolver = BddEndpointResolver(NAMED)
    input = ThingInput("n")
    assert _get_thing(resolver, input).uri == URI(host="n.example.com")
    endpoint_ = _get_thing(resolver, input, Config(endpoint_uri="http://h:1"))
    assert endpoint_.uri == URI(scheme="http", host="h", port=1, path="/n")
    uri = URI(scheme="http", host="u")
    endpoint_ = _get_thing(resolver, input, Config(endpoint_uri=uri))
    assert endpoint_.uri == URI(scheme="http", host="u", path="/n")


@pytest.mark.parametrize("name", [None, "", " \t"])
def test_blank_required_context_parameters_raise(name: str | None) -> None:
    resolver = BddEndpointResolver(NAMED)
    with pytest.raises(EndpointResolutionError, match="member name"):
        _get_thing(resolver, ThingInput(name))


@pytest.mark.parametrize("key", [None, "", " \t"])
def test_blank_required_context_parameters_the_rules_dont_read_raise(
    key: str | None,
) -> None:
    # OPERATION's required Key member names a parameter its BDD doesn't declare.
    with pytest.raises(EndpointResolutionError, match="member key"):
        _bound(Config(), Input(key=key))


def test_cached_endpoints_follow_the_parameters_rules_read() -> None:
    resolver = BddEndpointResolver(NAMED)
    first = _get_thing(resolver, ThingInput("n", "k1"))
    # The rules don't read Key, so another Key gives the same endpoint.
    assert _get_thing(resolver, ThingInput("n", "k2")) == first
    other = _get_thing(resolver, ThingInput("c"))
    assert other.uri.host == "c.example.com"
    assert _get_thing(resolver, ThingInput("n", "k3")) == first


def test_bdds_without_sdk_endpoint_use_endpoint_uri_as_given() -> None:
    no_endpoint = chain(
        [("Region", "string", True, "r", None, None)],
        [],
        [endpoint("https://{Region}.example.com")],
    )
    resolver = BddEndpointResolver(no_endpoint)
    endpoint_ = resolve(resolver, config=Config(endpoint_uri="https://custom:8443/p"))
    assert endpoint_.uri == URI(host="custom", port=8443, path="/p")
    uri = URI(host="given")
    assert resolve(resolver, config=Config(endpoint_uri=uri)).uri is uri
    assert resolve(resolver).uri == URI(host="r.example.com")


async def test_async_resolver() -> None:
    upper = chain(
        [string("S")],
        [((Tag.CALL, "x.upper", (Tag.REF, "S")), "u")],
        [endpoint("https://{u}"), error("no")],
    )
    extension = RulesExtension(functions={"x.upper": str.upper})
    resolver = AsyncBddEndpointResolver(upper, extensions=[extension])
    context = TypedProperties({"config": Config()})
    context[ENDPOINT_PARAMETERS] = {"S": "h"}
    params = EndpointResolverParams(
        operation=make_operation(), input=None, context=context
    )
    assert (await resolver.resolve_endpoint(params)).uri == URI(host="H")
