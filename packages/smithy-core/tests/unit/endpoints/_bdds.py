# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Helpers for endpoint BDD tests."""

from collections.abc import Mapping, Sequence
from typing import Any

from smithy_core.endpoints import (
    ENDPOINT_PARAMETERS,
    STATIC_ENDPOINT_CONFIG,
    EndpointBdd,
    EndpointResolverParams,
)
from smithy_core.endpoints._types import Tag
from smithy_core.interfaces import Endpoint, EndpointResolver
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeType
from smithy_core.types import TypedProperties

RESULT_OFFSET = 100_000_000
"""The endpointBdd trait's offset for result references."""

# ----------------------------------------------------------------- resolving


class Config:
    """A client config with the given attributes."""

    endpoint_uri: Any = None

    def __init__(self, **values: Any) -> None:
        self.__dict__.update(values)


class Input:
    """An operation input with the given attributes."""

    def __init__(self, **values: Any) -> None:
        self.__dict__.update(values)


def make_operation(
    name: str = "Op",
    members: Mapping[str, tuple[Any, Mapping[str, Any] | int]] | None = None,
    traits: Mapping[str, Any] | None = None,
) -> APIOperation[Any, Any]:
    """An operation with input members ``{name: (target schema, member traits)}``."""
    members = members or {}
    input_schema = (
        ShapeType.STRUCTURE.value,
        "com.example",
        f"{name}Input",
        0,
        tuple(members),
        tuple(
            (target, member_traits or 0) for target, member_traits in members.values()
        ),
    )
    return APIOperation(
        static_schema=(
            ShapeType.OPERATION.value,
            "com.example",
            name,
            traits or 0,
            input_schema,
            -1,
            (),
        ),
    )


NO_BINDINGS = make_operation()
"""An operation without context parameters."""


def resolve(
    resolver: EndpointResolver,
    *,
    parameters: Mapping[str, Any] | None = None,
    config: Any = None,
    operation: APIOperation[Any, Any] = NO_BINDINGS,
    input: Any = None,
) -> Endpoint:
    """Resolve an endpoint for a call.

    :param parameters: Values by rules name, set under ``ENDPOINT_PARAMETERS``.
    :param config: The client config; one with no fields by default.
    """
    context = TypedProperties()
    context[STATIC_ENDPOINT_CONFIG] = Config() if config is None else config
    if parameters is not None:
        context[ENDPOINT_PARAMETERS] = parameters
    return resolver.resolve_endpoint(
        EndpointResolverParams(operation=operation, input=input, context=context)
    )


# ----------------------------------------------------------------- building BDDs


def call_names(value: Any, out: set[str]) -> None:
    if isinstance(value, tuple):
        items: tuple[Any, ...] = value  # pyright: ignore[reportUnknownVariableType]
        if items and items[0] == Tag.CALL:
            out.add(items[1])
        for v in items:
            call_names(v, out)


def assemble(
    parameters: Sequence[tuple[Any, ...]],
    conditions: Sequence[tuple[Any, ...]],
    results: Sequence[tuple[Any, ...]],
    root: int,
    nodes: Sequence[int],
) -> EndpointBdd:
    """Assemble a BDD, deriving its functions."""
    names: set[str] = set()
    call_names(tuple(conditions), names)
    call_names(tuple(results), names)
    return EndpointBdd(
        parameters=tuple(parameters),
        functions=tuple(sorted(names)),
        conditions=tuple(conditions),
        results=(None, *results),
        root=root,
        nodes=tuple(nodes),
    )


def chain(
    parameters: Sequence[tuple[Any, ...]],
    conditions: Sequence[tuple[Any, ...]],
    results: Sequence[tuple[Any, ...]],
) -> EndpointBdd:
    """A decision list: condition i true gives result i + 1; none gives the last."""
    assert len(results) == len(conditions) + 1
    nodes = [-1, 1, -1]
    n = len(conditions)
    for i in range(n):
        low = i + 3 if i + 1 < n else RESULT_OFFSET + n + 1
        nodes += [i, RESULT_OFFSET + i + 1, low]
    root = 2 if n else RESULT_OFFSET + 1
    return assemble(parameters, conditions, results, root, nodes)


def echo(parameters: Sequence[tuple[Any, ...]]) -> EndpointBdd:
    """A BDD whose one endpoint has each parameter's value as a property of its name."""
    names = tuple(name for name, *_ in parameters)
    properties = (Tag.MAP, names, *((Tag.REF, name) for name in names))
    return chain(parameters, [], [endpoint("https://example.com", properties)])


def string(name: str, required: bool = False, default: Any = None) -> tuple[Any, ...]:
    return (name, "string", required, default, None, None)


def boolean(name: str, required: bool = False, default: Any = None) -> tuple[Any, ...]:
    return (name, "boolean", required, default, None, None)


def endpoint(url: Any, properties: Any = None, headers: Any = ()) -> tuple[Any, ...]:
    return (Tag.ENDPOINT, url, properties, headers)


def error(message: Any) -> tuple[Any, ...]:
    return (Tag.ERROR, message)
