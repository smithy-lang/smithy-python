# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Emission of lazy runtime models and their static typing surface."""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping
from dataclasses import replace
from json import dumps
from textwrap import wrap
from typing import TYPE_CHECKING, Final

from . import dependencies as _dependencies
from . import exceptions as _exceptions
from . import model as _model
from . import symbols as _symbols

if TYPE_CHECKING:
    from .generation import GenerationContext, ModelPlan, TypesSettings
    from .writer import PythonWriter

__all__ = ["ModelGenerator"]


class ModelGenerator:
    """Emit lazy runtime models and the complete static model stub."""

    def generate(self, context: GenerationContext[TypesSettings]) -> None:
        """Register ``models.py`` and ``models.pyi`` with the file manifest."""
        _validate_member_names(context)
        package = context.settings.package
        directory = package.replace(".", "/")
        _write_runtime(
            context.files.python_module(
                f"src/{directory}/models.py", f"{package}.models"
            ),
            context.plan.models,
        )
        _StubEmitter(
            context.files.python_module(
                f"src/{directory}/models.pyi", f"{package}.models"
            ),
            context,
        ).write()


def _core_reference(name: str, module: str) -> _symbols.TypeReference:
    return _symbols.TypeReference(
        name, f"smithy_core.{module}", dependencies=(_dependencies.SMITHY_CORE,)
    )


_MODEL_REGISTRY: Final = _core_reference("ModelRegistry", "_dynamic_models")
_MODELED_ERROR: Final = _core_reference("ModeledError", "exceptions")
_SHAPE_SERIALIZER: Final = _core_reference("ShapeSerializer", "serializers")
_SHAPE_DESERIALIZER: Final = _core_reference("ShapeDeserializer", "deserializers")
_UNKNOWN_ENUM_MIXIN: Final = _core_reference("UnknownEnumMixin", "types")
_RESPONSE_METADATA: Final = _core_reference("ResponseMetadata", "response")
_DATACLASS: Final = _symbols.TypeReference("dataclass", "dataclasses")
_SELF: Final = _symbols.TypeReference("Self", "typing")
_STR_ENUM: Final = _symbols.TypeReference("StrEnum", "enum")
_INT_ENUM: Final = _symbols.TypeReference("IntEnum", "enum")
_SCHEMAS: Final = _symbols.TypeReference("schemas", "._private")

_ERROR_MESSAGE_NAMES: Final = frozenset({"errormessage", "error_message", "message"})
_DOCSTRING_WIDTH: Final = 72
_MODEL_MEMBER_NAMES: Final = frozenset(
    {
        "bool",
        "bytes",
        "bytearray",
        "dict",
        "float",
        "int",
        "list",
        "str",
        "datetime",
        "serialize",
        "serialize_members",
        "deserialize",
        "__init__",
        "__post_init__",
        "_smithy_default",
        "__repr__",
        "__annotations__",
    }
)
_ERROR_MEMBER_NAMES: Final = frozenset(
    {"is_retry_safe", "retry_after", "is_throttling_error", "fault"}
)
_RESPONSE_METADATA_DOC: Final = (
    "Metadata about the response that produced this output.\n\n"
    "Use this to recover the request identifiers a service's support team needs "
    "in order to investigate a call. Members of the metadata are individually "
    "optional."
)
_SERVICE_ERROR_DOC: Final = (
    "Base error for all errors in the service.\n\n"
    "Some exceptions do not extend from this class, including synthetic, implicit, "
    "and shared exception types."
)
_UNKNOWN_UNION_DOC: Final = (
    "Represents an unknown variant.\n\n"
    "If you receive this value, you will need to update your library to receive "
    "the parsed value.\n\n"
    "This value may not be deliberately sent."
)


def _write_runtime(writer: PythonWriter, plan: ModelPlan) -> None:
    exports = _model_exports(plan)
    writer.line("class ServiceError(", _MODELED_ERROR, "):")
    with writer.indent():
        _write_docstring(writer, _SERVICE_ERROR_DOC)
    writer.line()
    writer.line()
    _write_mapping(writer, "_MODEL_INDEX", plan.registry_index)
    writer.line()
    _write_mapping(writer, "_RENAMES", plan.renames)
    writer.line()
    _write_mapping(writer, "_TARGET_NAMES", plan.target_names)
    writer.line()
    additional = exports[len(plan.registry_index) + 1 :]
    if additional:
        writer.line(
            "_MODEL_NAMES = (*tuple(_MODEL_INDEX), ",
            ", ".join(map(_quote, additional)),
            ")",
        )
    else:
        writer.line("_MODEL_NAMES = tuple(_MODEL_INDEX)")
    writer.line("__all__ = (", _quote(exports[0]), ", *_MODEL_NAMES)")
    writer.line()
    writer.line()
    writer.line("_registry = ", _MODEL_REGISTRY, "(")
    with writer.indent():
        writer.line(_SCHEMAS, ",")
        writer.line("renames=_RENAMES,")
        writer.line("index=_MODEL_INDEX,")
        writer.line("target_names=_TARGET_NAMES,")
        _write_string_set(writer, "shape_names", plan.shape_names, suffix=",")
        writer.line('service_error="ServiceError",')
    writer.line(")")
    writer.line("del ", _SCHEMAS, ", ", _MODEL_REGISTRY, ", ", _MODELED_ERROR)
    writer.line()
    writer.line()
    writer.line("def __getattr__(name: str):")
    with writer.indent():
        writer.line("value = _registry.build(name)")
        writer.line("globals()[name] = value")
        writer.line("return value")
    writer.line()
    writer.line()
    writer.line("def __dir__() -> list[str]:")
    with writer.indent():
        writer.line("return sorted({*globals(), *__all__})")


