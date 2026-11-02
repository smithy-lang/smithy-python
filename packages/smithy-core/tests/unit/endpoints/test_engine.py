# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""The rules engine, through the resolver: BDD walks, results and expressions."""

from typing import Any

import pytest
from smithy_core import URI
from smithy_core.endpoints import (
    ENDPOINT_HEADERS,
    BddEndpointResolver,
    RulesExtension,
)
from smithy_core.endpoints._types import Tag
from smithy_core.exceptions import EndpointResolutionError
from smithy_core.shapes import ShapeID

from ._bdds import (
    RESULT_OFFSET,
    assemble,
    boolean,
    chain,
    endpoint,
    error,
    resolve,
    string,
)

R = RESULT_OFFSET


def _parts(*values: Any) -> tuple[Any, ...]:
    return values


EXTRA = RulesExtension(functions={"x.parts": _parts})


def test_missing_functions_fail_at_construction() -> None:
    bdd = chain(
        [string("S")],
        [((Tag.CALL, "x.b", (Tag.CALL, "x.a", (Tag.REF, "S"))), None)],
        [endpoint("https://a"), error("no")],
    )
    with pytest.raises(EndpointResolutionError) as e:
        BddEndpointResolver(bdd)
    assert str(e.value).endswith(": x.a, x.b")


# --------------------------------------------------------------- BDD walks


def _walk(nodes: list[int]) -> dict[tuple[bool, bool], str]:
    """The result each pair of condition values reaches from node 2.

    Condition i tests boolean Pi, and result k is the error ``rk``.
    """
    bdd = assemble(
        [boolean(f"P{i}", required=True, default=False) for i in range(2)],
        [
            ((Tag.CALL, "booleanEquals", (Tag.REF, f"P{i}"), True), None)
            for i in range(2)
        ],
        [error("r1"), error("r2")],
        2,
        nodes,
    )
    resolver = BddEndpointResolver(bdd)
    reached: dict[tuple[bool, bool], str] = {}
    for bits in [(True, True), (True, False), (False, True), (False, False)]:
        with pytest.raises(EndpointResolutionError) as e:
            resolve(resolver, parameters={"P0": bits[0], "P1": bits[1]})
        reached[bits] = str(e.value)
    return reached


def test_complement_edges_swap_branches() -> None:
    # node 2: P0 ? node 3 : -node 3; node 3: P1 ? r1 : r2.
    assert _walk([-1, 1, -1, 0, 3, -3, 1, R + 1, R + 2]) == {
        (True, True): "r1",
        (True, False): "r2",
        (False, True): "r2",
        (False, False): "r1",
    }


def test_terminal_edges_mean_no_match() -> None:
    # node 2: P0 ? terminal : node 3; node 3: P1 ? r1 : -terminal.
    no_match = "No endpoint rule matched"
    assert _walk([-1, 1, -1, 0, 1, 3, 1, R + 1, -1]) == {
        (True, True): no_match,
        (True, False): no_match,
        (False, True): "r1",
        (False, False): no_match,
    }


# --------------------------------------------------------------- results


def _one(
    result: Any, extensions: list[RulesExtension] | None = None
) -> BddEndpointResolver:
    """A resolver whose rules always give one result."""
    return BddEndpointResolver(
        chain([string("S"), string("T")], [], [result]), extensions=extensions or []
    )


@pytest.mark.parametrize(
    "url, values, expected",
    [
        ("https://example.com", {}, URI(host="example.com")),
        (
            "https://{S}.example.com/p/{T}",
            {"S": "a", "T": "b"},
            URI(host="a.example.com", path="/p/b"),
        ),
        # A custom endpoint, with a port and a path.
        (
            (Tag.REF, "S"),
            {"S": "http://x.y:1/z"},
            URI(scheme="http", host="x.y", port=1, path="/z"),
        ),
    ],
)
def test_endpoint_urls(url: Any, values: dict[str, Any], expected: URI) -> None:
    assert resolve(_one(endpoint(url)), parameters=values).uri == expected


def test_custom_endpoint_paths_keep_their_prefix() -> None:
    url = "{url#scheme}://{url#authority}{url#normalizedPath}item"
    resolver = BddEndpointResolver(
        chain(
            [string("Endpoint", required=True)],
            [((Tag.CALL, "parseURL", "{Endpoint}"), "url")],
            [endpoint(url), error("no")],
        )
    )
    uri = resolve(resolver, parameters={"Endpoint": "http://localhost:9000/base"}).uri
    assert uri == URI(scheme="http", host="localhost", port=9000, path="/base/item")


