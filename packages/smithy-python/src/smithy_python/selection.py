# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Resolution of the service and shapes that an artifact generates."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Final

from .exceptions import CodegenError, InvalidInvocationError
from .model import MIXIN_TRAIT, Model, Shape, ShapeID, ShapeType

TRAIT_DEFINITION: Final = "smithy.api#trait"

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


@dataclass(frozen=True, slots=True)
class Selection:
    """The data shapes to generate and the ones left out."""

    shapes: tuple[Shape, ...]
    excluded: tuple[Shape, ...]


def select_generated_shapes(model: Model, service: Shape | None) -> Selection:
    """Return the data shapes to generate, in modeled order.

    With a service, the selection is the service closure: every data shape
    reachable from the service through its operations, resources, and members,
    which matches the surface every other Smithy generator produces. Data shapes
    in the model that are not connected to the service are reported as excluded.

    Without a service, every data shape in the model is selected. Names are then
    checked for case-insensitive uniqueness, which Smithy guarantees only within
    a service closure, since conflicting names cannot coexist in one module.

    Prelude shapes, trait definitions, and mixins are never generated.
    """
    candidates = tuple(shape for shape in model if _is_candidate(shape))
    if service is None:
        _require_unique_names(candidates)
        return Selection(shapes=candidates, excluded=())

    closure = _closure(model, service)
    shapes = tuple(shape for shape in candidates if shape.id in closure)
    excluded = tuple(shape for shape in candidates if shape.id not in closure)
    return Selection(shapes=shapes, excluded=excluded)


def _is_candidate(shape: Shape) -> bool:
    if shape.type.is_service_category or shape.id.is_prelude:
        return False
    return not any(shape.has_trait(trait) for trait in _EXCLUDED_TRAITS)


def _closure(model: Model, service: Shape) -> set[ShapeID]:
    closure: set[ShapeID] = set()
    queue = deque([service.id])
    while queue:
        shape_id = queue.popleft().without_member()
        if shape_id in closure:
            continue
        closure.add(shape_id)
        if (shape := model.get(shape_id)) is not None:
            queue.extend(shape.references())
    return closure


def _require_unique_names(shapes: tuple[Shape, ...]) -> None:
    by_name: dict[str, list[ShapeID]] = {}
    for shape in shapes:
        by_name.setdefault(shape.id.name.casefold(), []).append(shape.id)
    conflicts = [ids for ids in by_name.values() if len(ids) > 1]
    if conflicts:
        details = "; ".join(", ".join(map(str, ids)) for ids in conflicts)
        raise CodegenError(
            "Generated shape names must be case-insensitively unique. Rename the "
            f"conflicting shapes with the renameShapes transform: {details}"
        )
