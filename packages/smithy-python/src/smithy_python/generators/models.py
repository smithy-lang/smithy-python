# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ..context import GenerationContext
from ..docs import DocumentationConverter
from ..model import JSONValue, Member, Shape, ShapeID, ShapeType
from ..symbols import (
    DESERIALIZER,
    SCHEMA,
    UNION_UNKNOWN,
    snake_case,
)
from ..writer import PythonWriter


class _MissingDefault:
    pass


_MISSING = _MissingDefault()
_DATA_SHAPES = {
    ShapeType.STRUCTURE,
    ShapeType.UNION,
    ShapeType.ENUM,
    ShapeType.INT_ENUM,
}


class ModelsGenerator:
    """Generates dataclasses, enums, unions, serde helpers, and operations."""

    def __init__(self, context: GenerationContext) -> None:
        self.context = context
        self.docs = DocumentationConverter()
        self._shapes = {shape.id for shape in context.shapes}

    def run(self) -> None:
        writer = PythonWriter()
        self._add_imports(writer)
        self._import_schemas(writer)
        writer.write("logger = logging.getLogger(__name__)")
        writer.write()

        errors = [
            shape
            for shape in self.context.shapes
            if shape.type is ShapeType.STRUCTURE and shape.has_trait("smithy.api#error")
        ]
        if errors:
            writer.write("@dataclass(kw_only=True)")
            writer.write("class ServiceError(ModeledError):")
            writer.write('    """Base exception for modeled service errors."""')
            writer.write()

        for shape in self.context.shapes:
            if shape.type in {ShapeType.LIST, ShapeType.MAP}:
                writer.write(self._collection_helpers(shape))
                writer.write()
            elif shape.type is ShapeType.ENUM:
                writer.write(self._enum(shape, integer=False))
                writer.write()
            elif shape.type is ShapeType.INT_ENUM:
                writer.write(self._enum(shape, integer=True))
                writer.write()
            elif shape.type is ShapeType.STRUCTURE:
                writer.write(self._structure(shape))
                writer.write()
            elif shape.type is ShapeType.UNION:
                writer.write(self._union(shape))
                writer.write()

        for shape in self.context.shapes:
            if shape.type is ShapeType.OPERATION:
                writer.write(self._operation(shape))
                writer.write()

        path = f"src/{self.context.settings.module_name}/models.py"
        self.context.write(path, writer.render(), section="models")

    def _add_imports(self, writer: PythonWriter) -> None:
        writer.import_("logging", category="stdlib")
        writer.import_("dataclasses", "dataclass", category="stdlib")
        writer.import_("dataclasses", "field", category="stdlib")
        writer.import_("datetime", "datetime", category="stdlib")
        writer.import_("decimal", "Decimal", category="stdlib")
        writer.import_("enum", "IntEnum", category="stdlib")
        writer.import_("enum", "StrEnum", category="stdlib")
        writer.import_("typing", "Any", category="stdlib")
        writer.import_("typing", "Literal", category="stdlib")
        writer.import_("typing", "Self", category="stdlib")
        writer.import_("typing", "TypeAlias", category="stdlib")
        writer.import_(
            "smithy_core.aio.interfaces", "StreamingBlob", category="third_party"
        )
        writer.import_(
            "smithy_core.deserializers", "ShapeDeserializer", category="third_party"
        )
        writer.import_("smithy_core.documents", "Document", category="third_party")
        writer.import_("smithy_core.documents", "TypeRegistry", category="third_party")
        writer.import_("smithy_core.exceptions", "ModeledError", category="third_party")
        writer.import_(
            "smithy_core.exceptions", "SerializationError", category="third_party"
        )
        writer.import_("smithy_core.schemas", "APIOperation", category="third_party")
        writer.import_("smithy_core.schemas", "Schema", category="third_party")
        writer.import_(
            "smithy_core.serializers", "ShapeSerializer", category="third_party"
        )
        writer.import_("smithy_core.shapes", "ShapeID", category="third_party")
        writer.import_("smithy_core.types", "UnknownEnumMixin", category="third_party")
        self.context.add_dependency(
            *{
                dependency
                for shape in self.context.shapes
                for dependency in self.context.symbol_provider.to_symbol(
                    shape
                ).dependencies
            }
        )

    def _import_schemas(self, writer: PythonWriter) -> None:
        for shape in self.context.shapes:
            if shape.type is ShapeType.RESOURCE or shape.id.namespace == "smithy.api":
                continue
            schema = self.context.symbol_provider.to_symbol(shape).get_property(SCHEMA)
            if schema is not None:
                writer.import_(
                    "._private.schemas",
                    f"{schema.name} as _SCHEMA_{schema.name}",
                    category="local",
                )

    def _enum(self, shape: Shape, *, integer: bool) -> str:
        symbol = self.context.symbol_provider.to_symbol(shape)
        base = "IntEnum" if integer else "StrEnum"
        lines = [f"class {symbol.name}(UnknownEnumMixin, {base}):"]
        if documentation := shape.trait("smithy.api#documentation"):
            lines.append(self.docs.docstring(str(documentation)))
        if not shape.members:
            lines.append("    pass")
        for member in shape.members:
            name = self.context.symbol_provider.to_member_name(member, container=shape)
            value = member.trait("smithy.api#enumValue")
            lines.append(f"    {name} = {value!r}")
            if documentation := member.trait("smithy.api#documentation"):
                lines.append(self.docs.docstring(str(documentation)))
        return "\n".join(lines)

    def _structure(self, shape: Shape) -> str:
        symbol = self.context.symbol_provider.to_symbol(shape)
        is_error = shape.has_trait("smithy.api#error")
        base = "(ServiceError)" if is_error else ""
        lines = ["@dataclass(kw_only=True)", f"class {symbol.name}{base}:"]
        documentation = shape.trait("smithy.api#documentation")
        lines.append(
            self.docs.docstring(
                str(documentation) if documentation else f"Data for {shape.id.name}."
            )
        )
        if not shape.members and not is_error:
            lines.append("    pass")
        for member in shape.members:
            if (
                is_error
                and self.context.symbol_provider.to_member_name(member, container=shape)
                == "message"
            ):
                # ModeledError already defines a non-nullable message. Re-declaring
                # an optional Smithy member would create an incompatible override.
                continue
            lines.extend(self._property(shape, member))
        if is_error:
            fault = shape.trait("smithy.api#error")
            lines.append(f'    fault: Literal["client", "server"] | None = {fault!r}')
        lines.extend(("", *self._structure_serde(shape)))
        return "\n".join(lines)

    def _property(self, container: Shape, member: Member) -> list[str]:
        target = self.context.model.expect(member.target)
        symbol = self.context.symbol_provider.to_symbol(member)
        name = self.context.symbol_provider.to_member_name(member, container=container)
        required = member.has_trait("smithy.api#required") and not member.has_trait(
            "smithy.api#clientOptional"
        )
        default = self._default(member, target)
        nullable = self._is_nullable(member, target, default, required=required)
        annotation = symbol.name + (" | None" if nullable else "")
        sensitive = member.has_trait("smithy.api#sensitive") or target.has_trait(
            "smithy.api#sensitive"
        )
        assignment = ""
        if not isinstance(default, _MissingDefault):
            expression = self._default_expression(default, target)
            if isinstance(default, list | dict) or target.type is ShapeType.DOCUMENT:
                options = [f"default_factory=lambda: {expression}"]
                if sensitive:
                    options.insert(0, "repr=False")
                assignment = f" = field({', '.join(options)})"
            elif sensitive:
                assignment = f" = field(repr=False, default={expression})"
            else:
                assignment = f" = {expression}"
        elif nullable:
            assignment = (
                " = field(repr=False, default=None)" if sensitive else " = None"
            )
        elif sensitive:
            assignment = " = field(repr=False)"
        result = [f"    {name}: {annotation}{assignment}"]
        if documentation := member.trait("smithy.api#documentation"):
            result.append(self.docs.docstring(str(documentation)))
        return result

    def _structure_serde(self, shape: Shape) -> list[str]:
        schema = self._schema_alias(shape)
        is_error = shape.has_trait("smithy.api#error")
        lines = [
            "    def serialize(self, serializer: ShapeSerializer) -> None:",
            f"        serializer.write_struct({schema}, self)",
            "",
            "    def serialize_members(self, serializer: ShapeSerializer) -> None:",
        ]
        if not shape.members:
            lines.append("        pass")
        for member in shape.members:
            target = self.context.model.expect(member.target)
            name = self.context.symbol_provider.to_member_name(member, container=shape)
            required = member.has_trait("smithy.api#required") and not member.has_trait(
                "smithy.api#clientOptional"
            )
            nullable = self._is_nullable(
                member,
                target,
                self._default(member, target),
                required=required,
            )
            if is_error and name == "message":
                nullable = False
            if nullable:
                lines.append(f"        if self.{name} is not None:")
                indent = "            "
            else:
                indent = "        "
            member_schema = f"{schema}.members[{member.name!r}]"
            lines.extend(
                self._serialize_lines(
                    target, member_schema, f"self.{name}", "serializer", indent
                )
            )
        lines.extend(
            (
                "",
                "    @classmethod",
                "    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:",
                "        return cls(**cls.deserialize_kwargs(deserializer))",
                "",
                "    @classmethod",
                "    def deserialize_kwargs(cls, deserializer: ShapeDeserializer) -> dict[str, Any]:",
                "        kwargs: dict[str, Any] = {}",
                "",
                "        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:",
                "            match schema.expect_member_index():",
            )
        )
        if not shape.members:
            lines.append("                case _:")
            lines.append(
                '                    logger.debug("Unexpected member schema: %s", schema)'
            )
        else:
            for index, member in enumerate(shape.members):
                target = self.context.model.expect(member.target)
                name = self.context.symbol_provider.to_member_name(
                    member, container=shape
                )
                expression = self._deserialize_expression(
                    target, f"{schema}.members[{member.name!r}]", "de"
                )
                lines.extend(
                    (
                        f"                case {index}:",
                        f"                    kwargs[{name!r}] = {expression}",
                    )
                )
            lines.extend(
                (
                    "                case _:",
                    '                    logger.debug("Unexpected member schema: %s", schema)',
                )
            )
        lines.extend(
            (
                "",
                f"        deserializer.read_struct({schema}, consumer=_consumer)",
                "        return kwargs",
            )
        )
        return lines

    def _collection_helpers(self, shape: Shape) -> str:
        name = snake_case(shape.id.name)
        schema_type = self.context.symbol_provider.to_symbol(shape).name
        if shape.type is ShapeType.LIST:
            target = self.context.model.expect(shape.member("member").target)
            lines = [
                f"def _serialize_{name}(",
                f"    serializer: ShapeSerializer, schema: Schema, value: {schema_type}",
                ") -> None:",
                "    with serializer.begin_list(schema, size=len(value)) as entries:",
                "        for item in value:",
            ]
            if shape.has_trait("smithy.api#sparse"):
                lines.extend(
                    (
                        "            if item is None:",
                        "                entries.write_null(schema.members['member'])",
                        "                continue",
                    )
                )
            lines.extend(
                self._serialize_lines(
                    target,
                    "schema.members['member']",
                    "item",
                    "entries",
                    "            ",
                )
            )
            lines.extend(
                (
                    "",
                    f"def _deserialize_{name}(deserializer: ShapeDeserializer, schema: Schema) -> {schema_type}:",
                    f"    result: {schema_type} = []",
                    "",
                    "    def _consumer(de: ShapeDeserializer) -> None:",
                    f"        result.append({self._deserialize_expression(target, "schema.members['member']", 'de')})",
                    "",
                    "    deserializer.read_list(schema, consumer=_consumer)",
                    "    return result",
                )
            )
            return "\n".join(lines)

        target = self.context.model.expect(shape.member("value").target)
        lines = [
            f"def _serialize_{name}(",
            f"    serializer: ShapeSerializer, schema: Schema, value: {schema_type}",
            ") -> None:",
            "    with serializer.begin_map(schema, size=len(value)) as entries:",
            "        for key, item in value.items():",
            "            def _write_value(value_serializer: ShapeSerializer) -> None:",
        ]
        if shape.has_trait("smithy.api#sparse"):
            lines.extend(
                (
                    "                if item is None:",
                    "                    value_serializer.write_null(schema.members['value'])",
                    "                    return",
                )
            )
        lines.extend(
            self._serialize_lines(
                target,
                "schema.members['value']",
                "item",
                "value_serializer",
                "                ",
            )
        )
        lines.extend(
            (
                "",
                "            entries.entry(key, _write_value)",
                "",
                f"def _deserialize_{name}(deserializer: ShapeDeserializer, schema: Schema) -> {schema_type}:",
                f"    result: {schema_type} = {{}}",
                "",
                "    def _consumer(key: str, de: ShapeDeserializer) -> None:",
                f"        result[key] = {self._deserialize_expression(target, "schema.members['value']", 'de')}",
                "",
                "    deserializer.read_map(schema, consumer=_consumer)",
                "    return result",
            )
        )
        return "\n".join(lines)

    def _union(self, shape: Shape) -> str:
        symbol = self.context.symbol_provider.to_symbol(shape)
        schema = self._schema_alias(shape)
        variants: list[str] = []
        blocks: list[str] = []
        for member in shape.members:
            member_symbol = self.context.symbol_provider.union_member_symbol(
                shape, member
            )
            variants.append(member_symbol.name)
            target = self.context.model.expect(member.target)
            target_symbol = self.context.symbol_provider.to_symbol(member)
            lines = [
                "@dataclass(kw_only=True)",
                f"class {member_symbol.name}:",
            ]
            if documentation := member.trait("smithy.api#documentation"):
                lines.append(self.docs.docstring(str(documentation)))
            lines.extend(
                (
                    f"    value: {target_symbol.name}",
                    "",
                    "    def serialize(self, serializer: ShapeSerializer) -> None:",
                    f"        serializer.write_struct({schema}, self)",
                    "",
                    "    def serialize_members(self, serializer: ShapeSerializer) -> None:",
                )
            )
            lines.extend(
                self._serialize_lines(
                    target,
                    f"{schema}.members[{member.name!r}]",
                    "self.value",
                    "serializer",
                    "        ",
                )
            )
            blocks.append("\n".join(lines))

        unknown = symbol.expect_property(UNION_UNKNOWN)
        variants.append(unknown.name)
        blocks.append(
            "\n".join(
                (
                    "@dataclass(kw_only=True)",
                    f"class {unknown.name}:",
                    '    """An unknown union variant received from a newer service."""',
                    "    tag: str",
                    "",
                    "    def serialize(self, serializer: ShapeSerializer) -> None:",
                    '        raise SerializationError("Unknown union variants cannot be serialized")',
                    "",
                    "    def serialize_members(self, serializer: ShapeSerializer) -> None:",
                    '        raise SerializationError("Unknown union variants cannot be serialized")',
                )
            )
        )
        blocks.append(f"{symbol.name}: TypeAlias = {' | '.join(variants)}")
        deserializer = symbol.expect_property(DESERIALIZER)
        lines = [
            f"class {deserializer.name}:",
            f"    _result: {symbol.name} | None = None",
            "",
            f"    def deserialize(self, deserializer: ShapeDeserializer) -> {symbol.name}:",
            "        self._result = None",
            f"        deserializer.read_struct({schema}, self._consumer)",
            "        if self._result is None:",
            '            raise SerializationError("A union must contain exactly one value")',
            "        return self._result",
            "",
            "    def _consumer(self, schema: Schema, de: ShapeDeserializer) -> None:",
            "        match schema.expect_member_index():",
        ]
        for index, member in enumerate(shape.members):
            member_symbol = self.context.symbol_provider.union_member_symbol(
                shape, member
            )
            target = self.context.model.expect(member.target)
            expression = self._deserialize_expression(
                target, f"{schema}.members[{member.name!r}]", "de"
            )
            lines.extend(
                (
                    f"            case {index}:",
                    f"                self._set_result({member_symbol.name}(value={expression}))",
                )
            )
        lines.extend(
            (
                "            case _:",
                f"                self._set_result({unknown.name}(tag=schema.expect_member_name()))",
                "",
                f"    def _set_result(self, value: {symbol.name}) -> None:",
                "        if self._result is not None:",
                '            raise SerializationError("A union must contain exactly one value")',
                "        self._result = value",
            )
        )
        blocks.append("\n".join(lines))
        return "\n\n".join(blocks)

    def _operation(self, shape: Shape) -> str:
        input_shape = self._referenced_shape(shape, "input")
        output_shape = self._referenced_shape(shape, "output")
        if input_shape is None or output_shape is None:
            return f"# Operation {shape.id} has no generated input/output."
        operation = self.context.symbol_provider.to_symbol(shape)
        input_symbol = self.context.symbol_provider.to_symbol(input_shape)
        output_symbol = self.context.symbol_provider.to_symbol(output_shape)
        errors = [
            self.context.model.expect(reference)
            for reference in self._reference_list(shape, "errors")
            if reference.without_member() in self._shapes
        ]
        registry = ", ".join(
            f"ShapeID({str(error.id)!r}): {self.context.symbol_provider.to_symbol(error).name}"
            for error in errors
        )
        error_schemas = ", ".join(self._schema_alias(error) for error in errors)
        auth = ", ".join(f"ShapeID({value!r})" for value in self._effective_auth(shape))
        return "\n".join(
            (
                f"{operation.name} = APIOperation(",
                f"    input={input_symbol.name},",
                f"    output={output_symbol.name},",
                f"    schema={self._schema_alias(shape)},",
                f"    input_schema={self._schema_alias(input_shape)},",
                f"    output_schema={self._schema_alias(output_shape)},",
                f"    error_registry=TypeRegistry({{{registry}}}),",
                f"    effective_auth_schemes=[{auth}],",
                f"    error_schemas=[{error_schemas}],",
                ")",
            )
        )

    def _serialize_lines(
        self,
        target: Shape,
        schema: str,
        value: str,
        serializer: str,
        indent: str,
    ) -> list[str]:
        method = {
            ShapeType.BLOB: "write_data_stream"
            if target.has_trait("smithy.api#streaming")
            else "write_blob",
            ShapeType.BOOLEAN: "write_boolean",
            ShapeType.STRING: "write_string",
            ShapeType.ENUM: "write_string",
            ShapeType.TIMESTAMP: "write_timestamp",
            ShapeType.BYTE: "write_byte",
            ShapeType.SHORT: "write_short",
            ShapeType.INTEGER: "write_integer",
            ShapeType.INT_ENUM: "write_integer",
            ShapeType.LONG: "write_long",
            ShapeType.FLOAT: "write_float",
            ShapeType.DOUBLE: "write_double",
            ShapeType.BIG_INTEGER: "write_big_integer",
            ShapeType.BIG_DECIMAL: "write_big_decimal",
            ShapeType.DOCUMENT: "write_document",
        }.get(target.type)
        if method:
            return [f"{indent}{serializer}.{method}({schema}, {value})"]
        if target.type in {ShapeType.STRUCTURE, ShapeType.UNION}:
            return [f"{indent}{serializer}.write_struct({schema}, {value})"]
        if target.type in {ShapeType.LIST, ShapeType.MAP}:
            return [
                f"{indent}_serialize_{snake_case(target.id.name)}({serializer}, {schema}, {value})"
            ]
        return [f"{indent}raise SerializationError('Unsupported shape: {target.id}')"]

    def _deserialize_expression(
        self, target: Shape, schema: str, deserializer: str
    ) -> str:
        method = {
            ShapeType.BLOB: "read_data_stream"
            if target.has_trait("smithy.api#streaming")
            else "read_blob",
            ShapeType.BOOLEAN: "read_boolean",
            ShapeType.STRING: "read_string",
            ShapeType.ENUM: "read_string",
            ShapeType.TIMESTAMP: "read_timestamp",
            ShapeType.BYTE: "read_byte",
            ShapeType.SHORT: "read_short",
            ShapeType.INTEGER: "read_integer",
            ShapeType.INT_ENUM: "read_integer",
            ShapeType.LONG: "read_long",
            ShapeType.FLOAT: "read_float",
            ShapeType.DOUBLE: "read_double",
            ShapeType.BIG_INTEGER: "read_big_integer",
            ShapeType.BIG_DECIMAL: "read_big_decimal",
            ShapeType.DOCUMENT: "read_document",
        }.get(target.type)
        if method:
            return f"{deserializer}.{method}({schema})"
        if target.type is ShapeType.STRUCTURE:
            return f"{self.context.symbol_provider.to_symbol(target).name}.deserialize({deserializer})"
        if target.type is ShapeType.UNION:
            union = self.context.symbol_provider.to_symbol(target)
            return f"{union.expect_property(DESERIALIZER).name}().deserialize({deserializer})"
        if target.type in {ShapeType.LIST, ShapeType.MAP}:
            return (
                f"_deserialize_{snake_case(target.id.name)}({deserializer}, {schema})"
            )
        return "None"

    def _default(self, member: Member, target: Shape) -> _MissingDefault | JSONValue:
        if member.has_trait("smithy.api#clientOptional"):
            return _MISSING
        if "smithy.api#default" in member.traits:
            return member.traits["smithy.api#default"]
        if "smithy.api#default" in target.traits:
            return target.traits["smithy.api#default"]
        return _MISSING

    def _is_nullable(
        self,
        member: Member,
        target: Shape,
        default: _MissingDefault | JSONValue,
        *,
        required: bool,
    ) -> bool:
        if member.has_trait("smithy.api#clientOptional"):
            return True
        if default is None and target.type is not ShapeType.DOCUMENT:
            return True
        return not required and isinstance(default, _MissingDefault)

    def _default_expression(self, value: JSONValue, target: Shape) -> str:
        if target.type is ShapeType.DOCUMENT:
            return f"Document({value!r})"
        if target.type is ShapeType.TIMESTAMP and isinstance(value, int | float):
            return f"datetime.fromtimestamp({value!r})"
        if target.type is ShapeType.BIG_DECIMAL:
            return f"Decimal({str(value)!r})"
        return repr(value)

    def _schema_alias(self, shape: Shape) -> str:
        schema = self.context.symbol_provider.to_symbol(shape).expect_property(SCHEMA)
        return f"_SCHEMA_{schema.name}"

    def _referenced_shape(self, shape: Shape, key: str) -> Shape | None:
        value = shape.attributes.get(key)
        if not isinstance(value, dict):
            return None
        target_id = value.get("target")
        if not isinstance(target_id, str):
            return None
        target = self.context.model.expect(target_id)
        return target if target.id in self._shapes else None

    def _reference_list(self, shape: Shape, key: str) -> tuple[ShapeID, ...]:
        value = shape.attributes.get(key, [])
        if not isinstance(value, list):
            return ()
        result: list[ShapeID] = []
        for reference in value:
            if not isinstance(reference, dict):
                continue
            target = reference.get("target")
            if isinstance(target, str):
                result.append(ShapeID.parse(target))
        return tuple(result)

    def _effective_auth(self, operation: Shape) -> tuple[str, ...]:
        value = operation.trait("smithy.api#auth")
        if (
            "smithy.api#auth" not in operation.traits
            and self.context.service is not None
        ):
            value = self.context.service.trait("smithy.api#auth", [])
        if not isinstance(value, list):
            return ()
        return tuple(item for item in value if isinstance(item, str))