def test_error_results_render_their_message() -> None:
    with pytest.raises(EndpointResolutionError, match=r"^Invalid region: a$"):
        resolve(_one(error("Invalid region: {S}")), parameters={"S": "a"})


def test_function_failures_are_resolution_errors() -> None:
    def broken(value: Any) -> Any:
        raise KeyError(value)

    resolver = BddEndpointResolver(
        chain(
            [string("S")],
            [((Tag.CALL, "x.broken", (Tag.REF, "S")), None)],
            [endpoint("https://a"), error("no")],
        ),
        extensions=[RulesExtension(functions={"x.broken": broken})],
    )
    with pytest.raises(EndpointResolutionError, match="KeyError") as e:
        resolve(resolver, parameters={"S": "s"})
    assert isinstance(e.value.__cause__, KeyError)


TOKEN = ShapeID("x.auth#token")
SIGNED = ShapeID("x.auth#signed")
AUTH = RulesExtension(auth_schemes={"token": TOKEN, "signed": SIGNED})


def test_endpoint_properties() -> None:
    properties = (
        Tag.MAP,
        ("authSchemes", "backend", "nested"),
        (
            Tag.LIST,
            (
                Tag.MAP,
                ("audience", "name", "scopes"),
                "service",
                "token",
                (Tag.LIST, "*"),
            ),
            # No extension maps this name, so the endpoint leaves it out.
            (Tag.MAP, ("name",), "x.unmapped"),
            (
                Tag.MAP,
                ("name", "region", "strict"),
                "signed",
                "{S}",
                True,
            ),
        ),
        "fast",
        (Tag.MAP, ("a", "b"), (Tag.LIST, 1, True), (Tag.MAP, ("c",), "d")),
    )
    headers = (("x-a", ("1", "{S}")),)
    endpoint_ = resolve(
        _one(endpoint("https://example.com", properties, headers), [AUTH]),
        parameters={"S": "us-west-2"},
    )
    assert [(s.scheme_id, dict(s.properties)) for s in endpoint_.auth_schemes] == [
        (TOKEN, {"audience": "service", "scopes": ("*",)}),
        (SIGNED, {"region": "us-west-2", "strict": True}),
    ]
    assert endpoint_.properties[ENDPOINT_HEADERS] == {"x-a": ("1", "us-west-2")}
    assert endpoint_.properties["backend"] == "fast"
    assert endpoint_.properties["nested"] == {"a": (1, True), "b": {"c": "d"}}


def test_rendered_urls_must_be_uris() -> None:
    with pytest.raises(EndpointResolutionError, match="Invalid endpoint URI"):
        resolve(_one(endpoint((Tag.REF, "S"))), parameters={"S": "example.com"})


def test_auth_schemes_no_extension_maps_fail() -> None:
    properties = (Tag.MAP, ("authSchemes",), (Tag.LIST, (Tag.MAP, ("name",), "token")))
    with pytest.raises(EndpointResolutionError, match="no extension provides: token"):
        resolve(_one(endpoint("https://example.com", properties)), parameters={})


# --------------------------------------------------------------- expressions


def _value_of(expression: Any, values: dict[str, Any]) -> Any:
    """Evaluate an expression by assigning it in a condition and returning it as a
    property; None if the condition doesn't hold."""
    resolver = BddEndpointResolver(
        chain(
            [
                string("S"),
                string("T"),
                boolean("B"),
                ("A", "stringArray", False, None, None, False),
            ],
            [(expression, "v")],
            [endpoint("https://h", (Tag.MAP, ("v",), (Tag.REF, "v"))), error("no")],
        ),
        extensions=[EXTRA],
    )
    try:
        return resolve(resolver, parameters={"S": "s", **values}).properties["v"]
    except EndpointResolutionError as e:
        if str(e) == "no":
            return None
        raise


