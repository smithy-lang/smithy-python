# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""The loaded model and its navigation API."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from types import MappingProxyType
from typing import overload

from ..exceptions import ModelError, ShapeNotFoundError
from ._shape_id import PRELUDE_NAMESPACE, ShapeId, as_shape_id
from ._shapes import MemberShape, Node, ServiceShape, Shape, ShapeType


class Model:
    """A loaded, mixin-flattened Smithy model.

    ``shapes`` holds top-level shapes (never members) in input order followed
    by any embedded prelude shapes the input did not define. Members are
    reachable via their container or ``get_shape`` with a member ID.
    """

    __slots__ = ("_metadata", "_shapes", "_smithy_version")

    def __init__(
        self,
        *,
        smithy_version: str,
        metadata: Mapping[str, Node],
        shapes: Mapping[ShapeId, Shape],
    ) -> None:
        self._smithy_version = smithy_version
        self._metadata: Mapping[str, Node] = MappingProxyType(dict(metadata))
        self._shapes: Mapping[ShapeId, Shape] = MappingProxyType(dict(shapes))

    @property
    def smithy_version(self) -> str:
        """The ``smithy`` version string from the JSON AST."""
        return self._smithy_version

    @property
    def metadata(self) -> Mapping[str, Node]:
        """Model metadata in input key order."""
        return self._metadata

    @property
    def shapes(self) -> Mapping[ShapeId, Shape]:
        """All top-level shapes, including prelude shapes."""
        return self._shapes

    def __contains__(self, shape_id: object) -> bool:
        if isinstance(shape_id, str):
            try:
                shape_id = as_shape_id(shape_id)
            except ModelError:
                return False
        return isinstance(shape_id, ShapeId) and self.find_shape(shape_id) is not None

    def find_shape(self, shape_id: ShapeId | str) -> Shape | None:
        """Return the shape (or member) with this ID, or None."""
        shape_id = as_shape_id(shape_id)
        shape = self._shapes.get(shape_id.root)
        if shape is None or shape_id.member is None:
            return shape
        return shape.members.get(shape_id.member)

    def get_shape(self, shape_id: ShapeId | str) -> Shape:
        """Return the shape (or member) with this ID or raise ShapeNotFoundError."""
        shape = self.find_shape(shape_id)
        if shape is None:
            raise ShapeNotFoundError(f"Shape {shape_id} is not defined in the model")
        return shape

    def expect_shape[T: Shape](self, shape_id: ShapeId | str, kind: type[T]) -> T:
        """Return the shape with this ID, requiring it to be a ``kind``."""
        shape = self.get_shape(shape_id)
        if not isinstance(shape, kind):
            raise ModelError(
                f"Shape {shape_id} is a {type(shape).__name__}; "
                f"expected {kind.__name__}"
            )
        return shape

    def get_target(self, member: MemberShape) -> Shape:
        """Return the shape a member targets."""
        return self.get_shape(member.target)

    def is_prelude(self, shape: Shape | ShapeId) -> bool:
        """Whether a shape belongs to the Smithy prelude (never generated)."""
        shape_id = shape if isinstance(shape, ShapeId) else shape.id
        return shape_id.namespace == PRELUDE_NAMESPACE

    @overload
    def iter_shapes(
        self, kind: None = None, *, include_prelude: bool = False
    ) -> Iterator[Shape]: ...

    @overload
    def iter_shapes[T: Shape](
        self, kind: type[T], *, include_prelude: bool = False
    ) -> Iterator[T]: ...

    @overload
    def iter_shapes(
        self, kind: ShapeType, *, include_prelude: bool = False
    ) -> Iterator[Shape]: ...

    def iter_shapes(
        self,
        kind: type[Shape] | ShapeType | None = None,
        *,
        include_prelude: bool = False,
    ) -> Iterator[Shape]:
        """Iterate top-level shapes in model order, optionally filtered.

        ``kind`` may be a shape class or a ShapeType. Prelude shapes are
        skipped unless ``include_prelude`` is set. Mixin shapes are included;
        filter with ``Shape.is_mixin``.
        """
        for shape in self._shapes.values():
            if not include_prelude and self.is_prelude(shape):
                continue
            if kind is None:
                yield shape
            elif isinstance(kind, ShapeType):
                if shape.type is kind:
                    yield shape
            elif isinstance(shape, kind):
                yield shape

    def services(self) -> tuple[ServiceShape, ...]:
        """All non-mixin service shapes in model order."""
        return tuple(s for s in self.iter_shapes(ServiceShape) if not s.is_mixin)
