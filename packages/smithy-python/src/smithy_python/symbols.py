# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Python symbol resolution decoupled from source generation."""

from __future__ import annotations

import keyword
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from decimal import Decimal
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, Protocol, Self

from .model import Member, Model, Shape, ShapeID, ShapeType
from .settings import GeneratorSettings


@dataclass(frozen=True, slots=True)
class PythonDependency:
    """A Python distribution required by a generated symbol."""

    package: str
    version: str = ""
    extras: tuple[str, ...] = ()
    group: str = "dependencies"

    @property
    def requirement(self) -> str:
        extras = f"[{', '.join(self.extras)}]" if self.extras else ""
        return f"{self.package}{extras}{self.version}"


@dataclass(frozen=True, slots=True)
class SymbolProperty[T]:
    """A strongly typed key for symbol metadata."""

    name: str


@dataclass(frozen=True, slots=True)
class Symbol:
    """A Python type or value and everything needed to refer to it."""

    name: str
    namespace: str = ""
    definition_file: PurePosixPath | None = None
    dependencies: tuple[PythonDependency, ...] = ()
    references: tuple[Symbol, ...] = ()
    properties: Mapping[SymbolProperty[Any], Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def with_property[T](self, key: SymbolProperty[T], value: T) -> Self:
        return replace(
            self,
            properties=MappingProxyType({**self.properties, key: value}),
        )

    def get_property[T](
        self, key: SymbolProperty[T], default: T | None = None
    ) -> T | None:
        return self.properties.get(key, default)

    def expect_property[T](self, key: SymbolProperty[T]) -> T:
        try:
            return self.properties[key]
        except KeyError as error:
            raise KeyError(
                f"Symbol {self.name!r} has no {key.name!r} property"
            ) from error


SCHEMA = SymbolProperty[Symbol]("schema")
SERIALIZER = SymbolProperty[Symbol]("serializer")
DESERIALIZER = SymbolProperty[Symbol]("deserializer")
OPERATION_METHOD = SymbolProperty[Symbol]("operation_method")
UNION_UNKNOWN = SymbolProperty[Symbol]("union_unknown")
SHAPE = SymbolProperty[Shape]("shape")


class SymbolProvider(Protocol):
    """Resolves model shapes and members to Python symbols."""

    def to_symbol(self, shape: Shape | Member) -> Symbol: ...

    def to_member_name(
        self, member: Member, *, container: Shape | None = None
    ) -> str: ...

    def union_member_symbol(self, container: Shape, member: Member) -> Symbol: ...


_SMITHY_CORE = PythonDependency("smithy-core", "~=0.6.0")
_SIMPLE_TYPES: dict[ShapeType, tuple[str, str, PythonDependency | None]] = {
    ShapeType.BLOB: ("bytes", "", None),
    ShapeType.BOOLEAN: ("bool", "", None),
    ShapeType.STRING: ("str", "", None),
    ShapeType.TIMESTAMP: ("datetime", "datetime", None),
    ShapeType.BYTE: ("int", "", None),
    ShapeType.SHORT: ("int", "", None),
    ShapeType.INTEGER: ("int", "", None),
    ShapeType.LONG: ("int", "", None),
    ShapeType.FLOAT: ("float", "", None),
    ShapeType.DOUBLE: ("float", "", None),
    ShapeType.BIG_INTEGER: ("int", "", None),
    ShapeType.BIG_DECIMAL: (Decimal.__name__, "decimal", None),
    ShapeType.DOCUMENT: ("Document", "smithy_core.documents", _SMITHY_CORE),
}
_GENERATED_TYPES = {
    ShapeType.STRUCTURE,
    ShapeType.UNION,
    ShapeType.ENUM,
    ShapeType.INT_ENUM,
}
_CLASS_RESERVED = {
    "Config",
    "ServiceError",
    "Schema",
    "ShapeID",
}
_MEMBER_RESERVED = {
    "deserialize",
    "deserialize_kwargs",
    "serialize",
    "serialize_members",
}
_ERROR_MEMBER_RESERVED = {
    "args",
    "fault",
    "is_retry_safe",
    "is_throttling_error",
    "is_timeout_error",
    "retry_after",
}


class PythonSymbolProvider:
    """Default, idiomatic Python symbol provider for Smithy shapes."""

    def __init__(self, model: Model, settings: GeneratorSettings) -> None:
        self.model = model
        self.settings = settings
        self._cache: dict[ShapeID, Symbol] = {}
        self._resolving: set[ShapeID] = set()
        self._service = model.service(settings.service) if settings.service else None
        self._renames = self._service_renames()
        self._generated_names = {
            self._shape_name(shape) for shape in model if shape.type in _GENERATED_TYPES
        }
        self._generated_schema_names = {
            snake_case(self._shape_name(shape)).upper()
            for shape in model
            if shape.id.namespace != "smithy.api"
            and shape.type is not ShapeType.RESOURCE
        }

    def to_symbol(self, shape: Shape | Member) -> Symbol:
        if isinstance(shape, Member):
            target = self.model.expect(shape.target)
            symbol = self.to_symbol(target)
            # Enums intentionally use their wire type in member annotations so newly
            # added service values remain forwards compatible.
            if target.type is ShapeType.ENUM:
                return replace(symbol, name="str", namespace="", definition_file=None)
            if target.type is ShapeType.INT_ENUM:
                return replace(symbol, name="int", namespace="", definition_file=None)
            return symbol
        if (cached := self._cache.get(shape.id)) is not None:
            return cached
        if shape.id in self._resolving:
            return Symbol(name="Any", namespace="typing")
        self._resolving.add(shape.id)
        try:
            symbol = self._create_symbol(shape).with_property(SHAPE, shape)
            self._cache[shape.id] = symbol
            return symbol
        finally:
            self._resolving.remove(shape.id)

    def to_member_name(self, member: Member, *, container: Shape | None = None) -> str:
        name = snake_case(member.name)
        if keyword.iskeyword(name) or name in _MEMBER_RESERVED:
            name += "_"
        if container is not None and container.has_trait("smithy.api#error"):
            if name.lower() == "message":
                return "message"
            if name in _ERROR_MEMBER_RESERVED:
                name += "_"
        if container is not None and container.type in {
            ShapeType.ENUM,
            ShapeType.INT_ENUM,
        }:
            return name.upper()
        return name

    def union_member_symbol(self, container: Shape, member: Member) -> Symbol:
        name = f"{self._shape_name(container)}{pascal_case(member.name)}"
        if name in self._generated_names:
            name = f"{self._shape_name(container)}_{pascal_case(member.name)}"
        return self._generated(name, include_schema=False)

    def _create_symbol(self, shape: Shape) -> Symbol:
        if shape.type in _SIMPLE_TYPES:
            name, namespace, dependency = _SIMPLE_TYPES[shape.type]
            if name in self._generated_names:
                name = f"_{name}"
            if shape.type is ShapeType.BLOB and shape.has_trait("smithy.api#streaming"):
                streaming_name = (
                    "_StreamingBlob"
                    if "StreamingBlob" in self._generated_names
                    else "StreamingBlob"
                )
                return self._schema_property(
                    shape,
                    Symbol(
                        name=streaming_name,
                        namespace="smithy_core.aio.interfaces",
                        dependencies=(_SMITHY_CORE,),
                    ),
                )
            dependencies = (dependency,) if dependency is not None else ()
            return self._schema_property(
                shape, Symbol(name=name, namespace=namespace, dependencies=dependencies)
            )
        if shape.type is ShapeType.LIST:
            member = self.to_symbol(shape.member("member"))
            nullable = " | None" if shape.has_trait("smithy.api#sparse") else ""
            symbol = Symbol(
                name=f"list[{member.name}{nullable}]",
                references=(member,),
                dependencies=member.dependencies,
            )
            return self._collection_properties(
                shape, self._schema_property(shape, symbol)
            )
        if shape.type is ShapeType.MAP:
            value = self.to_symbol(shape.member("value"))
            nullable = " | None" if shape.has_trait("smithy.api#sparse") else ""
            symbol = Symbol(
                name=f"dict[str, {value.name}{nullable}]",
                references=(value,),
                dependencies=value.dependencies,
            )
            return self._collection_properties(
                shape, self._schema_property(shape, symbol)
            )
        if shape.type in _GENERATED_TYPES:
            symbol = self._schema_property(
                shape, self._generated(self._shape_name(shape))
            )
            if shape.type is ShapeType.UNION:
                unknown = f"{symbol.name}Unknown"
                if unknown in self._generated_names:
                    unknown = f"{symbol.name}_Unknown"
                symbol = symbol.with_property(
                    UNION_UNKNOWN, self._generated(unknown, include_schema=False)
                ).with_property(
                    DESERIALIZER,
                    self._generated(
                        f"{'' if shape.has_trait('smithy.api#streaming') else '_'}"
                        f"{symbol.name}Deserializer",
                        include_schema=False,
                    ),
                )
            return symbol
        if shape.type is ShapeType.OPERATION:
            constant = snake_case(self._shape_name(shape)).upper()
            return self._schema_property(
                shape, self._generated(constant)
            ).with_property(
                OPERATION_METHOD,
                Symbol(
                    name=snake_case(self._shape_name(shape)),
                    namespace=f"{self.settings.module_name}.client",
                ),
            )
        if shape.type is ShapeType.SERVICE:
            return self._schema_property(
                shape,
                Symbol(
                    name=f"{self._shape_name(shape)}Client",
                    namespace=f"{self.settings.module_name}.client",
                    definition_file=PurePosixPath(
                        f"src/{self.settings.module_name}/client.py"
                    ),
                ),
            )
        return Symbol(name="Any", namespace="typing")

    def _generated(self, name: str, *, include_schema: bool = True) -> Symbol:
        symbol = Symbol(
            name=name,
            namespace=f"{self.settings.module_name}.models",
            definition_file=PurePosixPath(f"src/{self.settings.module_name}/models.py"),
        )
        return symbol

    def _schema_property(self, shape: Shape, symbol: Symbol) -> Symbol:
        if shape.id.namespace == "smithy.api":
            name = snake_case(shape.id.name).upper()
            schema = Symbol(
                name=f"_{name}" if name in self._generated_schema_names else name,
                namespace="smithy_core.prelude",
                dependencies=(_SMITHY_CORE,),
            )
        else:
            schema = Symbol(
                name=snake_case(self._shape_name(shape)).upper(),
                namespace=f"{self.settings.module_name}._private.schemas",
                definition_file=PurePosixPath(
                    f"src/{self.settings.module_name}/_private/schemas.py"
                ),
            )
        return symbol.with_property(SCHEMA, schema)

    def _collection_properties(self, shape: Shape, symbol: Symbol) -> Symbol:
        name = snake_case(self._shape_name(shape))
        return symbol.with_property(
            SERIALIZER, self._generated(f"_serialize_{name}", include_schema=False)
        ).with_property(
            DESERIALIZER, self._generated(f"_deserialize_{name}", include_schema=False)
        )

    def _shape_name(self, shape: Shape) -> str:
        name = self._renames.get(shape.id, shape.id.name)
        result = pascal_case(name)
        return (
            f"{result}_"
            if result in _CLASS_RESERVED or keyword.iskeyword(result)
            else result
        )

    def _service_renames(self) -> dict[ShapeID, str]:
        if self._service is None:
            return {}
        rename = self._service.attributes.get("rename", {})
        if not isinstance(rename, dict):
            return {}
        return {
            ShapeID.parse(shape_id): local_name
            for shape_id, local_name in rename.items()
            if isinstance(local_name, str)
        }


def snake_case(value: str) -> str:
    """Convert Smithy identifiers to stable snake_case names."""
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    value = re.sub(r"[^A-Za-z0-9]+", "_", value)
    return value.strip("_").lower() or "_"


def pascal_case(value: str) -> str:
    parts = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value).replace("_", " ").split()
    return "".join(part[:1].upper() + part[1:] for part in parts) or "_"
