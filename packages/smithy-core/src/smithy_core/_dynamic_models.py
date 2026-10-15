#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Build model classes on demand from compact schemas.

A generated ``models.py`` is a thin module: it binds one :py:class:`ModelRegistry`
to its ``_private.schemas`` module and defers to ``registry.build(name)`` from a
module ``__getattr__``. No per-shape class source is emitted; the registry
synthesizes the dataclass (or union variants, enum, or error class) on first
access and the generic codec here serializes it by walking its hydrated schema.

The per-member reader/writer is resolved once and cached on the member schema via
a :py:class:`SchemaExtension`, so steady-state serde does the same work as
straight-line generated code reached through a cached callable rather than a type
match on every call.
"""

from __future__ import annotations

import datetime
from base64 import b64decode
from collections.abc import Collection
from dataclasses import field as _field
from dataclasses import make_dataclass
from decimal import Decimal
from enum import IntEnum, StrEnum
from types import ModuleType
from typing import TYPE_CHECKING, Any, cast, dataclass_transform

from ._model_naming import member_field_name, union_unknown_name, variant_class_name
from ._schema_compact import hydrate
from .deserializers import ShapeDeserializer
from .exceptions import ModeledError
from .schemas import Schema, SchemaExtension
from .serializers import ShapeSerializer
from .shapes import ShapeID, ShapeType
from .traits import (
    DefaultTrait,
    EnumValueTrait,
    ErrorTrait,
    RequiredTrait,
    SensitiveTrait,
    SparseTrait,
    StreamingTrait,
)
from .types import UnknownEnumMixin

if TYPE_CHECKING:
    from collections.abc import Callable

type _Writer = "Callable[[ShapeSerializer, Schema, Any], None]"
type _Reader = "Callable[[ShapeDeserializer, Schema], Any]"


def _scalar(write_name: str, read_name: str) -> tuple[_Writer, _Reader]:
    def w(s: ShapeSerializer, m: Schema, v: Any) -> None:
        getattr(s, write_name)(m, v)

    def r(d: ShapeDeserializer, m: Schema) -> Any:
        return getattr(d, read_name)(m)

    return w, r


_SCALAR_CODECS: dict[ShapeType, tuple[_Writer, _Reader]] = {
    ShapeType.BOOLEAN: _scalar("write_boolean", "read_boolean"),
    ShapeType.STRING: _scalar("write_string", "read_string"),
    ShapeType.ENUM: _scalar("write_string", "read_string"),
    ShapeType.TIMESTAMP: _scalar("write_timestamp", "read_timestamp"),
    ShapeType.BLOB: _scalar("write_blob", "read_blob"),
    ShapeType.BYTE: _scalar("write_byte", "read_byte"),
    ShapeType.SHORT: _scalar("write_short", "read_short"),
    ShapeType.INTEGER: _scalar("write_integer", "read_integer"),
    ShapeType.INT_ENUM: _scalar("write_integer", "read_integer"),
    ShapeType.LONG: _scalar("write_long", "read_long"),
    ShapeType.FLOAT: _scalar("write_float", "read_float"),
    ShapeType.DOUBLE: _scalar("write_double", "read_double"),
    ShapeType.BIG_INTEGER: _scalar("write_big_integer", "read_big_integer"),
    ShapeType.BIG_DECIMAL: _scalar("write_big_decimal", "read_big_decimal"),
    ShapeType.DOCUMENT: _scalar("write_document", "read_document"),
}

_PY_SCALAR: dict[ShapeType, Any] = {
    ShapeType.BOOLEAN: bool,
    ShapeType.STRING: str,
    ShapeType.ENUM: str,
    ShapeType.TIMESTAMP: datetime.datetime,
    ShapeType.BLOB: bytes,
    ShapeType.BYTE: int,
    ShapeType.SHORT: int,
    ShapeType.INTEGER: int,
    ShapeType.INT_ENUM: int,
    ShapeType.LONG: int,
    ShapeType.FLOAT: float,
    ShapeType.DOUBLE: float,
    ShapeType.BIG_INTEGER: int,
    ShapeType.BIG_DECIMAL: Decimal,
    ShapeType.DOCUMENT: Any,
    ShapeType.LIST: list,
    ShapeType.MAP: dict,
}


# Sentinel: a mandatory member (no dataclass default); emitted as a 2-tuple field.
_MANDATORY = object()

# Client error-correction defaults by scalar shape type (Smithy spec § client error
# correction). Mirrors MemberErrorCorrectionGenerator. Enum/int-enum fill the raw
# placeholder the dynamic serde uses ("" / -1), not an enum instance.
_CORRECTION_SCALARS: dict[ShapeType, Any] = {
    ShapeType.BOOLEAN: lambda: False,
    ShapeType.STRING: lambda: "",
    ShapeType.ENUM: lambda: "",
    ShapeType.INT_ENUM: lambda: -1,
    ShapeType.BYTE: lambda: 0,
    ShapeType.SHORT: lambda: 0,
    ShapeType.INTEGER: lambda: 0,
    ShapeType.LONG: lambda: 0,
    ShapeType.BIG_INTEGER: lambda: 0,
    ShapeType.FLOAT: lambda: 0.0,
    ShapeType.DOUBLE: lambda: 0.0,
    ShapeType.BIG_DECIMAL: lambda: Decimal(0),
    ShapeType.BLOB: lambda: b"",
    ShapeType.TIMESTAMP: lambda: datetime.datetime.fromtimestamp(0, tz=datetime.UTC),
    ShapeType.LIST: list,
    ShapeType.MAP: dict,
    ShapeType.DOCUMENT: lambda: _document(None),
}


def _document(value: Any) -> Any:
    from .documents import Document

    return Document(value)


# The generator synthesizes @input/@output onto operation I/O structures (see
# SchemaGenerator.filterTraits), so these are the authoritative nullability signals.
_INPUT_TRAIT = ShapeID("smithy.api#input")
_OUTPUT_TRAIT = ShapeID("smithy.api#output")


@dataclass_transform(kw_only_default=True)
class ModelRegistry:
    """Builds and caches model classes for one generated client from its schemas.

    CAUTION: ``schemas_module`` must be the client's ``_private.schemas``. Generated
    clients pass a codegen-built ``index`` and ``shape_names`` so no shape is hydrated
    until first requested; absent those, the registry falls back to hydrating every
    schema once to build the index.
    """

    def __init__(
        self,
        schemas_module: ModuleType,
        renames: dict[str, str] | None = None,
        *,
        index: dict[str, str] | None = None,
        shape_names: Collection[str] | None = None,
        service_error: str | None = None,
    ) -> None:
        self._schemas = schemas_module
        self._renames = renames or {}
        self._classes: dict[str, type] = {}
        self._union_schemas: dict[str, Schema] = {}
        # A codegen-supplied index (name -> schema-const, variant/unknown names already
        # disambiguated) lets the registry resolve a build() without hydrating every
        # schema in the module just to map names; the scanning fallback hydrates all.
        self._index: dict[str, str] | None = index
        self._shape_names: set[str] = set(shape_names) if shape_names else set()
        # Generated clients name their per-service error base (a ModeledError subclass
        # emitted into the models module). Modeled errors extend it so `except
        # ServiceError` catches them; a hand-built registry omits it and falls back to
        # ModeledError.
        self._service_error_name = service_error
        self._codec = SchemaExtension(self._resolve_member_codec)
        self._field_names_ext = SchemaExtension(self._compute_field_names)

    def _error_base(self) -> type:
        if self._service_error_name is None:
            return ModeledError
        return getattr(self._models_module, self._service_error_name)

    @property
    def _models_module(self) -> ModuleType:
        import sys

        return sys.modules[self._schemas.__name__.rsplit(".", 2)[0] + ".models"]

    def _field_names(self, schema: Schema) -> tuple[str, ...]:
        return schema.get_extension(self._field_names_ext)

    def _is_input(self, schema: Schema) -> bool:
        return schema.get_trait(_INPUT_TRAIT) is not None

    def _is_output(self, schema: Schema) -> bool:
        return schema.get_trait(_OUTPUT_TRAIT) is not None

    def _compute_field_names(self, schema: Schema) -> tuple[str, ...]:
        self._ensure_index()
        is_error = schema.get_trait(ErrorTrait) is not None
        is_enum = schema.shape_type in (ShapeType.ENUM, ShapeType.INT_ENUM)
        carries_md = is_error or self._is_output(schema)
        return tuple(
            member_field_name(
                member.expect_member_name(),
                is_error=is_error,
                carries_response_metadata=carries_md,
                is_enum=is_enum,
            )
            for member in schema.members_by_index
        )

    def build(self, name: str) -> type:
        cached = self._classes.get(name)
        if cached is not None:
            return cached
        index = self._ensure_index()
        # Event-stream union deserializer helper: _<Union>Deserializer().deserialize(d).
        if name.startswith("_") and name.endswith("Deserializer"):
            union_name = name[1 : -len("Deserializer")]
            if union_name in index:
                built = self._build_union_deserializer(union_name)
                self._classes[name] = built
                return built
        renamed = self._renames.get(name)
        if renamed is not None:
            const = renamed
        elif name in index:
            const = index[name]
        else:
            # smithy.api#Unit is a prelude empty struct used as a union variant target;
            # it is not emitted as a generated schema constant, so build it from the prelude.
            if name == "Unit":
                from .prelude import UNIT

                built = self._build_struct("Unit", UNIT)
                built.__module__ = self._schemas.__name__.rsplit(".", 2)[0] + ".models"
                self._classes[name] = built
                return built
            raise AttributeError(name)
        schema = hydrate(getattr(self._schemas, const))
        if schema.shape_type == ShapeType.UNION:
            self._build_union(schema.id.name, schema)
            return self._classes[name]
        if schema.shape_type in (ShapeType.ENUM, ShapeType.INT_ENUM):
            built: type = self._build_enum(name, schema)
        else:
            built = self._build_struct(name, schema)
        built.__module__ = self._schemas.__name__.rsplit(".", 2)[0] + ".models"
        self._classes[name] = built
        return built

    def _build_union_deserializer(self, union_name: str) -> type:
        # Ensure the union (and its variants + schema) are registered.
        self.build(union_name)
        registry = self

        def deserialize(self: Any, deserializer: ShapeDeserializer) -> Any:
            return registry._deserialize_union(deserializer, union_name)

        return type(f"_{union_name}Deserializer", (), {"deserialize": deserialize})

    def serialize_members(
        self, instance: Any, serializer: ShapeSerializer, schema: Schema
    ) -> None:
        field_names = self._field_names(schema)
        for i, member in enumerate(schema.members_by_index):
            value = getattr(instance, field_names[i])
            if value is None:
                continue
            writer, _ = member.get_extension(self._codec)
            writer(serializer, member, value)

    def deserialize_kwargs(
        self, deserializer: ShapeDeserializer, schema: Schema
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        by_index = schema.members_by_index
        field_names = self._field_names(schema)

        def consume(member_schema: Schema, de: ShapeDeserializer) -> None:
            idx = member_schema.expect_member_index()
            _, reader = by_index[idx].get_extension(self._codec)
            kwargs[field_names[idx]] = reader(de, by_index[idx])

        deserializer.read_struct(schema, consumer=consume)
        if not self._is_input(schema):
            self._error_correct(schema, kwargs, field_names, by_index)
        return kwargs

    def _error_correct(
        self,
        schema: Schema,
        kwargs: dict[str, Any],
        field_names: tuple[str, ...],
        by_index: tuple[Schema, ...],
    ) -> None:
        """Fill @required members a non-compliant server omitted (Smithy client error correction)."""
        for i, member in enumerate(by_index):
            fname = field_names[i]
            if fname in kwargs:
                continue
            if member.get_trait(RequiredTrait) is None:
                continue
            if member.get_trait(DefaultTrait) is not None:
                continue
            kwargs[fname] = self._correction_default(member)

    def _correction_default(self, member: Schema) -> Any:
        st = member.shape_type
        if st == ShapeType.STRUCTURE:
            target = member.expect_member_target().id.name
            return self.build(target)._smithy_default()  # type: ignore[attr-defined]
        if st == ShapeType.UNION:
            target = member.expect_member_target().id.name
            return self.build(union_unknown_name(target, self._shape_names))(tag="")
        return _CORRECTION_SCALARS[st]()

    def _build_struct(self, name: str, schema: Schema) -> type:
        is_error = schema.get_trait(ErrorTrait) is not None
        # Per Smithy @input structure constraints, every member of an input
        # structure is effectively optional regardless of @required; only
        # non-input structures make a @required, non-@default member mandatory.
        input_nullable = self._is_input(schema)
        field_names = self._field_names(schema)
        fields: list[Any] = []
        for i, member in enumerate(schema.members_by_index):
            spec = self._field_spec(member, input_nullable)
            if spec is _MANDATORY:
                fields.append((field_names[i], _py_type(member)))
            else:
                fields.append((field_names[i], _py_type(member), spec))
        bases: tuple[type, ...] = (self._error_base(),) if is_error else ()
        # Operation outputs carry a non-modeled response_metadata attribute, excluded
        # from eq and repr. Errors inherit it from ModeledError instead.
        if not is_error and self._is_output(schema):
            from .response import EMPTY_RESPONSE_METADATA, ResponseMetadata

            fields.append(
                (
                    "response_metadata",
                    ResponseMetadata,
                    _field(default=EMPTY_RESPONSE_METADATA, repr=False, compare=False),
                )
            )
        return make_dataclass(
            name,
            fields,
            bases=bases,
            kw_only=True,
            namespace=self._struct_namespace(schema),
        )

    def _build_enum(self, name: str, schema: Schema) -> type:
        # Mirrors EnumGenerator/IntEnumGenerator: UnknownEnumMixin first base, member
        # name from the symbol-provider namer, wire value from the enumValue trait (the
        # member name is only the default when the trait is absent).
        is_int = schema.shape_type is ShapeType.INT_ENUM
        base: type = IntEnum if is_int else StrEnum
        members: dict[str, Any] = {}
        for member in schema.members_by_index:
            member_name = member.expect_member_name()
            value_trait = member.get_trait(EnumValueTrait)
            value = value_trait.value if value_trait is not None else member_name
            members[
                member_field_name(
                    member_name,
                    is_error=False,
                    carries_response_metadata=False,
                    is_enum=True,
                )
            ] = value
        bases = (UnknownEnumMixin, base)
        meta = type(base)
        ns = cast("dict[str, Any]", meta.__prepare__(name, bases))
        for field_name, value in members.items():
            ns[field_name] = value
        return cast(type, meta(name, bases, ns))

    def _field_spec(self, member: Schema, input_nullable: bool) -> Any:
        """The dataclass default for a member.

        A member is mandatory (no default) only when its container is NOT an input
        structure, it is @required, and it has no @default. Input-structure members
        are always nullable (``| None = None``) per the Smithy @input constraints.
        Sensitive members get repr=False; @default values are typed; list/map/document
        defaults use default_factory.
        """
        sensitive = member.get_trait(SensitiveTrait) is not None
        default_trait = member.get_trait(DefaultTrait)
        required = member.get_trait(RequiredTrait) is not None

        if default_trait is None:
            if required and not input_nullable:
                return _field(repr=False) if sensitive else _MANDATORY
            return _field(default=None, repr=False) if sensitive else None

        factory = self._default_factory(member, default_trait)
        if factory is not None:
            if sensitive:
                return _field(default_factory=factory, repr=False)
            return _field(default_factory=factory)
        value = self._default_value(member, default_trait)
        return _field(default=value, repr=False) if sensitive else value

    def _default_value(self, member: Schema, trait: DefaultTrait) -> Any:
        st = member.shape_type
        raw = trait.value
        if raw is None:
            return None  # null default -> None (member is nullable)
        if st == ShapeType.TIMESTAMP:
            return _parse_timestamp(member, raw)
        if st == ShapeType.BLOB:
            return b64decode(raw)  # type: ignore[arg-type]
        if st in (ShapeType.ENUM, ShapeType.INT_ENUM):
            return (
                raw  # built value is the raw string/int; enum classes are StrEnum/int
            )
        return raw

    def _default_factory(self, member: Schema, trait: DefaultTrait) -> Any:
        st = member.shape_type
        if st == ShapeType.LIST:
            return list
        if st == ShapeType.MAP:
            return dict
        if st == ShapeType.DOCUMENT:
            # Matches StructureGenerator: a document @default resolves to Document(value).
            # The compact schema preserves an object default as a Mapping, an array as a
            # tuple, and null as None (a non-None Document(None)).
            from collections.abc import Mapping

            raw = trait.value
            value: Any
            if isinstance(raw, Mapping):
                value = dict(raw)
            elif isinstance(raw, (tuple, list)):
                value = list(raw)
            else:
                value = raw
            return lambda: _document(value)
        return None

    def _build_union(self, name: str, schema: Schema) -> None:
        for member in schema.members_by_index:
            vname = variant_class_name(
                name, member.expect_member_name(), self._shape_names
            )
            self._classes[vname] = self._build_variant(
                vname, schema, member.expect_member_index()
            )
        unknown = union_unknown_name(name, self._shape_names)
        self._classes[unknown] = make_dataclass(unknown, [("tag", str)])
        self._union_schemas[name] = schema
        # A tagged union has no single runtime class; expose a marker so the name
        # resolves. Static code uses the .pyi union alias, not this object.
        self._classes[name] = make_dataclass(name, [])

    def _build_variant(self, vname: str, union_schema: Schema, index: int) -> type:
        registry = self

        def serialize(self: Any, serializer: ShapeSerializer) -> None:
            serializer.write_struct(union_schema, self)

        def serialize_members(self: Any, serializer: ShapeSerializer) -> None:
            member = union_schema.members_by_index[index]
            writer, _ = member.get_extension(registry._codec)
            writer(serializer, member, self.value)

        @classmethod  # type: ignore[misc]
        def deserialize(cls: type, deserializer: ShapeDeserializer) -> Any:
            member = union_schema.members_by_index[index]
            _, reader = member.get_extension(registry._codec)
            return cls(value=reader(deserializer, member))

        return make_dataclass(
            vname,
            [("value", Any)],
            namespace={
                "serialize": serialize,
                "serialize_members": serialize_members,
                "deserialize": deserialize,
            },
        )

    def _struct_namespace(self, schema: Schema) -> dict[str, Any]:
        registry = self

        def serialize(self: Any, serializer: ShapeSerializer) -> None:
            serializer.write_struct(schema, self)

        def serialize_members(self: Any, serializer: ShapeSerializer) -> None:
            registry.serialize_members(self, serializer, schema)

        @classmethod  # type: ignore[misc]
        def deserialize(cls: type, deserializer: ShapeDeserializer) -> Any:
            return cls(**registry.deserialize_kwargs(deserializer, schema))

        @classmethod  # type: ignore[misc]
        def _smithy_default(cls: type) -> Any:
            field_names = registry._field_names(schema)
            by_index = schema.members_by_index
            kwargs: dict[str, Any] = {}
            registry._error_correct(schema, kwargs, field_names, by_index)
            return cls(**kwargs)

        return {
            "serialize": serialize,
            "serialize_members": serialize_members,
            "deserialize": deserialize,
            "_smithy_default": _smithy_default,
        }

    def _deserialize_union(self, deserializer: ShapeDeserializer, name: str) -> Any:
        schema = self._union_schemas[name]
        by_index = schema.members_by_index
        result: list[Any] = [None]

        def consume(member_schema: Schema, de: ShapeDeserializer) -> None:
            member = by_index[member_schema.expect_member_index()]
            _, reader = member.get_extension(self._codec)
            variant = self.build(
                variant_class_name(name, member.expect_member_name(), self._shape_names)
            )
            result[0] = variant(value=reader(de, member))

        deserializer.read_struct(schema, consumer=consume)
        if result[0] is None:
            result[0] = self.build(union_unknown_name(name, self._shape_names))(
                tag="unknown"
            )
        return result[0]

    def _is_streaming(self, member: Schema) -> bool:
        try:
            target = member.expect_member_target()
        except Exception:
            return False
        return target.get_trait(StreamingTrait) is not None

    def _resolve_member_codec(self, member: Schema) -> tuple[_Writer, _Reader]:
        st = member.shape_type
        if st == ShapeType.BLOB and self._is_streaming(member):
            return _scalar("write_data_stream", "read_data_stream")
        scalar = _SCALAR_CODECS.get(st)
        if scalar is not None:
            return scalar
        if st == ShapeType.STRUCTURE:
            target = member.expect_member_target().id.name

            def wr(s: ShapeSerializer, m: Schema, v: Any) -> None:
                s.write_struct(m, v)

            def rr(d: ShapeDeserializer, m: Schema) -> Any:
                from typing import cast

                from .deserializers import DeserializeableShape

                return cast(
                    "type[DeserializeableShape]", self.build(target)
                ).deserialize(d)

            return wr, rr
        if st == ShapeType.UNION:
            target = member.expect_member_target().id.name
            self.build(target)  # ensure union schema is registered

            def wu(s: ShapeSerializer, m: Schema, v: Any) -> None:
                s.write_struct(m, v)

            def ru(d: ShapeDeserializer, m: Schema) -> Any:
                return self._deserialize_union(d, target)

            return wu, ru
        if st == ShapeType.LIST:
            collection = member.expect_member_target()
            elem = collection.members_by_index[0]
            return self._list_codec(elem, collection.get_trait(SparseTrait) is not None)
        if st == ShapeType.MAP:
            collection = member.expect_member_target()
            value_member = collection.members["value"]
            return self._map_codec(
                value_member, collection.get_trait(SparseTrait) is not None
            )
        raise NotImplementedError(f"no codec for shape type {st}")

    def _list_codec(self, elem: Schema, sparse: bool) -> tuple[_Writer, _Reader]:
        def w(s: ShapeSerializer, m: Schema, v: list[Any]) -> None:
            ew, _ = elem.get_extension(self._codec)
            with s.begin_list(m, len(v)) as ls:
                for e in v:
                    if sparse and e is None:
                        ls.write_null(elem)
                    else:
                        ew(ls, elem, e)

        def r(d: ShapeDeserializer, m: Schema) -> list[Any]:
            _, er = elem.get_extension(self._codec)
            out: list[Any] = []

            def read_one(dd: ShapeDeserializer) -> None:
                if dd.is_null():
                    dd.read_null()
                    if sparse:
                        out.append(None)
                else:
                    out.append(er(dd, elem))

            d.read_list(m, read_one)
            return out

        return w, r

    def _map_codec(self, value_member: Schema, sparse: bool) -> tuple[_Writer, _Reader]:
        def w(s: ShapeSerializer, m: Schema, v: dict[str, Any]) -> None:
            vw, _ = value_member.get_extension(self._codec)
            with s.begin_map(m, len(v)) as ms:
                for k, val in v.items():
                    if sparse and val is None:
                        ms.entry(k, lambda vs: vs.write_null(value_member))
                    else:
                        ms.entry(k, lambda vs, _v=val: vw(vs, value_member, _v))

        def r(d: ShapeDeserializer, m: Schema) -> dict[str, Any]:
            _, vr = value_member.get_extension(self._codec)
            out: dict[str, Any] = {}

            def read_entry(k: str, dd: ShapeDeserializer) -> None:
                if dd.is_null():
                    dd.read_null()
                    if sparse:
                        out[k] = None
                else:
                    out[k] = vr(dd, value_member)

            d.read_map(m, read_entry)
            return out

        return w, r

    def _ensure_index(self) -> dict[str, str]:
        if self._index is None:
            # First pass: every real shape name, so variant-name disambiguation
            # (PythonSymbolProvider.memberShape) can see the whole model.
            consts: list[tuple[str, Schema]] = []
            shape_names: set[str] = set()
            for const in dir(self._schemas):
                if not (const.replace("_", "").isupper() and const[:1].isalpha()):
                    continue
                tup = getattr(self._schemas, const)
                if not isinstance(tup, tuple):
                    continue
                schema = hydrate(cast("tuple[Any, ...]", tup))
                consts.append((const, schema))
                shape_names.add(schema.id.name)
            self._shape_names = shape_names
            index: dict[str, str] = {}
            for const, schema in consts:
                index.setdefault(schema.id.name, const)
                if schema.shape_type == ShapeType.UNION:
                    for mname in schema.members:
                        index.setdefault(
                            variant_class_name(schema.id.name, mname, shape_names),
                            const,
                        )
                    index.setdefault(
                        union_unknown_name(schema.id.name, shape_names), const
                    )
            self._index = index
        return self._index


def _py_type(member: Schema) -> Any:
    return _PY_SCALAR.get(member.shape_type, Any)


def _parse_timestamp(member: Schema, raw: Any) -> datetime.datetime:
    """Build a datetime from a @default node, honoring @timestampFormat.

    A numeric node is epoch seconds; a string node is RFC3339 (or the member's
    declared timestamp format). Matches CodegenUtils.parseTimestampNode.
    """
    from .utils import ensure_utc, epoch_seconds_to_datetime

    if isinstance(raw, (int, float)):
        return epoch_seconds_to_datetime(raw)
    return ensure_utc(datetime.datetime.fromisoformat(str(raw)))
