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
from collections.abc import Collection, Mapping, Sequence
from dataclasses import field as _field
from dataclasses import make_dataclass
from decimal import Decimal
from enum import IntEnum, StrEnum
from threading import RLock
from types import ModuleType
from typing import TYPE_CHECKING, Any, cast, dataclass_transform

from ._model_naming import (
    escape_input_member_names,
    member_field_name,
    to_snake_case,
    union_unknown_name,
    variant_class_name,
)
from ._schema_compact import hydrate
from .deserializers import ShapeDeserializer
from .exceptions import ModeledError, SerializationError, SmithyError
from .schemas import Schema, SchemaExtension
from .serializers import ShapeSerializer
from .shapes import ShapeID, ShapeType
from .traits import (
    DefaultTrait,
    EnumValueTrait,
    ErrorTrait,
    IdempotencyTokenTrait,
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
# Converts or checks a member's value: (value, redact, in_model) -> value. ``redact``
# is set under a sensitive shape, where keys the caller wrote stay out of errors.
# ``in_model`` is set inside a model the caller built, which is checked as it is.
type _InputConverter = "Callable[[Any, bool, bool], Any]"

# Sequences that are never meant as a list of their elements.
_NOT_A_LIST = (str, bytes, bytearray, memoryview)

# The dictionary form of a shape is named with this suffix, and the form an async
# client takes for an input with a streaming body also with this prefix.
_PARAMS_SUFFIX = "Params"
_ASYNC_PREFIX = "Async"

# Path segments shown for a value nested too deeply to be converted.
_MAX_DEEP_PATH = 6


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
        renames: Mapping[str, str] | None = None,
        *,
        index: Mapping[str, str] | None = None,
        target_names: Mapping[str, str] | None = None,
        shape_names: Collection[str] | None = None,
        service_error: str | None = None,
    ) -> None:
        self._schemas = schemas_module
        self._renames = dict(renames or {})
        self._classes: dict[str, type] = {}
        self._union_schemas: dict[str, Schema] = {}
        # Reentrant because build() recurses: unions build their variants, and a
        # member codec resolves nested targets through build(). Guards the
        # read-miss-build-store on _classes so concurrent builders of one shape
        # cannot publish two distinct class objects.
        self._lock = RLock()
        # A codegen-supplied index (name -> schema-const, variant/unknown names already
        # disambiguated) lets the registry resolve a build() without hydrating every
        # schema in the module just to map names; the scanning fallback hydrates all.
        self._index = dict(index) if index is not None else None
        # Full shape ID -> generated public model name. Full IDs keep member-target
        # resolution unambiguous when service renames distinguish same-named shapes
        # from different namespaces.
        self._target_names = dict(target_names or {})
        self._renamed_schemas = {
            schema_name: model_name for model_name, schema_name in self._renames.items()
        }
        self._shape_names: set[str] = set(shape_names) if shape_names else set()
        # Generated clients name their per-service error base (a ModeledError subclass
        # emitted into the models module). Modeled errors extend it so `except
        # ServiceError` catches them; a hand-built registry omits it and falls back to
        # ModeledError.
        self._service_error_name = service_error
        if service_error is not None:
            self._shape_names.add(service_error)
        self._codec = SchemaExtension(self._resolve_member_codec)
        self._field_names_ext = SchemaExtension(self._compute_field_names)
        self._input_plan = SchemaExtension(self._resolve_input_plan)
        self._input_converter = SchemaExtension(self._resolve_input_converter)

    def build(self, name: str) -> type:
        cached = self._classes.get(name)
        if cached is not None:
            return cached
        with self._lock:
            cached = self._classes.get(name)
            if cached is not None:
                return cached
            index = self._ensure_index()
            # Event-stream union deserializer helper: _<Union>Deserializer().deserialize(d).
            if name.startswith("_") and name.endswith("Deserializer"):
                union_name = name[1 : -len("Deserializer")]
                if union_name in index or union_name in self._renames:
                    built = self._build_union_deserializer(union_name)
                    self._classes[name] = built
                    return built
            module = self._models_module_name
            renamed = self._renames.get(name)
            if renamed is not None:
                const = renamed
            elif name in index:
                const = index[name]
            else:
                # smithy.api#Unit is a prelude empty struct used as a union variant
                # target; it is not emitted as a generated schema constant, so build it
                # from the prelude.
                if name == "Unit":
                    from .prelude import UNIT

                    built = self._build_struct("Unit", UNIT)
                    built.__module__ = module
                    self._classes[name] = built
                    return built
                # The dictionary form of an input shape is a TypedDict in the stub
                # and a plain dict at runtime, so it costs nothing to import.
                if self._is_params_name(name):
                    self._classes[name] = dict
                    return dict
                raise AttributeError(name)
            schema = hydrate(getattr(self._schemas, const))
            canonical = self._renamed_schemas.get(const)
            if schema.shape_type == ShapeType.UNION:
                self._build_union(canonical or schema.id.name, schema)
                built = self._classes.get(name)
                if built is None and name == schema.id.name:
                    built = self._classes[canonical or schema.id.name]
                if built is None:
                    raise AttributeError(name)
                self._classes[name] = built
                return built
            canonical = canonical or name
            if cached := self._classes.get(canonical):
                self._classes[name] = cached
                return cached
            if schema.shape_type in (ShapeType.ENUM, ShapeType.INT_ENUM):
                built = self._build_enum(canonical, schema)
            else:
                built = self._build_struct(canonical, schema)
            built.__module__ = module
            self._classes[canonical] = built
            self._classes[name] = built
            return built

    def serialize_members(
        self, instance: Any, serializer: ShapeSerializer, schema: Schema
    ) -> None:
        field_names = self._field_names(schema)
        for i, member in enumerate(schema.members_by_index):
            if self._is_event_stream_member(member):
                continue
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
            member = by_index[idx]
            if self._is_event_stream_member(member):
                return
            _, reader = member.get_extension(self._codec)
            kwargs[field_names[idx]] = reader(de, member)

        deserializer.read_struct(schema, consumer=consume)
        if not self._is_input(schema):
            self._error_correct(schema, kwargs, field_names, by_index)
        return kwargs

    def build_input(
        self, schema: Schema, members: Mapping[str, Any], operation: str
    ) -> Any:
        """Build an operation's input model from its keyword arguments.

        Dictionaries are converted to the models they stand for, at any depth.
        Model instances are checked and passed through as they are, never copied
        or changed. ``None`` is the same as omitting a member, which takes the
        member's default if it has one. An idempotency token left unset stays
        unset here; the request pipeline generates it.

        :param schema: The schema of the operation's input structure.
        :param members: The keyword arguments, keyed by generated member name.
        :param operation: The operation's name, used in error messages.
        :raises TypeError: If a key is unknown, a member that must be set is
            missing, or a value has the wrong shape. The message gives the path to
            the problem and never includes a value, nor, under a sensitive shape,
            a key the caller wrote.
        """
        try:
            return self._input_struct(
                schema, members, schema.get_trait(SensitiveTrait) is not None
            )
        except _InputError as error:
            segments = error.path[::-1]
            if error.too_deep and len(segments) > _MAX_DEEP_PATH:
                segments = [*segments[:_MAX_DEEP_PATH], "..."]
            path = "".join(segments).lstrip(".")
            where = f" at {path}" if path else ""
            raise TypeError(
                f"Invalid {operation} input{where}: {error.message}"
            ) from None
        except RecursionError:
            raise TypeError(
                f"Invalid {operation} input: {_too_deep('').message}"
            ) from None

    def _error_base(self) -> type:
        if self._service_error_name is None:
            return ModeledError
        return getattr(self._models_module, self._service_error_name)

    @property
    def _models_module_name(self) -> str:
        return self._schemas.__name__.rsplit(".", 2)[0] + ".models"

    @property
    def _models_module(self) -> ModuleType:
        import sys

        return sys.modules[self._models_module_name]

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
        names = tuple(
            member_field_name(
                member.expect_member_name(),
                is_error=is_error,
                carries_response_metadata=carries_md,
                is_enum=is_enum,
            )
            for member in schema.members_by_index
        )
        return escape_input_member_names(names) if self._is_input(schema) else names

    def _is_params_name(self, name: str) -> bool:
        """Whether a name is the dictionary form of a modeled shape.

        CAUTION: InputParams in the code generator assigns these names. A form is
        named after its shape, then as many underscores as it takes to not be the
        name of a modeled shape, then ``Params``. A shape's own name may end in
        underscores too, so they are taken off one at a time until a shape matches.
        """
        if not name.endswith(_PARAMS_SUFFIX):
            return False
        shape = name[: -len(_PARAMS_SUFFIX)]
        while True:
            # smithy.api#Unit has no schema constant; see build().
            if self._const(shape) is not None or shape == "Unit":
                return True
            if shape.startswith(_ASYNC_PREFIX) and self._has_streaming_body(
                shape[len(_ASYNC_PREFIX) :]
            ):
                return True
            if not shape.endswith("_"):
                return False
            shape = shape[:-1]

    def _const(self, name: str) -> str | None:
        """The schema constant of a generated model name, if it is one."""
        return self._renames.get(name) or self._ensure_index().get(name)

    def _has_streaming_body(self, name: str) -> bool:
        """Whether a name is an operation input with a streaming blob member."""
        const = self._const(name)
        if const is None:
            return False
        schema = hydrate(getattr(self._schemas, const))
        return self._is_input(schema) and any(
            member.shape_type is ShapeType.BLOB and self._is_streaming(member)
            for member in schema.members_by_index
        )

    def _build_union_deserializer(self, union_name: str) -> type:
        # Ensure the union (and its variants + schema) are registered.
        self.build(union_name)
        registry = self

        def deserialize(self: Any, deserializer: ShapeDeserializer) -> Any:
            return registry._deserialize_union(deserializer, union_name)

        return type(f"_{union_name}Deserializer", (), {"deserialize": deserialize})

    def _error_correct(
        self,
        schema: Schema,
        kwargs: dict[str, Any],
        field_names: tuple[str, ...],
        by_index: tuple[Schema, ...],
    ) -> None:
        """Fill @required members a non-compliant server omitted (Smithy client error correction)."""
        for i, member in enumerate(by_index):
            if self._is_event_stream_member(member):
                continue
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
            target = self._target_name(member.expect_member_target())
            return self.build(target)._smithy_default()  # type: ignore[attr-defined]
        if st == ShapeType.UNION:
            target = self._target_name(member.expect_member_target())
            return self.build(self._union_unknown_name(target))(tag="")
        return _CORRECTION_SCALARS[st]()

    def _build_struct(self, name: str, schema: Schema) -> type:
        error_trait = schema.get_trait(ErrorTrait)
        is_error = error_trait is not None
        # Per Smithy @input structure constraints, every member of an input
        # structure is effectively optional regardless of @required; only
        # non-input structures make a @required, non-@default member mandatory.
        input_nullable = self._is_input(schema)
        field_names = self._field_names(schema)
        fields: list[Any] = []
        for i, member in enumerate(schema.members_by_index):
            if self._is_event_stream_member(member):
                continue
            if is_error and field_names[i] == "message":
                if member.get_trait(SensitiveTrait) is not None:
                    fields.append(
                        (
                            "message",
                            str,
                            _field(default="", kw_only=False, repr=False),
                        )
                    )
                continue
            spec = self._field_spec(member, input_nullable)
            if spec is _MANDATORY:
                fields.append((field_names[i], _py_type(member)))
            else:
                fields.append((field_names[i], _py_type(member), spec))
        if error_trait is not None:
            fields.append(
                ("fault", str | None, _field(default=error_trait.fault.value))
            )
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
        if name in self._union_schemas:
            return
        module = self._models_module_name
        for member in schema.members_by_index:
            vname = self._union_variant_name(name, member.expect_member_name())
            variant = self._build_variant(vname, schema, member.expect_member_index())
            variant.__module__ = module
            self._classes[vname] = variant
        unknown = self._union_unknown_name(name)

        def reject_serialization(self: Any, serializer: ShapeSerializer) -> None:
            raise SerializationError("Unknown union variants may not be serialized.")

        @classmethod  # type: ignore[misc]
        def deserialize(cls: type, deserializer: ShapeDeserializer) -> Any:
            raise NotImplementedError

        unknown_cls = make_dataclass(
            unknown,
            [("tag", str)],
            namespace={
                "serialize": reject_serialization,
                "serialize_members": reject_serialization,
                "deserialize": deserialize,
            },
        )
        unknown_cls.__module__ = module
        self._classes[unknown] = unknown_cls
        self._union_schemas[name] = schema
        # A tagged union has no single runtime class; expose a marker so the name
        # resolves. Static code uses the .pyi union alias, not this object.
        marker = make_dataclass(name, [])
        marker.__module__ = module
        self._classes[name] = marker
        original = schema.id.name
        index = self._ensure_index()
        const = self._renames.get(name, index.get(name))
        if (
            original != name
            and original not in self._renames
            and const is not None
            and index.get(original) == const
        ):
            self._classes.setdefault(original, marker)
            self._union_schemas.setdefault(original, schema)
            for member in schema.members_by_index:
                member_name = member.expect_member_name()
                canonical_variant = self._union_variant_name(name, member_name)
                original_variant = self._union_variant_name(original, member_name)
                if (
                    original_variant not in self._renames
                    and index.get(original_variant, const) == const
                ):
                    self._classes.setdefault(
                        original_variant, self._classes[canonical_variant]
                    )
            original_unknown = self._union_unknown_name(original)
            if (
                original_unknown not in self._renames
                and index.get(original_unknown, const) == const
            ):
                self._classes.setdefault(original_unknown, unknown_cls)

    def _union_variant_name(self, container: str, member: str) -> str:
        capitalized = member[:1].upper() + member[1:]
        return self._union_synthetic_name(container, capitalized)

    def _union_unknown_name(self, container: str) -> str:
        return self._union_synthetic_name(container, "Unknown")

    def _union_synthetic_name(self, container: str, suffix: str) -> str:
        base = container + suffix
        disambiguated = container + "_" + suffix
        index = self._ensure_index()
        const = self._renames.get(container, index.get(container))
        if const is not None:
            for candidate in (base, disambiguated):
                if self._renames.get(candidate, index.get(candidate)) == const:
                    return candidate
            owner = self._renames.get(base, index.get(base))
            if owner is not None and owner != const:
                return disambiguated
        return disambiguated if base in self._shape_names else base

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
                self._union_variant_name(name, member.expect_member_name())
            )
            result[0] = variant(value=reader(de, member))

        deserializer.read_struct(schema, consumer=consume)
        if result[0] is None:
            result[0] = self.build(self._union_unknown_name(name))(tag="unknown")
        return result[0]

    def _input_struct(
        self, schema: Schema, value: Mapping[Any, Any], redact: bool
    ) -> Any:
        members, required, cls = schema.get_extension(self._input_plan)
        kwargs: dict[str, Any] = {}
        unknown: list[Any] | None = None
        for key, item in value.items():
            member = members.get(key)
            if member is None:
                if unknown is None:
                    unknown = []
                unknown.append(key)
            elif item is not None:
                convert = member.get_extension(self._input_converter)
                if convert is None:
                    kwargs[key] = item
                else:
                    try:
                        kwargs[key] = convert(item, redact, False)
                    except _InputError as error:
                        error.path.append(f".{key}")
                        raise
                    except RecursionError:
                        raise _too_deep(f".{key}") from None
        if unknown is not None:
            raise _InputError(_unknown_members(unknown, members, redact))
        missing = [name for name in required if name not in kwargs]
        if missing:
            raise _InputError(_missing_members(missing))
        return cls(**kwargs)

    def _check_struct(self, schema: Schema, instance: Any, redact: bool) -> None:
        """Check a model the caller built, which is used exactly as it is.

        Its members must be models too: a dictionary inside a model is rejected
        rather than converted, because converting it would change the model.
        """
        members, required, _ = schema.get_extension(self._input_plan)
        for key, member in members.items():
            item = getattr(instance, key, None)
            if item is None:
                continue
            check = member.get_extension(self._input_converter)
            if check is not None:
                try:
                    check(item, redact, True)
                except _InputError as error:
                    error.path.append(f".{key}")
                    raise
                except RecursionError:
                    raise _too_deep(f".{key}") from None
        missing = [name for name in required if getattr(instance, name, None) is None]
        if missing:
            raise _InputError(_missing_members(missing))

    def _resolve_input_plan(
        self, schema: Schema
    ) -> tuple[dict[str, Schema], tuple[str, ...], type]:
        """A structure's members by generated name, those that must be set, and its
        model class."""
        field_names = self._field_names(schema)
        # An operation's own idempotency token may be left unset even when it is
        # required, because the pipeline generates it. One nested in its input is
        # not generated, so it must be set like any other required member.
        own_token = self._is_input(schema)
        members: dict[str, Schema] = {}
        required: list[str] = []
        for i, member in enumerate(schema.members_by_index):
            if self._is_event_stream_member(member):
                continue
            members[field_names[i]] = member
            if own_token and member.get_trait(IdempotencyTokenTrait) is not None:
                continue
            if (
                member.get_trait(RequiredTrait) is not None
                and member.get_trait(DefaultTrait) is None
            ):
                required.append(field_names[i])
        cls = self.build(self._target_name(schema))
        return members, tuple(required), cls

    def _resolve_input_converter(self, member: Schema) -> _InputConverter | None:
        """The conversion for a member's value, or None if it is used as given.

        Resolved once per member and cached on its schema, as the codecs are.
        """
        st = member.shape_type
        if st == ShapeType.STRUCTURE:
            convert = self._input_struct_converter(member.expect_member_target())
        elif st == ShapeType.UNION:
            convert = self._input_union_converter(member.expect_member_target())
        elif st == ShapeType.LIST:
            collection = member.expect_member_target()
            convert = self._input_list_converter(
                collection.members_by_index[0],
                collection.get_trait(SparseTrait) is not None,
            )
        elif st == ShapeType.MAP:
            collection = member.expect_member_target()
            convert = self._input_map_converter(
                collection.members["value"],
                sparse=collection.get_trait(SparseTrait) is not None,
                sensitive_keys=collection.members["key"].get_trait(SensitiveTrait)
                is not None,
            )
        else:
            return None
        # A member's traits include its target's. Everything under a sensitive
        # member is the caller's data, including the keys of dictionaries.
        if member.get_trait(SensitiveTrait) is None:
            return convert
        return lambda value, redact, in_model: convert(value, True, in_model)

    def _input_struct_converter(self, target: Schema) -> _InputConverter:
        name = self._target_name(target)
        cls = self.build(name)

        def convert(value: Any, redact: bool, in_model: bool) -> Any:
            if isinstance(value, cls):
                self._check_struct(target, value, redact)
                return value
            if in_model:
                raise _unexpected_in_model(name, value)
            if isinstance(value, Mapping):
                return self._input_struct(
                    target, cast("Mapping[Any, Any]", value), redact
                )
            raise _unexpected(f"{name} or a dict", value)

        return convert

    def _input_union_converter(self, target: Schema) -> _InputConverter:
        name = self._target_name(target)
        self.build(name)  # registers the variant classes
        variants: dict[str, tuple[type, Schema]] = {}
        keys: dict[type, str] = {}
        for member in target.members_by_index:
            member_name = member.expect_member_name()
            key = member_field_name(
                member_name,
                is_error=False,
                carries_response_metadata=False,
                is_enum=False,
            )
            variant = self.build(self._union_variant_name(name, member_name))
            variants[key] = (variant, member)
            keys[variant] = key
        unknown = self.build(self._union_unknown_name(name))

        def convert_value(key: str, item: Any, redact: bool, in_model: bool) -> Any:
            if item is None:
                raise _InputError(
                    f"the {key!r} variant of {name} is None; a variant must have a "
                    "value"
                )
            convert_item = variants[key][1].get_extension(self._input_converter)
            if convert_item is None:
                return item
            try:
                return convert_item(item, redact, in_model)
            except _InputError as error:
                error.path.append(f".{key}")
                raise
            except RecursionError:
                raise _too_deep(f".{key}") from None

        def convert(value: Any, redact: bool, in_model: bool) -> Any:
            key = keys.get(value.__class__)
            if key is not None:
                # A variant the caller built is checked and used as it is.
                convert_value(key, value.value, redact, True)
                return value
            if isinstance(value, unknown):
                raise _InputError(f"an unknown {name} variant cannot be sent")
            if in_model:
                raise _unexpected_in_model(f"a {name} variant", value)
            if not isinstance(value, Mapping):
                raise _unexpected(f"a {name} variant or a single-key dict", value)
            mapping = cast("Mapping[Any, Any]", value)
            # Exactly one key: one whose value is None is not left out, as it would
            # be in a structure, because it names a variant all the same.
            if len(mapping) != 1:
                if not mapping:
                    raise _InputError(
                        f"a {name} dict sets no variant; set exactly one of "
                        + ", ".join(repr(known) for known in variants)
                    )
                raise _InputError(
                    f"a {name} dict must have exactly one key, got {len(mapping)}: "
                    + ", ".join(
                        _describe_key(k, redact and k not in variants) for k in mapping
                    )
                )
            ((key, item),) = mapping.items()
            if key not in variants:
                raise _InputError(
                    f"unknown variant {_describe_key(key, redact)} for {name}; "
                    "set exactly one of " + ", ".join(repr(known) for known in variants)
                )
            return variants[key][0](value=convert_value(key, item, redact, False))

        return convert

    def _input_list_converter(self, element: Schema, sparse: bool) -> _InputConverter:
        def convert(value: Any, redact: bool, in_model: bool) -> Any:
            # A str is a Sequence of its characters, which is never what is meant.
            if isinstance(value, _NOT_A_LIST) or not isinstance(value, Sequence):
                raise _unexpected("a list", value)
            items = cast("Sequence[Any]", value)
            convert_item = element.get_extension(self._input_converter)
            # A list inside a model is checked where it is; any other is copied.
            out: list[Any] | None = None if in_model else []
            for index, item in enumerate(items):
                if item is None:
                    if not sparse:
                        error = _InputError("None is only allowed in a sparse list")
                        error.path.append(f"[{index}]")
                        raise error
                elif convert_item is not None:
                    try:
                        item = convert_item(item, redact, in_model)
                    except _InputError as error:
                        error.path.append(f"[{index}]")
                        raise
                    except RecursionError:
                        raise _too_deep(f"[{index}]") from None
                if out is not None:
                    out.append(item)
            return items if out is None else out

        return convert

    def _input_map_converter(
        self, value_member: Schema, *, sparse: bool, sensitive_keys: bool
    ) -> _InputConverter:
        def convert(value: Any, redact: bool, in_model: bool) -> Any:
            if not isinstance(value, Mapping):
                raise _unexpected("a dict", value)
            entries = cast("Mapping[Any, Any]", value)
            convert_item = value_member.get_extension(self._input_converter)
            # Map keys are the caller's data, so sensitive ones stay out of paths.
            names_keys = not (redact or sensitive_keys)
            out: dict[str, Any] | None = None if in_model else {}
            for key, item in entries.items():
                if not isinstance(key, str):
                    raise _InputError(f"map keys must be str, got {type(key).__name__}")
                if item is None:
                    if not sparse:
                        error = _InputError("None is only allowed in a sparse map")
                        error.path.append(f"[{key!r}]" if names_keys else "[<key>]")
                        raise error
                elif convert_item is not None:
                    try:
                        item = convert_item(item, redact, in_model)
                    except _InputError as error:
                        error.path.append(f"[{key!r}]" if names_keys else "[<key>]")
                        raise
                    except RecursionError:
                        raise _too_deep(
                            f"[{key!r}]" if names_keys else "[<key>]"
                        ) from None
                if out is not None:
                    out[key] = item
            return entries if out is None else out

        return convert

    def _is_streaming(self, member: Schema) -> bool:
        try:
            target = member.expect_member_target()
        except Exception:
            return False
        return target.get_trait(StreamingTrait) is not None

    def _is_event_stream_member(self, member: Schema) -> bool:
        try:
            target = member.expect_member_target()
        except Exception:
            return False
        return (
            target.shape_type is ShapeType.UNION
            and target.get_trait(StreamingTrait) is not None
        )

    def _resolve_member_codec(self, member: Schema) -> tuple[_Writer, _Reader]:
        st = member.shape_type
        if st == ShapeType.BLOB and self._is_streaming(member):
            return _scalar("write_data_stream", "read_data_stream")
        if st in (ShapeType.ENUM, ShapeType.INT_ENUM):
            # A StrEnum/IntEnum serializes as its bare str/int, but deserialize must
            # coerce the raw primitive back through the enum class (matching the eager
            # EnumGenerator's `EnumClass(read_string(...))`).
            is_int = st == ShapeType.INT_ENUM
            enum_cls = self.build(self._target_name(member.expect_member_target()))
            write_name = "write_integer" if is_int else "write_string"
            read_name = "read_integer" if is_int else "read_string"

            def we(s: ShapeSerializer, m: Schema, v: Any) -> None:
                getattr(s, write_name)(m, v)

            def re(d: ShapeDeserializer, m: Schema) -> Any:
                return enum_cls(getattr(d, read_name)(m))

            return we, re
        scalar = _SCALAR_CODECS.get(st)
        if scalar is not None:
            return scalar
        if st == ShapeType.STRUCTURE:
            target = self._target_name(member.expect_member_target())

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
            target = self._target_name(member.expect_member_target())
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

    def _target_name(self, schema: Schema) -> str:
        if generated := self._target_names.get(str(schema.id)):
            return generated
        # A renamed shape may share its ID name with another shape, which the
        # name-keyed index below would resolve it to. Its full ID tells them apart.
        for const, renamed in self._renamed_schemas.items():
            if hydrate(getattr(self._schemas, const)).id == schema.id:
                return renamed
        index = self._ensure_index()
        const = index.get(schema.id.name)
        return (
            self._renamed_schemas.get(const, schema.id.name)
            if const is not None
            else schema.id.name
        )

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