@pytest.mark.parametrize(
    "expression, values, expected",
    [
        # Calls pass references, literals and nested calls in order.
        ((Tag.CALL, "x.parts", (Tag.REF, "S"), 1, True, "z"), {}, ("s", 1, True, "z")),
        ((Tag.CALL, "x.parts", (Tag.CALL, "x.parts", (Tag.REF, "S"))), {}, (("s",),)),
        ((Tag.CALL, "x.parts", (Tag.LIST, "a", (Tag.REF, "S"))), {}, (("a", "s"),)),
        ((Tag.CALL, "coalesce", (Tag.REF, "T"), (Tag.REF, "S")), {}, "s"),
        ((Tag.CALL, "ite", (Tag.REF, "B"), "yes", "no"), {"B": True}, "yes"),
        ((Tag.CALL, "ite", (Tag.REF, "B"), "yes", "no"), {"B": False}, "no"),
        # getAttr: keys, indexes, negative indexes, and misses.
        (
            (Tag.ATTR, (Tag.CALL, "parseURL", (Tag.REF, "S")), "authority"),
            {"S": "https://h:1"},
            "h:1",
        ),
        ((Tag.ATTR, (Tag.REF, "A"), "[0]"), {"A": ["x", "y"]}, "x"),
        ((Tag.ATTR, (Tag.REF, "A"), "[-1]"), {"A": ["x", "y"]}, "y"),
        ((Tag.ATTR, (Tag.REF, "A"), "[5]"), {"A": ["x", "y"]}, None),
        # Templates; escaped braces are literal.
        ("{S}-{A#[0]}", {"A": ["q"]}, "s-q"),
        ("a{{b}}c", {}, "a{b}c"),
        # A value that is set but empty still satisfies its condition.
        ((Tag.CALL, "uriEncode", (Tag.REF, "S")), {"S": ""}, ""),
    ],
)
def test_expressions(expression: Any, values: dict[str, Any], expected: Any) -> None:
    assert _value_of(expression, values) == expected


IS_IP = (Tag.ATTR, (Tag.CALL, "parseURL", (Tag.REF, "S")), "isIp")
SCHEME = (Tag.ATTR, (Tag.CALL, "parseURL", (Tag.REF, "S")), "scheme")


@pytest.mark.parametrize(
    "condition, values, expected",
    [
        # isSet considers presence, not truthiness.
        ((Tag.CALL, "isSet", (Tag.REF, "S")), {"S": ""}, True),
        ((Tag.CALL, "isSet", (Tag.REF, "T")), {}, False),
        ((Tag.CALL, "not", (Tag.CALL, "isSet", (Tag.REF, "T"))), {}, True),
        ((Tag.CALL, "booleanEquals", (Tag.REF, "B"), True), {"B": True}, True),
        ((Tag.CALL, "booleanEquals", (Tag.REF, "B"), True), {"B": False}, False),
        ((Tag.CALL, "stringEquals", (Tag.REF, "S"), "s"), {}, True),
        ((Tag.CALL, "stringEquals", (Tag.REF, "T"), "s"), {}, False),
        # A literal with braces is a template, so it's rendered, not compared as is.
        ((Tag.CALL, "stringEquals", (Tag.REF, "S"), "{T}"), {"T": "s"}, True),
        # An expression against a literal, as in getAttr(...) and coalesce(...).
        ((Tag.CALL, "booleanEquals", IS_IP, True), {"S": "https://1.2.3.4"}, True),
        (
            (
                Tag.CALL,
                "booleanEquals",
                (Tag.CALL, "coalesce", (Tag.REF, "B"), False),
                True,
            ),
            {},
            False,
        ),
        ((Tag.CALL, "stringEquals", SCHEME, "http"), {"S": "http://h"}, True),
        ((Tag.CALL, "stringEquals", SCHEME, "http"), {"S": "https://h"}, False),
        # coalesce of only unset values is unset.
        (
            (Tag.CALL, "isSet", (Tag.CALL, "coalesce", (Tag.REF, "T"), (Tag.REF, "T"))),
            {},
            False,
        ),
    ],
)
def test_conditions(condition: Any, values: dict[str, Any], expected: bool) -> None:
    resolver = BddEndpointResolver(
        chain(
            [string("S"), string("T"), boolean("B")],
            [(condition, None)],
            [endpoint("https://yes"), error("no")],
        )
    )
    try:
        resolve(resolver, parameters={"S": "s", **values})
        holds = True
    except EndpointResolutionError as e:
        assert str(e) == "no"
        holds = False
    assert holds is expected
