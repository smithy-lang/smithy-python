# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Python names and symbolic type references for an already selected model."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Collection
from dataclasses import dataclass, replace

from . import dependencies as _dependencies
from .model import (
    DECLARATION_TYPES,
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

__all__ = ["SymbolProvider", "TypeReference"]


@dataclass(frozen=True, slots=True)
class TypeReference:
    """A symbolic name, its public module, and ordered generic arguments.

    ``module=None`` denotes the None literal. ``nullable`` permits None in
    addition to this reference, and is used only for sparse collection entries.
    Dependencies are recorded when a writer consumes the reference. No imports
    or annotation rendering are performed here.
    """

    name: str
    module: str | None = None
    arguments: tuple[TypeReference, ...] = ()
    nullable: bool = False
    dependencies: tuple[_dependencies.Dependency, ...] = ()


class SymbolProvider:
    """Naming for selected data shapes; IDs and wire names are never modified."""

    def __init__(
        self,
        model: Model,
        selection: Selection,
        *,
        package: str,
        reserved_member_names: Callable[[Shape], Collection[str]] | None = None,
    ) -> None:
        if not _DISTRIBUTION_NAME.fullmatch(package) or any(
            not part.isidentifier() or unicodedata.normalize("NFKC", part) in _KEYWORDS
            for part in package.split(".")
        ):
            raise ValueError(
                f"Invalid Python package or distribution name: {package!r}"
            )
        self._model = model
        self._selection = selection
        self._package = package
        self._reserved_member_names: dict[ShapeId, frozenset[str]] = {}
        self._type_references: dict[ShapeId, TypeReference] = {}
        self._declaration_names: dict[ShapeId, str] = {}
        self._schema_names = _plan_schema_names(selection)
        self._union_variant_names: dict[ShapeId, str] = {}
        self._union_unknown_names: dict[ShapeId, str] = {}
        self._selected = frozenset(shape.id for shape in selection.shapes)
        self._reserved_declarations = _RESERVED_DECLARATIONS
        if any(
            shape.type not in _ENUMS
            and any(member.target == _UNIT for member in shape.members.values())
            for shape in selection.shapes
        ):
            self._reserved_declarations |= {"Unit"}
        self._shape_names: frozenset[str] = frozenset()
        declarations: dict[str, ShapeId] = {}
        for shape in selection.shapes:
            if shape.type not in DECLARATION_TYPES:
                continue
            self._check_collision(
                declarations, self.declaration_name(shape.id), shape.id
            )
            if reserved_member_names:
                self._reserved_member_names[shape.id] = frozenset(
                    reserved_member_names(shape)
                )
            members: dict[str, ShapeId] = {}
            for member in shape.members.values():
                self._check_collision(members, self.member_name(member.id), member.id)
        self._shape_names = frozenset((*declarations, *self._reserved_declarations))
        for shape in selection.shapes:
            if shape.type is not ShapeType.UNION:
                continue
            for member in shape.members.values():
                self._check_collision(
                    declarations, self.union_variant_name(member.id), member.id
                )
            self._check_collision(
                declarations, self.union_unknown_name(shape.id), shape.id
            )

    def declaration_name(self, shape_id: ShapeId | str) -> str:
        """Return a generated type's PascalCase name; aliases have no declaration."""
        shape = self._shape(shape_id)
        cached = self._declaration_names.get(shape.id)
        if cached is not None:
            return cached
        if shape.type not in DECLARATION_TYPES or self._model.is_prelude(shape):
            raise ModelError(f"No generated declaration for {shape.id}")
        service = self._selection.service
        name = service.rename.get(shape.id, shape.id.name) if service else shape.id.name
        result = _name(name, pascal=True, reserved=self._reserved_declarations)
        if not re.fullmatch(r"[A-Za-z0-9_]+", name) or not result.isidentifier():
            raise ModelError(
                f"Invalid Python declaration name {result!r} for {shape.id}"
            )
        self._declaration_names[shape.id] = result
        return result

    def schema_name(self, shape_id: ShapeId | str) -> str:
        """Return the module-level compact schema constant name."""
        shape = self._selected_shape(shape_id)
        if (
            shape.id.is_member
            or shape.is_mixin
            or shape.has_trait("trait")
            or shape.type
            in (ShapeType.SERVICE, ShapeType.OPERATION, ShapeType.RESOURCE)
        ):
            raise ModelError(f"No data schema for {shape.id} ({shape.type})")
        cached = self._schema_names.get(shape.id)
        if cached is not None:
            return cached
        if self._model.is_prelude(shape):
            return _name(shape.id.name, constant=True)
        raise ModelError(f"No schema name planned for {shape.id}")

    def union_variant_name(self, shape_id: ShapeId | str) -> str:
        """Return the generated class name for a union member."""
        member = self._shape(shape_id)
        if not isinstance(member, MemberShape):
            raise ModelError(f"Union variant naming requires a member ID: {member.id}")
        cached = self._union_variant_names.get(member.id)
        if cached is not None:
            return cached
        container = self._shape(member.container)
        if container.type is not ShapeType.UNION:
            raise ModelError(f"{member.id} is not a union member")
        container_name = self.declaration_name(container.id)
        capitalized = member.name[:1].upper() + member.name[1:]
        result = container_name + capitalized
        if result in self._shape_names:
            result = container_name + "_" + capitalized
        self._union_variant_names[member.id] = result
        return result

    def union_unknown_name(self, shape_id: ShapeId | str) -> str:
        """Return the generated unknown-variant class name for a union."""
        shape = self._shape(shape_id)
        cached = self._union_unknown_names.get(shape.id)
        if cached is not None:
            return cached
        if shape.type is not ShapeType.UNION:
            raise ModelError(f"{shape.id} is not a union")
        container_name = self.declaration_name(shape.id)
        result = container_name + "Unknown"
        if result in self._shape_names:
            result = container_name + "_Unknown"
        self._union_unknown_names[shape.id] = result
        return result

    def type_reference(self, shape_id: ShapeId | str) -> TypeReference:
        """Resolve a value type; enums use str/int to permit unknown values."""
        root = self._model.get_shape(shape_id).id
        # Entries are complete references, so a failed walk leaves the cache valid.
        resolved = self._type_references
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
                    arguments = tuple(self.type_reference(target) for target in targets)
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
                resolved[current] = TypeReference("Unit", f"{self._package}.models")
            elif shape.type in (ShapeType.STRUCTURE, ShapeType.UNION):
                resolved[current] = TypeReference(
                    self.declaration_name(current), f"{self._package}.models"
                )
            elif shape.type is ShapeType.BLOB and shape.has_trait("streaming"):
                resolved[current] = _STREAMING_BLOB
            elif shape.type in _FIXED_TYPES:
                resolved[current] = _FIXED_TYPES[shape.type]
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
        if container.type not in DECLARATION_TYPES or self._model.is_prelude(container):
            raise ModelError(f"No generated member name for {member.id}")
        return _name(
            member.name,
            constant=container.type in _ENUMS,
            preserve_underscores=True,
            reserved=self._reserved_member_names.get(container.id, ()),
        )

    @staticmethod
    def _check_collision(
        scope: dict[str, ShapeId], name: str, shape_id: ShapeId
    ) -> None:
        if name in scope:
            raise ModelError(
                f"Python name collision {name!r}: {scope[name]}, {shape_id}"
            )
        scope[name] = shape_id

    def _selected_shape(self, shape_id: ShapeId | str) -> Shape:
        shape = self._model.get_shape(shape_id)
        if shape.id.root not in self._selected and not self._model.is_prelude(shape):
            raise ModelError(f"Shape {shape.id} is not selected")
        return shape

    def _shape(self, shape_id: ShapeId | str) -> Shape:
        shape = self._selected_shape(shape_id)
        if (
            shape.is_mixin
            or shape.has_trait("trait")
            or shape.type
            in (ShapeType.SERVICE, ShapeType.OPERATION, ShapeType.RESOURCE)
        ):
            raise ModelError(f"No data symbol for {shape.id} ({shape.type})")
        return shape


# Union of Python 3.12-3.15 hard keywords, independent of the host interpreter.
# Soft keywords (match, case, type, lazy, _) remain ordinary identifiers here.
# Update this when adding support for another Python version.
_KEYWORDS = frozenset(
    "False None True and as assert async await break class continue def del "
    "elif else except finally for from global if import in is lambda nonlocal "
    "not or pass raise return try while with yield".split()
)
_ENUMS = frozenset({ShapeType.ENUM, ShapeType.INT_ENUM})
_RESERVED_DECLARATIONS = frozenset({"ServiceError"})
_UNIT = ShapeId("smithy.api", "Unit")
_DISTRIBUTION_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")
_ACRONYM_BOUNDARY = re.compile(r"([A-Z]+)([A-Z][a-z])")
_WORD_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")

_STREAMING_BLOB = TypeReference(
    "StreamingBlob",
    "smithy_core.aio.interfaces",
    dependencies=(_dependencies.SMITHY_CORE,),
)

# Types whose reference never depends on the shape: Smithy's simple types, with
# enums widened to str/int so unknown values remain representable.
_FIXED_TYPES = {
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
    ShapeType.DOCUMENT: TypeReference(
        "Document", "smithy_core.documents", dependencies=(_dependencies.SMITHY_CORE,)
    ),
}


def _name(
    value: str,
    *,
    pascal: bool = False,
    constant: bool = False,
    preserve_underscores: bool = False,
    reserved: Collection[str] = (),
) -> str:
    if pascal:
        result = "".join(word[:1].upper() + word[1:] for word in value.split("_"))
    else:
        value = _ACRONYM_BOUNDARY.sub(r"\1_\2", value)
        value = _WORD_BOUNDARY.sub(r"\1_\2", value)
        result = (
            value.lower()
            if preserve_underscores
            else "_".join(word.lower() for word in value.split("_") if word)
        )
    if result[:1].isdigit():
        result = "_" + result
    if result.startswith("__") and not result.endswith("__"):
        result += "___"
    elif (
        result in _KEYWORDS
        or result in reserved
        or (constant and result.upper() in reserved)
    ):
        result += "_"
    if constant:
        result = _escape_enum_underscores(result).upper()
    return result


def _escape_enum_underscores(name: str) -> str:
    if name.startswith("__"):
        return name + "_" if name.endswith("__") and not name.endswith("___") else name
    if name.startswith("_") and name.endswith("_") and not name.endswith("__"):
        return name + "_"
    return name


def _plan_schema_names(selection: Selection) -> dict[ShapeId, str]:
    names: dict[ShapeId, str] = {}
    used: set[str] = set()
    for shape in selection.shapes:
        selected = (
            selection.service.rename.get(shape.id, shape.id.name)
            if selection.service
            else shape.id.name
        )
        base = _name(selected, constant=True)
        name = base
        suffix = 2
        while name in used:
            name = f"{base}_{suffix}"
            suffix += 1
        used.add(name)
        names[shape.id] = name
    return names
