# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from typing import Protocol

from .model import Model, Shape, ShapeID


class ShapeFilter(Protocol):
    """Selects the ordered shapes that a generator should emit."""

    def select(self, model: Model) -> tuple[Shape, ...]: ...


class AllShapes:
    def __init__(self, predicate: Callable[[Shape], bool] | None = None) -> None:
        self._predicate: Callable[[Shape], bool] = predicate or _include_all

    def select(self, model: Model) -> tuple[Shape, ...]:
        return tuple(shape for shape in model if self._predicate(shape))


class ConnectedShapeFilter:
    """Selects the transitive closure of structural references from root shapes."""

    def __init__(
        self,
        roots: Iterable[ShapeID | str],
        *,
        include: Iterable[ShapeID | str] = (),
        predicate: Callable[[Shape], bool] | None = None,
    ) -> None:
        self._roots = tuple(_shape_id(root) for root in roots)
        self._include = tuple(_shape_id(shape) for shape in include)
        self._predicate: Callable[[Shape], bool] = predicate or _include_all

    def select(self, model: Model) -> tuple[Shape, ...]:
        selected: set[ShapeID] = set()
        queue = deque((*self._roots, *self._include))
        while queue:
            shape_id = queue.popleft().without_member()
            if shape_id in selected:
                continue
            shape = model.expect(shape_id)
            selected.add(shape_id)
            queue.extend(reference for reference in shape.references())
        return tuple(
            shape for shape in model if shape.id in selected and self._predicate(shape)
        )


def _shape_id(value: ShapeID | str) -> ShapeID:
    return ShapeID.parse(value) if isinstance(value, str) else value


def _include_all(_shape: Shape) -> bool:
    return True
