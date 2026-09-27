# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Python names and symbolic type references for an already selected model."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace

from .model import (
    ListShape,
    MapShape,
    MemberShape,
    Model,
    ModelError,
    Shape,
    ShapeId,
    ShapeType,
)
from .selection import Selection

# Python 3.12 hard keywords, deliberately independent of the host interpreter.
# Soft keywords (match, case, type, _) remain ordinary identifiers here.
_KEYWORDS = frozenset(
    "False None True and as assert async await break class continue def del "
    "elif else except finally for from global if import in is lambda nonlocal "
    "not or pass raise return try while with yield".split()
)
_ENUMS = frozenset({ShapeType.ENUM, ShapeType.INT_ENUM})
_NAMED = _ENUMS | {ShapeType.STRUCTURE, ShapeType.UNION}


@dataclass(frozen=True, slots=True)
class TypeReference:
    """A symbolic name, its defining module, and ordered generic arguments.

    ``module=None`` denotes the None literal. ``nullable`` permits None in
    addition to this reference, and is used only for sparse collection entries.
    No imports or annotation rendering are performed.
    """

    name: str
    module: str | None = None
    arguments: tuple[TypeReference, ...] = ()
    nullable: bool = False


_PRIMITIVES = {
    ShapeType.BOOLEAN: TypeReference("bool", "builtins"),
    ShapeType.STRING: TypeReference("str", "builtins"),
    ShapeType.ENUM: TypeReference("str", "builtins"),
    ShapeType.INT_ENUM: TypeReference("int", "builtins"),
    **dict.fromkeys(
        (
            ShapeType.BYTE,
            ShapeType.SHORT,
            ShapeType.INTEGER,
            ShapeType.LONG,
            ShapeType.BIG_INTEGER,
        ),
        TypeReference("int", "builtins"),
    ),
    ShapeType.FLOAT: TypeReference("float", "builtins"),
    ShapeType.DOUBLE: TypeReference("float", "builtins"),
    ShapeType.BLOB: TypeReference("bytes", "builtins"),
    ShapeType.BIG_DECIMAL: TypeReference("Decimal", "decimal"),
    ShapeType.TIMESTAMP: TypeReference("datetime", "datetime"),
    ShapeType.DOCUMENT: TypeReference("Document", "smithy_core.documents"),
}


def _name(value: str, *, pascal: bool = False, constant: bool = False) -> str:
    if pascal:
        result = "".join(word[:1].upper() + word[1:] for word in value.split("_"))
    else:
        value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
        value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
        result = "_".join(word.lower() for word in value.split("_") if word)
    if constant:
        result = result.upper()
    if result[:1].isdigit():
        result = "_" + result
    if result in _KEYWORDS:
        result += "_"
    return result


