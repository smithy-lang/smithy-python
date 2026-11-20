# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Planning of the ``paginate_*`` methods of generated clients."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from . import exceptions as _exceptions
from . import model as _model
from .symbols import (
    _CLIENT_METHOD_NAMES,  # pyright: ignore[reportPrivateUsage]
    TypeReference,
)

if TYPE_CHECKING:
    from .clients import ClientPlan

__all__ = ["PaginatorPlan", "plan_paginators"]


@dataclass(frozen=True, slots=True)
class PaginatorPlan:
    """The generated description of one operation's effective paginated trait.

    Member names are the generated Python names, not Smithy member names.
    """

    method_name: str
    # Member names, not tokens, but left out of the repr like any token field.
    input_token: str = field(repr=False)
    output_token: tuple[str, ...] = field(repr=False)
    items: tuple[str, ...] | None
    item_type: TypeReference | None


def plan_paginators(plan: ClientPlan) -> tuple[PaginatorPlan | None, ...]:
    """Plan a paginator for each operation of the client that has one.

    The result is parallel to ``plan.operations``.

    :raises CodegenError: Naming the operation, if its effective paginated trait
        lacks a token, a token or items path can't be resolved to a supported
        member, or its input and output tokens target different types.
    """
    service = plan.selection.service
    assert service is not None  # noqa: S101 - ClientPlan requires a service
    defaults = _settings(service)
    names = _allocate_names(plan)
    return tuple(
        _plan(plan, operation.operation, names[operation.operation.id], defaults)
        if operation.operation.id in names
        else None
        for operation in plan.operations
    )


_PAGINATED: Final = _model.ShapeId("smithy.api", "paginated")
_PREFIX: Final = "paginate_"
_TOKEN_TYPES: Final = (_model.ShapeType.STRING, _model.ShapeType.MAP)


def _settings(shape: _model.Shape) -> Mapping[str, _model.Node]:
    value = shape.get_trait(_PAGINATED) if shape.has_trait(_PAGINATED) else None
    return value if isinstance(value, Mapping) else {}


def _allocate_names(plan: ClientPlan) -> dict[_model.ShapeId, str]:
    """Name each paginator ``paginate_`` plus its operation's method name.

    Operation names never change. A paginator name that is taken by an operation
    or client member gets underscores until it is free of those and of every
    other paginator's preferred name, so names don't depend on operation order.
    """
    preferred = {
        operation.operation.id: _PREFIX + operation.method_name
        for operation in plan.operations
        if operation.operation.has_trait(_PAGINATED)
    }
    taken = {operation.method_name for operation in plan.operations}
    taken |= _CLIENT_METHOD_NAMES
    reserved = taken | set(preferred.values())
    names: dict[_model.ShapeId, str] = {}
    for shape_id, name in preferred.items():
        if name not in taken:
            names[shape_id] = name
            continue
        while name in reserved:
            name += "_"
        reserved.add(name)
        names[shape_id] = name
    return names


def _plan(
    plan: ClientPlan,
    operation: _model.OperationShape,
    name: str,
    defaults: Mapping[str, _model.Node],
) -> PaginatorPlan:
    settings = {**defaults, **_settings(operation)}
    input_token = settings.get("inputToken")
    output_token = settings.get("outputToken")
    if not isinstance(input_token, str) or not isinstance(output_token, str):
        raise _exceptions.CodegenError(
            f"Paginated operation {operation.id} needs an inputToken and an "
            "outputToken, from its paginated trait or its service's"
        )
    model = plan.model
    input_shape = model.get_shape(operation.input)
    member = input_shape.members.get(input_token)
    if member is None:
        raise _exceptions.CodegenError(
            f"Paginated operation {operation.id} names inputToken {input_token!r}, "
            f"which is not a member of {input_shape.id}"
        )
    input_target = model.get_target(member)
    if input_target.type not in _TOKEN_TYPES:
        raise _exceptions.CodegenError(
            f"Paginated operation {operation.id} has inputToken {input_token!r} "
            f"targeting a {input_target.type}, but only string and map tokens are "
            "supported"
        )
    token_names, token = _resolve(plan, operation, "outputToken", output_token)
    if token.type not in _TOKEN_TYPES:
        raise _exceptions.CodegenError(
            f"Paginated operation {operation.id} has outputToken {output_token!r} "
            f"targeting a {token.type}, but only string and map tokens are supported"
        )
    # Each output token is sent as the next input token, unconverted.
    if input_target.type != token.type:
        raise _exceptions.CodegenError(
            f"Paginated operation {operation.id} has inputToken {input_token!r} "
            f"targeting a {input_target.type}, but outputToken {output_token!r} "
            f"targets a {token.type}"
        )
    items = settings.get("items")
    item_names: tuple[str, ...] | None = None
    item_type: TypeReference | None = None
    if isinstance(items, str):
        item_names, collection = _resolve(plan, operation, "items", items)
        if not isinstance(collection, _model.ListShape | _model.MapShape):
            raise _exceptions.CodegenError(
                f"Paginated operation {operation.id} has items {items!r} targeting "
                f"a {collection.type}, but items must be a list or a map"
            )
        arguments = plan.symbols.type_reference(collection.id).arguments
        item_type = (
            arguments[0]
            if isinstance(collection, _model.ListShape)
            else TypeReference("tuple", "builtins", arguments)
        )
    return PaginatorPlan(
        method_name=name,
        input_token=plan.symbols.member_name(member.id),
        output_token=token_names,
        items=item_names,
        item_type=item_type,
    )


def _resolve(
    plan: ClientPlan, operation: _model.OperationShape, setting: str, path: str
) -> tuple[tuple[str, ...], _model.Shape]:
    """Return a dotted output path's Python member names, and its target."""
    shape = plan.model.get_shape(operation.output)
    names: list[str] = []
    for segment in path.split("."):
        member = (
            shape.members.get(segment)
            if isinstance(shape, _model.StructureShape)
            else None
        )
        if member is None:
            raise _exceptions.CodegenError(
                f"Paginated operation {operation.id} has {setting} {path!r}, but "
                f"{segment!r} is not a member of the structure {shape.id}"
            )
        names.append(plan.symbols.member_name(member.id))
        shape = plan.model.get_target(member)
    return tuple(names), shape
