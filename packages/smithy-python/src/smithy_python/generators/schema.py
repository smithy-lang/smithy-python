# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from ..context import GenerationContext
from ..model import JSONValue, Member, Shape, ShapeType
from ..symbols import SCHEMA
from ..writer import PythonWriter

_TRAIT_FILTER = {
    "smithy.api#documentation",
    "smithy.api#enum",
    "smithy.synthetic#enum",
}


class SchemaGenerator:
    """Generates the compact runtime schema graph used by serializers."""

    def __init__(self, context: GenerationContext) -> None:
        self.context = context
        self._generated = {
            shape.id
            for shape in context.shapes
            if shape.type is not ShapeType.RESOURCE
            and shape.id.namespace != "smithy.api"
        }

    def run(self) -> None:
        writer = PythonWriter()
        writer.import_("smithy_core.schemas", "Schema", category="third_party")
        writer.import_("smithy_core.shapes", "ShapeID", category="third_party")
        writer.import_("smithy_core.shapes", "ShapeType", category="third_party")
        writer.import_("smithy_core.traits", "Trait", category="third_party")
        prelude_names = self._prelude_references()
        for name in prelude_names:
            writer.import_("smithy_core.prelude", name, category="third_party")

        generated_shapes = [
            shape for shape in self.context.shapes if shape.id in self._generated
        ]
        for shape in generated_shapes:
            writer.write(self._shape_schema(shape))
            writer.write()
        if any(shape.members for shape in generated_shapes):
            writer.write(
                "# Complete member links after every schema exists. This supports cycles while"
            )
            writer.write("# retaining the exact member order from the Smithy model.")
            for shape in generated_shapes:
                for index, member in enumerate(shape.members):
                    writer.write(self._member_assignment(shape, member, index))
            writer.write()

        path = f"src/{self.context.settings.module_name}/_private/schemas.py"
        self.context.write(path, writer.render(), section="schemas")

    def _shape_schema(self, shape: Shape) -> str:
        symbol = self.context.symbol_provider.to_symbol(shape).expect_property(SCHEMA)
        traits = _traits(shape.traits)
        arguments = [f"id=ShapeID({str(shape.id)!r})"]
        if shape.type is not ShapeType.STRUCTURE:
            arguments.append(f"shape_type=ShapeType.{_shape_type_name(shape.type)}")
        if traits:
            arguments.append(f"traits={traits}")
        if shape.type is ShapeType.STRUCTURE or shape.members:
            members = ", ".join(f"{member.name!r}: None" for member in shape.members)
            arguments.append(f"members={{{members}}}")
            constructor = "Schema.collection"
        else:
            constructor = "Schema"
        joined = ",\n    ".join(arguments)
        return f"{symbol.name} = {constructor}(\n    {joined},\n)"

    def _member_assignment(self, shape: Shape, member: Member, index: int) -> str:
        container = self.context.symbol_provider.to_symbol(shape).expect_property(
            SCHEMA
        )
        target = self.context.model.expect(member.target)
        target_schema = self.context.symbol_provider.to_symbol(target).expect_property(
            SCHEMA
        )
        traits = _traits(member.traits)
        arguments = [
            f"id={container.name}.id.with_member({member.name!r})",
            f"target={target_schema.name}",
            f"index={index}",
        ]
        if traits:
            arguments.append(f"member_traits={traits}")
        joined = ",\n        ".join(arguments)
        return (
            f"{container.name}.members[{member.name!r}] = Schema.member(\n"
            f"        {joined},\n"
            ")"
        )

    def _prelude_references(self) -> tuple[str, ...]:
        names: set[str] = set()
        for shape in self.context.shapes:
            for member in shape.members:
                if member.target.namespace == "smithy.api":
                    target = self.context.model.expect(member.target)
                    names.add(
                        self.context.symbol_provider.to_symbol(target)
                        .expect_property(SCHEMA)
                        .name
                    )
        return tuple(sorted(names))


def _shape_type_name(shape_type: ShapeType) -> str:
    value = shape_type.value
    result: list[str] = []
    for character in value:
        if character.isupper():
            result.extend(("_", character))
        else:
            result.append(character.upper())
    return "".join(result)


def _traits(traits: Any) -> str:
    rendered = [
        _trait(shape_id, value)
        for shape_id, value in traits.items()
        if shape_id not in _TRAIT_FILTER
    ]
    return f"[{', '.join(rendered)}]" if rendered else ""


def _trait(shape_id: str, value: JSONValue) -> str:
    if value == {}:
        return f"Trait.new(id=ShapeID({shape_id!r}))"
    return f"Trait.new(id=ShapeID({shape_id!r}), value={value!r})"
