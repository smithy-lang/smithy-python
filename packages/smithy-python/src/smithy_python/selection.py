# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Service and data-shape selection on a loaded semantic model."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from ._selector import Selector
from .exceptions import InvalidInvocationError, InvalidShapeIdError, ModelError
from .model import (
    DECLARATION_TYPES,
    MemberShape,
    Model,
    OperationShape,
    ResourceShape,
    ServiceShape,
    Shape,
    ShapeId,
    ShapeType,
)

__all__ = [
    "Selection",
    "Selector",
    "resolve_service",
    "select_shapes",
    "select_type_shapes",
]


@dataclass(frozen=True, slots=True)
class Selection:
    """Selected service and eligible data shapes in original model order."""

    service: ServiceShape | None
    shapes: tuple[Shape, ...]
    excluded_count: int
    """Eligible data shapes omitted by the service closure (zero without a service)."""


def resolve_service(
    model: Model, *, service_id: str | None = None, require_service: bool = False
) -> ServiceShape | None:
    """Resolve an absolute service ID or the sole non-mixin service.

    Invalid or ambiguous selections raise :class:`InvalidInvocationError`.
    """
    if service_id is not None:
        try:
            shape_id = ShapeId.from_string(service_id)
        except InvalidShapeIdError as error:
            raise InvalidInvocationError(f"--service: {error}") from error
        if shape_id.is_member:
            raise InvalidInvocationError(
                f"--service {service_id!r} is a member ID, not a service"
            )
        shape = model.find_shape(shape_id)
        if shape is None:
            raise InvalidInvocationError(f"--service {service_id!r} is not defined")
        if not isinstance(shape, ServiceShape):
            raise InvalidInvocationError(f"--service {service_id!r} is not a service")
        if shape.is_mixin:
            raise InvalidInvocationError(f"--service {service_id!r} is a mixin")
        return shape

    services = model.services()
    if len(services) > 1:
        candidates = ", ".join(str(service.id) for service in services)
        raise InvalidInvocationError(
            f"Multiple services found; select one with --service: {candidates}"
        )
    if services:
        return services[0]
    if require_service:
        raise InvalidInvocationError("Client generation requires a service")
    return None


def select_shapes(
    model: Model, *, service_id: str | None = None, require_service: bool = False
) -> Selection:
    """Select data for generation from an already loaded, flattened model.

    Service selection failures raise ``InvalidInvocationError``. Without a
    service, case-insensitive data-shape name conflicts raise ``ModelError``.
    This stage neither validates Smithy semantics nor writes output.
    """
    service = resolve_service(
        model, service_id=service_id, require_service=require_service
    )
    eligible = tuple(
        shape
        for shape in model.iter_shapes()
        if shape.type
        not in (
            ShapeType.SERVICE,
            ShapeType.OPERATION,
            ShapeType.RESOURCE,
            ShapeType.MEMBER,
        )
        and not shape.is_mixin
        and not shape.has_trait("trait")
    )
    if service is None:
        _check_names(eligible)
        return Selection(service=None, shapes=eligible, excluded_count=0)

    visited = _closure(model, service.id)
    selected = tuple(shape for shape in eligible if shape.id in visited)
    return Selection(
        service=service, shapes=selected, excluded_count=len(eligible) - len(selected)
    )


def select_type_shapes(
    model: Model,
    *,
    service_id: str | None = None,
    selector: Selector | None = None,
    generate_inputs_and_outputs: bool = False,
) -> Selection:
    """Select declarations and their schema dependencies for standalone types.

    Unlike client selection, this function never infers a service. A selector
    narrows declaration roots before their transitive member targets are added.
    """
    service = (
        resolve_service(model, service_id=service_id)
        if service_id is not None
        else None
    )
    declarations = tuple(
        shape
        for shape in model.iter_shapes()
        if shape.type in DECLARATION_TYPES
        and not shape.is_mixin
        and not shape.has_trait("trait")
        and not shape.has_trait("private")
    )
    if service is None:
        candidates = declarations
        excluded_count = 0
    else:
        closure = _closure(model, service.id)
        candidates = tuple(shape for shape in declarations if shape.id in closure)
        excluded_count = len(declarations) - len(candidates)

    resolved_selector = selector or Selector.identity()
    selected_ids = (
        frozenset(shape.id for shape in candidates)
        if resolved_selector.is_identity
        else resolved_selector.select(model)
    )
    operation_inputs_and_outputs = {
        shape_id
        for operation in model.iter_shapes(OperationShape)
        for shape_id in (operation.input, operation.output)
    }
    roots = tuple(
        shape
        for shape in candidates
        if shape.id in selected_ids
        and (
            generate_inputs_and_outputs
            or (
                shape.id not in operation_inputs_and_outputs
                and not shape.has_trait("input")
                and not shape.has_trait("output")
            )
        )
    )

    closure = {shape.id for shape in roots}
    pending = list(closure)
    while pending:
        shape = model.get_shape(pending.pop())
        for member in shape.members.values():
            target = model.get_shape(member.target)
            if (
                model.is_prelude(target)
                or target.id in closure
                or target.is_mixin
                or target.has_trait("trait")
                or target.type
                in {
                    ShapeType.SERVICE,
                    ShapeType.OPERATION,
                    ShapeType.RESOURCE,
                    ShapeType.MEMBER,
                }
            ):
                continue
            closure.add(target.id)
            pending.append(target.id)

    shapes = tuple(shape for shape in model.iter_shapes() if shape.id in closure)
    _check_names(
        tuple(shape for shape in shapes if shape.type in DECLARATION_TYPES),
        service=service,
    )
    return Selection(service=service, shapes=shapes, excluded_count=excluded_count)


def _closure(model: Model, root: ShapeId) -> set[ShapeId]:
    visited: set[ShapeId] = set()
    pending = [root]
    while pending:
        shape_id = pending.pop()
        if shape_id in visited:
            continue
        visited.add(shape_id)
        pending.extend(_references(model.get_shape(shape_id)))
    return visited


def _references(shape: Shape) -> Iterator[ShapeId]:
    # Only semantic relationships are edges, never trait nodes, rename entries,
    # or mixin declarations (the loader has already flattened their contents).
    for member in shape.members.values():
        yield member.target
    if isinstance(shape, MemberShape):
        yield shape.target
    elif isinstance(shape, ServiceShape):
        yield from shape.operations
        yield from shape.resources
        yield from shape.errors
    elif isinstance(shape, OperationShape):
        yield shape.input
        yield shape.output
        yield from shape.errors
    elif isinstance(shape, ResourceShape):
        yield from shape.identifiers.values()
        yield from shape.properties.values()
        for operation in (
            shape.create,
            shape.put,
            shape.read,
            shape.update,
            shape.delete,
            shape.list,
        ):
            if operation is not None:
                yield operation
        yield from shape.operations
        yield from shape.collection_operations
        yield from shape.resources


def _check_names(
    shapes: tuple[Shape, ...], *, service: ServiceShape | None = None
) -> None:
    by_name: dict[str, list[ShapeId]] = {}
    for shape in shapes:
        name = service.rename.get(shape.id, shape.id.name) if service else shape.id.name
        by_name.setdefault(name.casefold(), []).append(shape.id)
    conflicts = [ids for ids in by_name.values() if len(ids) > 1]
    if conflicts:
        details = "; ".join(
            ", ".join(str(shape_id) for shape_id in ids) for ids in conflicts
        )
        raise ModelError(f"Case-insensitive data shape name conflicts: {details}")