class SymbolProvider:
    """Naming for selected data shapes; IDs and wire names are never modified."""

    def __init__(self, model: Model, selection: Selection, *, package: str) -> None:
        if any(
            not part.isidentifier() or unicodedata.normalize("NFKC", part) in _KEYWORDS
            for part in package.split(".")
        ):
            raise ValueError(f"Invalid Python package name: {package!r}")
        self._model = model
        self._selection = selection
        self._package = package
        self._selected = frozenset(shape.id for shape in selection.shapes)
        declarations: dict[str, ShapeId] = {}
        for shape in selection.shapes:
            if shape.type not in _NAMED or shape.has_trait("streaming"):
                continue
            self._check_collision(
                declarations, self.declaration_name(shape.id), shape.id
            )
            members: dict[str, ShapeId] = {}
            for member in shape.members.values():
                self._check_collision(members, self.member_name(member.id), member.id)

    @staticmethod
    def _check_collision(
        scope: dict[str, ShapeId], name: str, shape_id: ShapeId
    ) -> None:
        if name in scope:
            raise ModelError(
                f"Python name collision {name!r}: {scope[name]}, {shape_id}"
            )
        scope[name] = shape_id

    def _shape(self, shape_id: ShapeId | str) -> Shape:
        shape = self._model.get_shape(shape_id)
        if shape.id.root not in self._selected and not self._model.is_prelude(shape):
            raise ModelError(f"Shape {shape.id} is not selected")
        if (
            shape.is_mixin
            or shape.has_trait("trait")
            or shape.type
            in (ShapeType.SERVICE, ShapeType.OPERATION, ShapeType.RESOURCE)
        ):
            raise ModelError(f"No data symbol for {shape.id} ({shape.type})")
        if shape.type in (ShapeType.BLOB, ShapeType.UNION) and shape.has_trait(
            "streaming"
        ):
            raise ModelError(f"Unsupported streaming {shape.type}: {shape.id}")
        return shape

    def declaration_name(self, shape_id: ShapeId | str) -> str:
        """Return a generated type's PascalCase name; aliases have no declaration."""
        shape = self._shape(shape_id)
        if shape.type not in _NAMED or self._model.is_prelude(shape):
            raise ModelError(f"No generated declaration for {shape.id}")
        service = self._selection.service
        name = service.rename.get(shape.id, shape.id.name) if service else shape.id.name
        result = _name(name, pascal=True)
        if not re.fullmatch(r"[A-Za-z0-9_]+", name) or not result.isidentifier():
            raise ModelError(
                f"Invalid Python declaration name {result!r} for {shape.id}"
            )
        return result

    def type_reference(self, shape_id: ShapeId | str) -> TypeReference:
        """Resolve a value type; enums use str/int to permit unknown values."""
        root = self._model.get_shape(shape_id).id
        resolved: dict[ShapeId, TypeReference] = {}
        active: dict[ShapeId, None] = {}
        pending = [(root, False)]
        while pending:
            current, expanded = pending.pop()
            if current in resolved:
                continue
            shape = self._shape(current)
            if isinstance(shape, MemberShape):
                raise ModelError(
                    f"Type references require a target, not member ID {current}"
                )
            if isinstance(shape, (ListShape, MapShape)):
                targets = (
                    (shape.member.target,)
                    if isinstance(shape, ListShape)
                    else (shape.key.target, shape.value.target)
                )
                if expanded:
                    arguments = tuple(resolved[target] for target in targets)
                    if shape.has_trait("sparse"):
                        arguments = (
                            *arguments[:-1],
                            replace(arguments[-1], nullable=True),
                        )
                    resolved[current] = TypeReference(
                        "list" if isinstance(shape, ListShape) else "dict",
                        "builtins",
                        arguments,
                    )
                    del active[current]
                else:
                    if current in active:
                        cycle = list(active)
                        cycle = [*cycle[cycle.index(current) :], current]
                        path = " -> ".join(str(item) for item in cycle)
                        raise ModelError(f"Collection-only cycle: {path}")
                    active[current] = None
                    pending.append((current, True))
                    pending.extend((target, False) for target in reversed(targets))
            elif current == ShapeId("smithy.api", "Unit"):
                resolved[current] = TypeReference("None")
            elif shape.type in (ShapeType.STRUCTURE, ShapeType.UNION):
                resolved[current] = TypeReference(
                    self.declaration_name(current), f"{self._package}.models"
                )
            elif shape.type in _PRIMITIVES:
                resolved[current] = _PRIMITIVES[shape.type]
            else:
                raise ModelError(
                    f"No Python type reference for {current} ({shape.type})"
                )
        return resolved[root]

    def member_name(self, shape_id: ShapeId | str) -> str:
        """Return a field name or an enum constant, not a wire name."""
        member = self._shape(shape_id)
        if not isinstance(member, MemberShape):
            raise ModelError(f"Member naming requires a member ID: {member.id}")
        container = self._shape(member.container)
        if container.type not in _NAMED or self._model.is_prelude(container):
            raise ModelError(f"No generated member name for {member.id}")
        return _name(member.name, constant=container.type in _ENUMS)
