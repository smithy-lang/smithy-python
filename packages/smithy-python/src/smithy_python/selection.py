# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Resolution of the service and shapes that an artifact generates."""

from __future__ import annotations

from collections import deque
from typing import Final

from .exceptions import CodegenError, InvalidInvocationError
from .model import MIXIN_TRAIT, Model, Shape, ShapeID, ShapeType

TRAIT_DEFINITION: Final = "smithy.api#trait"
PRIVATE_TRAIT: Final = "smithy.api#private"

# Shapes carrying these traits describe the model rather than data and are
# never generated, even when the JSON AST includes them.
_EXCLUDED_TRAITS: Final = frozenset({TRAIT_DEFINITION, MIXIN_TRAIT})


def resolve_service(
    model: Model, requested: ShapeID | None, *, required: bool
) -> Shape | None:
    """Return the service to generate, or ``None`` when one is not needed.

    An explicitly requested service must exist and be a concrete service shape.
    When none is requested, a model containing exactly one concrete service uses
    it, a model with several is an error, and a model with none returns ``None``
    unless the artifact requires a service. Services marked ``@mixin`` are
    abstract and never candidates.
    """
    if requested is not None:
        shape = model.get(requested)
        if shape is None:
            raise InvalidInvocationError(f"Service not found in model: {requested}")
        if shape.type is not ShapeType.SERVICE:
            raise InvalidInvocationError(
                f"Expected a service shape, found {shape.type}: {requested}"
            )
        if shape.has_trait(MIXIN_TRAIT):
            raise InvalidInvocationError(
                f"Cannot generate a mixin service; select a service that uses it: "
                f"{requested}"
            )
        return shape

    services = tuple(
        service for service in model.services() if not service.has_trait(MIXIN_TRAIT)
    )
    if len(services) == 1:
        return services[0]
    if len(services) > 1:
        candidates = ", ".join(str(service.id) for service in services)
        raise InvalidInvocationError(
            f"The model contains multiple services; select one with --service: "
            f"{candidates}"
        )
    if required:
        raise InvalidInvocationError("The model does not contain a service")
    return None


def select_generated_shapes(model: Model) -> tuple[Shape, ...]:
    """Return the data shapes to generate, in modeled order.

    Every data shape in the model is a candidate; the set is not narrowed to a
    service closure. Prelude shapes, trait definitions, and mixins are never
    generated. Shapes marked ``@private`` are generated only when reachable from
    another generated shape, since they are not meant to be used directly but
    may still be targeted by public members.

    Raises :class:`CodegenError` when two selected shapes have case-insensitively
    equal names, since they cannot coexist in one Python module.
    """
    candidates = tuple(shape for shape in model if _is_candidate(shape))
    # Operations and services are not generated here, but shapes they reference
    # are, so they seed reachability alongside the public data shapes.
    roots = tuple(
        shape
        for shape in model
        if not shape.has_trait(PRIVATE_TRAIT) and not _is_excluded(shape)
    )
    reachable = _reachable_ids(model, roots)
    selected = tuple(
        shape
        for shape in candidates
        if not shape.has_trait(PRIVATE_TRAIT) or shape.id in reachable
    )
    _require_unique_names(selected)
    return selected


def _is_candidate(shape: Shape) -> bool:
    if shape.type.is_service_category or shape.id.is_prelude:
        return False
    return not _is_excluded(shape)


def _is_excluded(shape: Shape) -> bool:
    return any(shape.has_trait(trait) for trait in _EXCLUDED_TRAITS)


def _reachable_ids(model: Model, roots: tuple[Shape, ...]) -> set[ShapeID]:
    reachable: set[ShapeID] = set()
    queue = deque(root.id for root in roots)
    while queue:
        shape_id = queue.popleft().without_member()
        if shape_id in reachable:
            continue
        reachable.add(shape_id)
        if (shape := model.get(shape_id)) is not None:
            queue.extend(shape.references())
    return reachable


def _require_unique_names(shapes: tuple[Shape, ...]) -> None:
    by_name: dict[str, list[ShapeID]] = {}
    for shape in shapes:
        by_name.setdefault(shape.id.name.casefold(), []).append(shape.id)
    conflicts = [ids for ids in by_name.values() if len(ids) > 1]
    if conflicts:
        details = "; ".join(", ".join(map(str, ids)) for ids in conflicts)
        raise CodegenError(
            "Generated shape names must be case-insensitively unique. Rename the "
            "conflicting shapes with the renameShapes transform, or drop shapes not "
            f"connected to a service with the removeUnusedShapes transform: {details}"
        )