def _scalar(write_name: str, read_name: str) -> tuple[_Writer, _Reader]:
    def w(s: ShapeSerializer, m: Schema, v: Any) -> None:
        getattr(s, write_name)(m, v)

    def r(d: ShapeDeserializer, m: Schema) -> Any:
        return getattr(d, read_name)(m)

    return w, r


_SCALAR_CODECS: dict[ShapeType, tuple[_Writer, _Reader]] = {
    ShapeType.BOOLEAN: _scalar("write_boolean", "read_boolean"),
    ShapeType.STRING: _scalar("write_string", "read_string"),
    ShapeType.TIMESTAMP: _scalar("write_timestamp", "read_timestamp"),
    ShapeType.BLOB: _scalar("write_blob", "read_blob"),
    ShapeType.BYTE: _scalar("write_byte", "read_byte"),
    ShapeType.SHORT: _scalar("write_short", "read_short"),
    ShapeType.INTEGER: _scalar("write_integer", "read_integer"),
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


def _document(value: Any) -> Any:
    from .documents import Document

    return Document(value)


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


# Never reaches a caller: build_input reports it as a TypeError.
class _InputError(SmithyError):
    """A problem with a keyword input, and the path to it, innermost segment first."""

    def __init__(self, message: str) -> None:
        self.message = message
        self.path: list[str] = []
        self.too_deep = False


def _unexpected(expected: str, value: Any) -> _InputError:
    # Only the value's type is named; the value itself may be sensitive.
    return _InputError(f"expected {expected}, got {type(value).__name__}")


def _unexpected_in_model(expected: str, value: Any) -> _InputError:
    error = _unexpected(expected, value)
    if isinstance(value, Mapping):
        error.message += "; a dict inside a model is not converted"
    return error


def _too_deep(segment: str) -> _InputError:
    """The error for a value the interpreter's recursion limit stopped.

    A value that contains itself never ends, and neither does its path, so only
    the start of the path is reported. A value used in several places without
    containing itself is converted at each of them and never gets here.
    """
    error = _InputError(
        "nested too deeply to be converted; a dict, list, or model may contain itself"
    )
    error.too_deep = True
    if segment:
        error.path.append(segment)
    return error


def _describe_key(key: Any, redact: bool = False) -> str:
    # Keys are named because the caller wrote them, unless they are sensitive data.
    # Values are never included.
    if redact:
        return "<redacted>"
    return repr(key) if isinstance(key, str) else f"<{type(key).__name__} key>"


def _unknown_members(
    keys: list[Any], members: Mapping[str, Schema], redact: bool
) -> str:
    described: list[str] = []
    for key in keys:
        description = _describe_key(key, redact)
        if isinstance(key, str) and not redact:
            suggestion = to_snake_case(key)
            if suggestion != key and suggestion in members:
                description += f" (did you mean {suggestion!r}?)"
        described.append(description)
    return f"unknown member{'s' if len(keys) > 1 else ''} " + ", ".join(described)


def _missing_members(names: list[str]) -> str:
    return f"missing required member{'s' if len(names) > 1 else ''} " + ", ".join(
        repr(name) for name in names
    )


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