class _StubEmitter:
    def __init__(
        self,
        writer: PythonWriter,
        context: GenerationContext[TypesSettings],
    ) -> None:
        self.writer = writer
        self.model = context.model
        self.plan = context.plan.models
        self.symbols = context.symbols
        self.module = f"{context.settings.package}.models"
        operations = tuple(context.model.iter_shapes(_model.OperationShape))
        self.inputs = {operation.input for operation in operations} | {
            shape.id for shape in self.plan.shapes if shape.has_trait("input")
        }
        self.outputs = {operation.output for operation in operations} | {
            shape.id for shape in self.plan.shapes if shape.has_trait("output")
        }

    def write(self) -> None:
        writer = self.writer
        writer.line("__all__ = [")
        with writer.indent():
            for name in sorted(_model_exports(self.plan)):
                writer.line(_quote(name), ",")
        writer.line("]")
        writer.line()
        writer.line("class _SerdeShape:")
        with writer.indent():
            writer.line(
                "def serialize(self, serializer: ",
                _SHAPE_SERIALIZER,
                ") -> None: ...",
            )
            writer.line(
                "def serialize_members(self, serializer: ",
                _SHAPE_SERIALIZER,
                ") -> None: ...",
            )
            writer.line("@classmethod")
            writer.line(
                "def deserialize(cls, deserializer: ",
                _SHAPE_DESERIALIZER,
                ") -> ",
                _SELF,
                ": ...",
            )
        writer.line()
        writer.line("class ServiceError(", _MODELED_ERROR, "):")
        with writer.indent():
            _write_docstring(writer, _SERVICE_ERROR_DOC)

        for shape in self.plan.shapes:
            writer.line()
            match shape.type:
                case _model.ShapeType.STRUCTURE:
                    self._write_structure(shape)
                case _model.ShapeType.UNION:
                    self._write_union(shape)
                case _model.ShapeType.ENUM | _model.ShapeType.INT_ENUM:
                    self._write_enum(shape)
                case _:
                    pass
        if self.plan.includes_unit:
            writer.line()
            writer.line("@", _DATACLASS, "(kw_only=True)")
            writer.line("class Unit(_SerdeShape):")
            with writer.indent():
                writer.line("pass")

    def _write_structure(self, shape: _model.Shape) -> None:
        writer = self.writer
        name = self.plan.declaration_names[shape.id]
        error = shape.has_trait("error")
        writer.line("@", _DATACLASS, "(kw_only=True)")
        writer.line(
            "class ",
            name,
            "(ServiceError, _SerdeShape):" if error else "(_SerdeShape):",
        )
        with writer.indent():
            members = tuple(
                member
                for member in shape.members.values()
                if not error or member.name.lower() not in _ERROR_MESSAGE_NAMES
            )
            carries_metadata = error or shape.id in self.outputs
            _write_docstring(
                writer,
                _documentation(shape) or f"Dataclass for {shape.id.name} structure.",
            )
            if members or carries_metadata:
                writer.line()
            for member in members:
                reference = self.symbols.type_reference(member.target)
                has_default = member.has_trait("default") or self.model.get_target(
                    member
                ).has_trait("default")
                mandatory = (
                    shape.id not in self.inputs
                    and member.has_trait("required")
                    and not has_default
                )
                if not mandatory:
                    reference = replace(reference, nullable=True)
                writer.line(
                    self.symbols.member_name(member.id),
                    ": ",
                    reference,
                    "" if mandatory else " = ...",
                )
                if docs := _documentation(member):
                    _write_docstring(writer, docs)
            if carries_metadata:
                writer.line("response_metadata: ", _RESPONSE_METADATA, " = ...")
                _write_docstring(writer, _RESPONSE_METADATA_DOC)

    def _write_union(self, shape: _model.Shape) -> None:
        writer = self.writer
        variants: list[_symbols.TypeReference] = []
        for member in shape.members.values():
            name = self.plan.union_variant_names[member.id]
            variants.append(_symbols.TypeReference(name, self.module))
            writer.line("@", _DATACLASS)
            writer.line("class ", name, "(_SerdeShape):")
            with writer.indent():
                if docs := _documentation(member):
                    _write_docstring(writer, docs)
                    writer.line()
                writer.line("value: ", self.symbols.type_reference(member.target))
            writer.line()

        unknown = self.plan.union_unknown_names[shape.id]
        variants.append(_symbols.TypeReference(unknown, self.module))
        writer.line("@", _DATACLASS)
        writer.line("class ", unknown, "(_SerdeShape):")
        with writer.indent():
            _write_docstring(writer, _UNKNOWN_UNION_DOC)
            writer.line()
            writer.line("tag: str")
        writer.line()

        name = self.plan.declaration_names[shape.id]
        writer.line(name, " = ", *_join_types(variants))
        if docs := _documentation(shape):
            _write_docstring(writer, docs)
        writer.line()
        writer.line("class _", name, "Deserializer:")
        with writer.indent():
            writer.line(
                "def deserialize(self, deserializer: ",
                _SHAPE_DESERIALIZER,
                ") -> ",
                _symbols.TypeReference(name, self.module),
                ": ...",
            )

    def _write_enum(self, shape: _model.Shape) -> None:
        writer = self.writer
        name = self.plan.declaration_names[shape.id]
        base = _INT_ENUM if shape.type is _model.ShapeType.INT_ENUM else _STR_ENUM
        writer.line("class ", name, "(", _UNKNOWN_ENUM_MIXIN, ", ", base, "):")
        with writer.indent():
            docs = _documentation(shape)
            if docs:
                _write_docstring(writer, docs)
                if shape.members:
                    writer.line()
            for member in shape.members.values():
                value = member.get_trait("enumValue")
                writer.line(
                    self.symbols.member_name(member.id),
                    " = ",
                    _literal(member.name if value is None else value),
                )
                if docs := _documentation(member):
                    _write_docstring(writer, docs)
            if not docs and not shape.members:
                writer.line("pass")


def _model_exports(plan: ModelPlan) -> tuple[str, ...]:
    exports = ("ServiceError", *plan.registry_index)
    return (*exports, "Unit") if plan.includes_unit else exports


def _write_mapping(writer: PythonWriter, name: str, values: Mapping[str, str]) -> None:
    if not values:
        writer.line(name, " = {}")
        return
    writer.line(name, " = {")
    with writer.indent():
        for key, value in values.items():
            writer.line(_quote(key), ": ", _quote(value), ",")
    writer.line("}")


def _write_string_set(
    writer: PythonWriter,
    name: str,
    values: Collection[str],
    *,
    suffix: str = "",
) -> None:
    if not values:
        writer.line(name, "=frozenset()", suffix)
        return
    writer.line(name, "=frozenset(")
    with writer.indent():
        writer.line("{")
        with writer.indent():
            for value in sorted(values):
                writer.line(_quote(value), ",")
        writer.line("}")
    writer.line(")", suffix)


def _write_docstring(writer: PythonWriter, value: str) -> None:
    lines = [
        wrapped
        for line in value.split("\n")
        for wrapped in (
            wrap(
                line,
                width=_DOCSTRING_WIDTH,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [""]
        )
    ]
    if len(lines) > 1:
        writer.line('"""')
        for line in lines:
            writer.line(line.replace("\\", "\\\\").replace('"""', '\\"""'))
        writer.line('"""')
        return
    writer.line(_quote(lines[0]))


def _literal(value: object) -> str:
    return _quote(value) if isinstance(value, str) else repr(value)


def _quote(value: str) -> str:
    return dumps(value, ensure_ascii=False)


def _join_types(
    types: Collection[_symbols.TypeReference],
) -> tuple[str | _symbols.TypeReference, ...]:
    parts: list[str | _symbols.TypeReference] = []
    for reference in types:
        if parts:
            parts.append(" | ")
        parts.append(reference)
    return tuple(parts)


def _documentation(shape: _model.Shape) -> str | None:
    value = shape.get_trait("documentation")
    return value if isinstance(value, str) else None


def _validate_member_names(context: GenerationContext[TypesSettings]) -> None:
    reserved = _model_reserved_member_names(context.model)
    for shape in context.plan.models.shapes:
        names: set[str] = set()
        shape_reserved = reserved(shape)
        for member in shape.members.values():
            name = context.symbols.member_name(member.id)
            if name in shape_reserved:
                raise _exceptions.CodegenError(
                    f"Symbol provider did not reserve model member name {name!r} "
                    f"for {member.id}"
                )
            if name in names:
                raise _exceptions.CodegenError(
                    f"Generated model member name collision {name!r} in {shape.id}"
                )
            names.add(name)


def _model_reserved_member_names(
    model: _model.Model,
) -> Callable[[_model.Shape], Collection[str]]:
    outputs = {
        operation.output for operation in model.iter_shapes(_model.OperationShape)
    } | {shape.id for shape in model.iter_shapes() if shape.has_trait("output")}

    def reserved(shape: _model.Shape) -> Collection[str]:
        names = set(_MODEL_MEMBER_NAMES)
        if shape.has_trait("error"):
            names.update(_ERROR_MEMBER_NAMES)
        if shape.has_trait("error") or shape.id in outputs:
            names.add("response_metadata")
        return names

    return reserved
