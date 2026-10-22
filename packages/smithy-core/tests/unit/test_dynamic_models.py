#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
from enum import IntEnum, StrEnum
from types import ModuleType
from typing import Any, Protocol, cast

import pytest
from smithy_core import _schema_compact
from smithy_core._dynamic_models import ModelRegistry
from smithy_core._schema_compact import StaticSchema
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import ModeledError, SerializationError
from smithy_core.schemas import Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeType
from smithy_core.types import UnknownEnumMixin

NS = "ns.example"


class _UnknownVariant(Protocol):
    def serialize(self, serializer: ShapeSerializer) -> None: ...

    def serialize_members(self, serializer: ShapeSerializer) -> None: ...


class _UnknownVariantClass(Protocol):
    def __call__(self, *, tag: str) -> _UnknownVariant: ...

    def deserialize(self, deserializer: ShapeDeserializer) -> _UnknownVariant: ...


class _ModeledErrorClass(Protocol):
    def __call__(self) -> ModeledError: ...

    def deserialize(self, deserializer: ShapeDeserializer) -> ModeledError: ...


def _struct(name: str, members: tuple[tuple[str, object], ...]) -> StaticSchema:
    return (
        ShapeType.STRUCTURE.value,
        NS,
        name,
        0,
        tuple(m[0] for m in members),
        tuple((m[1], 0) for m in members),
    )


_ERROR_TRAIT = "smithy.api#error"


def _error_struct(
    name: str,
    members: tuple[tuple[str, object], ...],
    *,
    fault: str = "client",
) -> StaticSchema:
    return (
        ShapeType.STRUCTURE.value,
        NS,
        name,
        {_ERROR_TRAIT: fault},
        tuple(m[0] for m in members),
        tuple((m[1], 0) for m in members),
    )


def _union(name: str, members: tuple[tuple[str, object], ...]) -> StaticSchema:
    return (
        ShapeType.UNION.value,
        NS,
        name,
        0,
        tuple(m[0] for m in members),
        tuple((m[1], 0) for m in members),
    )


_ENUM_VALUE = "smithy.api#enumValue"


def _enum(
    name: str,
    members: tuple[tuple[str, object | None], ...],
    *,
    int_enum: bool = False,
) -> StaticSchema:
    # Enum members target UNIT (-1); a present enumValue is a valued member-trait dict.
    type_int = (ShapeType.INT_ENUM if int_enum else ShapeType.ENUM).value
    return (
        type_int,
        NS,
        name,
        0,
        tuple(m[0] for m in members),
        tuple((-1, {_ENUM_VALUE: m[1]} if m[1] is not None else 0) for m in members),
    )


def _module(**consts: StaticSchema) -> ModuleType:
    mod = ModuleType("ns.example._private.schemas")
    for const, tup in consts.items():
        setattr(mod, const, tup)
    return mod


def _fields(cls: type) -> list[str]:
    fields: dict[str, object] = getattr(cls, "__dataclass_fields__")
    return list(fields)


def _tracking_module(**consts: StaticSchema) -> tuple[ModuleType, list[str]]:
    """A schemas module that records every attribute read, to detect hydration."""
    touched: list[str] = []

    class _Tracking(ModuleType):
        def __getattribute__(self, name: str) -> object:
            if name.replace("_", "").isupper() and name[:1].isalpha():
                touched.append(name)
            return super().__getattribute__(name)

    mod = _Tracking("ns.example._private.schemas")
    for const, tup in consts.items():
        setattr(mod, const, tup)
    return mod, touched


def test_supplied_index_resolves_without_scanning_module() -> None:
    # Two structs, but the index names only one. With a supplied index the registry
    # must resolve it without reading the other schema constant at all.
    mod, touched = _tracking_module(
        FOO=_struct("Foo", (("a", ShapeType.STRING.value),)),
        BAR=_struct("Bar", (("b", ShapeType.STRING.value),)),
    )
    registry = ModelRegistry(mod, index={"Foo": "FOO"}, shape_names={"Foo", "Bar"})
    foo = registry.build("Foo")
    assert foo.__name__ == "Foo"
    assert touched == ["FOO"]  # BAR never read


def test_supplied_index_matches_scanning_fallback() -> None:
    consts = {
        "FOO": _struct("Foo", (("a", ShapeType.STRING.value),)),
        "BAR": _struct("Bar", (("b", ShapeType.INTEGER.value),)),
    }
    scanned = ModelRegistry(_module(**consts)).build("Foo")
    supplied = ModelRegistry(
        _module(**consts),
        index={"Foo": "FOO", "Bar": "BAR"},
        shape_names={"Foo", "Bar"},
    ).build("Foo")
    assert _fields(scanned) == _fields(supplied)


def test_supplied_index_preserves_distinct_same_named_structures() -> None:
    first = (
        ShapeType.STRUCTURE.value,
        "a.example",
        "Thing",
        0,
        ("first",),
        ((ShapeType.STRING.value, 0),),
    )
    second = (
        ShapeType.STRUCTURE.value,
        "b.example",
        "Thing",
        0,
        ("second",),
        ((ShapeType.STRING.value, 0),),
    )
    registry = ModelRegistry(
        _module(FIRST=first, SECOND=second),
        index={"FirstThing": "FIRST", "SecondThing": "SECOND"},
    )

    first_cls = registry.build("FirstThing")
    second_cls = registry.build("SecondThing")
    assert first_cls is not second_cls
    assert first_cls.__name__ == "FirstThing"
    assert second_cls.__name__ == "SecondThing"
    assert _fields(first_cls) == ["first"]
    assert _fields(second_cls) == ["second"]


def test_registry_copies_supplied_name_maps() -> None:
    renames = {"Alias": "FOO"}
    index = {"Alias": "FOO"}
    registry = ModelRegistry(
        _module(FOO=_struct("Foo", ())),
        renames=renames,
        index=index,
    )
    renames.clear()
    index.clear()

    assert registry.build("Alias").__name__ == "Alias"


def test_alias_and_canonical_struct_lookups_share_class_identity() -> None:
    registry = ModelRegistry(
        _module(FOO=_struct("Foo", ())),
        renames={"Alias": "FOO"},
    )

    alias = registry.build("Alias")
    assert registry.build("Foo") is alias
    assert registry.build("Alias") is alias


def test_alias_and_canonical_union_lookups_share_class_identity() -> None:
    registry = ModelRegistry(
        _module(FOO=_union("Foo", (("value", ShapeType.STRING.value),))),
        renames={"Alias": "FOO"},
    )

    alias = registry.build("Alias")
    variant = registry.build("AliasValue")
    unknown = registry.build("AliasUnknown")
    assert registry.build("Foo") is alias
    assert registry.build("Alias") is alias
    assert registry.build("AliasValue") is variant
    assert registry.build("FooValue") is variant
    assert registry.build("FooUnknown") is unknown

    class _De:
        def read_struct(self, schema: Schema, consumer: Any) -> None:
            consumer(schema.members_by_index[0], self)

        def read_string(self, schema: Schema) -> str:
            return "value"

    alias_deserializer = registry.build("_AliasDeserializer")()
    original_deserializer = registry.build("_FooDeserializer")()
    alias_value = alias_deserializer.deserialize(cast(ShapeDeserializer, _De()))
    original_value = original_deserializer.deserialize(cast(ShapeDeserializer, _De()))
    assert type(alias_value) is variant
    assert type(original_value) is variant
    assert alias_value.value == original_value.value == "value"


def test_renamed_union_does_not_replace_same_named_shape() -> None:
    renamed = (
        ShapeType.UNION.value,
        "a.example",
        "Thing",
        0,
        ("value",),
        ((ShapeType.STRING.value, 0),),
    )
    other = (
        ShapeType.STRUCTURE.value,
        "b.example",
        "Thing",
        0,
        ("other",),
        ((ShapeType.STRING.value, 0),),
    )
    registry = ModelRegistry(
        _module(A_OTHER=other, Z_RENAMED=renamed),
        renames={"FirstThing": "Z_RENAMED"},
    )

    first = registry.build("FirstThing")
    thing = registry.build("Thing")
    assert first is not thing
    assert _fields(thing) == ["other"]


def test_supplied_union_names_override_original_shape_names() -> None:
    union = (
        ShapeType.UNION.value,
        "a.example",
        "Foo",
        0,
        ("item",),
        ((ShapeType.STRING.value, 0),),
    )
    item = (
        ShapeType.STRUCTURE.value,
        "b.example",
        "OldItem",
        0,
        ("item",),
        ((ShapeType.STRING.value, 0),),
    )
    unknown = (
        ShapeType.STRUCTURE.value,
        "b.example",
        "OldUnknown",
        0,
        ("unknown",),
        ((ShapeType.STRING.value, 0),),
    )
    registry = ModelRegistry(
        _module(FOO=union, ITEM=item, UNKNOWN=unknown),
        renames={
            "Choice": "FOO",
            "ChoiceItem": "ITEM",
            "ChoiceUnknown": "UNKNOWN",
        },
        index={
            "Foo": "FOO",
            "Choice_Item": "FOO",
            "Choice_Unknown": "FOO",
            "OldItem": "ITEM",
            "OldUnknown": "UNKNOWN",
        },
        shape_names={"Foo", "OldItem", "OldUnknown"},
    )

    item_cls = registry.build("ChoiceItem")
    unknown_cls = registry.build("ChoiceUnknown")
    registry.build("Choice")
    assert registry.build("Choice_Item") is not item_cls
    assert registry.build("Choice_Unknown") is not unknown_cls
    assert registry.build("ChoiceItem") is item_cls
    assert registry.build("ChoiceUnknown") is unknown_cls


def test_renamed_union_aliases_do_not_replace_renamed_models() -> None:
    registry = ModelRegistry(
        _module(
            FOO=_union("Foo", (("value", ShapeType.STRING.value),)),
            VALUE=_struct("ValueModel", (("value", ShapeType.STRING.value),)),
            UNKNOWN=_struct("UnknownModel", (("value", ShapeType.STRING.value),)),
        ),
        renames={
            "Alias": "FOO",
            "FooValue": "VALUE",
            "FooUnknown": "UNKNOWN",
        },
    )

    registry.build("Alias")
    assert _fields(registry.build("FooValue")) == ["value"]
    assert _fields(registry.build("FooUnknown")) == ["value"]
    assert registry.build("FooValue") is not registry.build("AliasValue")
    assert registry.build("FooUnknown") is not registry.build("AliasUnknown")


def test_renamed_union_original_alias_does_not_replace_renamed_model() -> None:
    registry = ModelRegistry(
        _module(
            FOO=_union("Foo", (("value", ShapeType.STRING.value),)),
            MODEL=_struct("Model", (("value", ShapeType.STRING.value),)),
        ),
        renames={"Alias": "FOO", "Foo": "MODEL"},
    )

    registry.build("Alias")
    assert _fields(registry.build("Foo")) == ["value"]
    assert registry.build("Foo") is not registry.build("Alias")


def test_target_names_resolve_renames_by_full_shape_id() -> None:
    _schema_compact._cache.clear()
    first = (
        ShapeType.STRUCTURE.value,
        "a.example",
        "Thing",
        0,
    )
    second = (
        ShapeType.STRUCTURE.value,
        "b.example",
        "Thing",
        0,
    )
    container = _struct("Container", (("value", lambda: second),))
    registry = ModelRegistry(
        _module(FIRST=first, SECOND=second, CONTAINER=container),
        renames={"FirstThing": "FIRST", "SecondThing": "SECOND"},
        index={
            "FirstThing": "FIRST",
            "SecondThing": "SECOND",
            "Container": "CONTAINER",
        },
        target_names={
            "a.example#Thing": "FirstThing",
            "b.example#Thing": "SecondThing",
            f"{NS}#Container": "Container",
        },
        shape_names={"FirstThing", "SecondThing", "Container"},
    )
    schema = _schema_compact.hydrate(container)
    member = schema.members_by_index[0]
    _, reader = member.get_extension(registry._codec)

    class _De:
        def read_struct(self, schema: object, consumer: object) -> None:
            pass

    result = reader(cast(ShapeDeserializer, _De()), member)
    assert type(result).__name__ == "SecondThing"


def test_supplied_index_disambiguated_union_variant() -> None:
    # Union FooWarning.message collides with struct FooWarningMessage; codegen emits
    # the "_"-disambiguated variant name in the index. The real struct must still
    # build with its modeled field, not the union variant's "value".
    _schema_compact._cache.clear()
    union = _union("FooWarning", (("message", ShapeType.STRING.value),))
    struct = _struct("FooWarningMessage", (("text", ShapeType.STRING.value),))
    mod = _module(FOOWARNING=union, FOOWARNINGMESSAGE=struct)
    registry = ModelRegistry(
        mod,
        index={
            "FooWarning": "FOOWARNING",
            "FooWarning_Message": "FOOWARNING",
            "FooWarningUnknown": "FOOWARNING",
            "FooWarningMessage": "FOOWARNINGMESSAGE",
        },
        shape_names={"FooWarning", "FooWarningMessage"},
    )
    struct_cls = registry.build("FooWarningMessage")
    assert _fields(struct_cls) == ["text"]
    variant_cls = registry.build("FooWarning_Message")
    assert _fields(variant_cls) == ["value"]


def test_str_enum_uses_wire_value_not_member_name() -> None:
    # The member name (EN_US) differs from the wire value (en-US); the built enum must
    # carry the wire value so serialization sends en-US, not EN_US.
    _schema_compact._cache.clear()
    mod = _module(
        LANG=_enum("Lang", (("EN_US", "en-US"), ("MULTI", "multi"))),
    )
    registry = ModelRegistry(mod, index={"Lang": "LANG"}, shape_names={"Lang"})
    cls = cast("type[StrEnum]", registry.build("Lang"))
    assert cls["EN_US"].value == "en-US"
    assert cls["EN_US"] == "en-US"
    assert list(cls.__members__) == ["EN_US", "MULTI"]
    unknown = cast(UnknownEnumMixin, cls("xx-YY"))
    assert unknown.is_unknown  # UnknownEnumMixin: unknown value, no raise


def test_int_enum_builds_with_values() -> None:
    _schema_compact._cache.clear()
    mod = _module(CODE=_enum("Code", (("A", 1), ("B", 2)), int_enum=True))
    registry = ModelRegistry(mod, index={"Code": "CODE"}, shape_names={"Code"})
    cls = cast("type[IntEnum]", registry.build("Code"))
    assert cls["A"].value == 1
    assert int(cls["A"]) == 1


def test_enum_defaults_value_to_member_name_when_trait_absent() -> None:
    _schema_compact._cache.clear()
    mod = _module(STATUS=_enum("Status", (("ACTIVE", None), ("DELETED", None))))
    registry = ModelRegistry(mod, index={"Status": "STATUS"}, shape_names={"Status"})
    cls = cast("type[StrEnum]", registry.build("Status"))
    assert cls["ACTIVE"].value == "ACTIVE"


def test_modeled_error_extends_injected_service_error() -> None:
    import sys

    _schema_compact._cache.clear()

    class ServiceError(ModeledError):
        pass

    models = ModuleType("ns.example.models")
    models.ServiceError = ServiceError  # type: ignore[attr-defined]
    sys.modules["ns.example.models"] = models
    try:
        mod = _module(BOOM=_error_struct("Boom", (("reason", ShapeType.STRING.value),)))
        registry = ModelRegistry(
            mod,
            index={"Boom": "BOOM"},
            shape_names={"Boom"},
            service_error="ServiceError",
        )
        cls = registry.build("Boom")
        assert issubclass(cls, ServiceError)
        assert issubclass(cls, ModeledError)
    finally:
        del sys.modules["ns.example.models"]


def test_modeled_error_falls_back_to_modeled_error_without_service_error() -> None:
    _schema_compact._cache.clear()
    mod = _module(BOOM=_error_struct("Boom", (("reason", ShapeType.STRING.value),)))
    registry = ModelRegistry(mod, index={"Boom": "BOOM"}, shape_names={"Boom"})
    cls = registry.build("Boom")
    assert issubclass(cls, ModeledError)
    assert cls.__mro__[1] is ModeledError


def test_modeled_error_uses_modeled_fault() -> None:
    _schema_compact._cache.clear()
    mod = _module(BOOM=_error_struct("Boom", (), fault="server"))
    registry = ModelRegistry(mod, index={"Boom": "BOOM"}, shape_names={"Boom"})
    cls = cast(_ModeledErrorClass, registry.build("Boom"))

    class _De:
        def read_struct(self, schema: Schema, consumer: Any) -> None:
            pass

    assert cls().fault == "server"
    assert cls.deserialize(cast(ShapeDeserializer, _De())).fault == "server"


def test_enum_member_deserialize_coerces_to_enum_class() -> None:
    # A member whose target is an enum must deserialize to the enum class, not the
    # raw wire string (the eager generator wrapped it as EnumClass(read_string(...))).
    _schema_compact._cache.clear()
    lang = _enum("Lang", (("EN_US", "en-US"), ("MULTI", "multi")))
    req = (
        ShapeType.STRUCTURE.value,
        NS,
        "Req",
        0,
        ("lang",),
        ((lambda: lang, 0),),
    )
    mod = _module(LANG=lang, REQ=req)
    registry = ModelRegistry(
        mod,
        index={"Lang": "LANG", "Req": "REQ"},
        shape_names={"Lang", "Req"},
    )
    req_schema = _schema_compact.hydrate(req)
    member = req_schema.members_by_index[0]
    _, reader = member.get_extension(registry._codec)

    class _De:
        def read_string(self, schema: object) -> str:
            return "en-US"

    result = reader(cast(ShapeDeserializer, _De()), member)
    lang = cast("type[StrEnum]", registry.build("Lang"))
    assert result is lang["EN_US"]


def test_union_classes_report_models_module() -> None:
    # The union parent, each variant, and the Unknown class must carry the client
    # models module, not smithy_core._dynamic_models.
    _schema_compact._cache.clear()
    mod = _module(
        FOO=_union("Foo", (("a", ShapeType.STRING.value),)),
    )
    registry = ModelRegistry(mod, index={"Foo": "FOO"}, shape_names={"Foo"})
    registry.build("Foo")
    for name in ("Foo", "FooA", "FooUnknown"):
        assert registry.build(name).__module__ == "ns.example.models"


def test_unknown_union_variant_rejects_serde() -> None:
    _schema_compact._cache.clear()
    mod = _module(FOO=_union("Foo", (("a", ShapeType.STRING.value),)))
    registry = ModelRegistry(mod, index={"Foo": "FOO"}, shape_names={"Foo"})
    registry.build("Foo")
    unknown = cast(_UnknownVariantClass, registry.build("FooUnknown"))
    value = unknown(tag="future")

    with pytest.raises(SerializationError):
        value.serialize(cast(ShapeSerializer, object()))
    with pytest.raises(SerializationError):
        value.serialize_members(cast(ShapeSerializer, object()))
    with pytest.raises(NotImplementedError):
        unknown.deserialize(cast(ShapeDeserializer, object()))


def test_concurrent_build_returns_one_class() -> None:
    import threading

    _schema_compact._cache.clear()
    mod = _module(FOO=_struct("Foo", (("a", ShapeType.STRING.value),)))
    registry = ModelRegistry(mod, index={"Foo": "FOO"}, shape_names={"Foo"})
    start = threading.Barrier(8)
    results: list[type] = []
    lock = threading.Lock()

    def worker() -> None:
        start.wait()
        built = registry.build("Foo")
        with lock:
            results.append(built)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len({id(r) for r in results}) == 1


def _operation(name: str, input_ref: object, output_ref: object) -> StaticSchema:
    # Operation tuple: shape header (0-3) then input (4), output (5), errors (6).
    return (
        ShapeType.OPERATION.value,
        NS,
        name,
        0,
        input_ref,
        output_ref,
        (),
    )


def test_import_and_one_operation_does_not_build_every_shape() -> None:
    # Importing the operation table (constructing APIOperation objects) must build no
    # model classes and hydrate no schemas; using one operation must build only that
    # operation's input, leaving sibling operations' shapes and unrelated shapes alone.
    import smithy_core._dynamic_models as dm
    from smithy_core.schemas import APIOperation

    _schema_compact._cache.clear()
    a_in = _struct("AInput", (("a", ShapeType.STRING.value),))
    a_out = _struct("AOutput", (("a", ShapeType.STRING.value),))
    b_in = _struct("BInput", (("b", ShapeType.STRING.value),))
    b_out = _struct("BOutput", (("b", ShapeType.STRING.value),))
    unrelated = _struct("Unrelated", (("c", ShapeType.STRING.value),))
    mod = _module(
        AINPUT=a_in,
        AOUTPUT=a_out,
        BINPUT=b_in,
        BOUTPUT=b_out,
        UNRELATED=unrelated,
        OP_A=_operation("OpA", lambda: a_in, lambda: a_out),
        OP_B=_operation("OpB", lambda: b_in, lambda: b_out),
    )
    registry = ModelRegistry(
        mod,
        index={
            "AInput": "AINPUT",
            "AOutput": "AOUTPUT",
            "BInput": "BINPUT",
            "BOutput": "BOUTPUT",
            "Unrelated": "UNRELATED",
        },
        shape_names={"AInput", "AOutput", "BInput", "BOutput", "Unrelated"},
    )

    hydrations: list[object] = []
    original = dm.hydrate

    def _counting(tup: StaticSchema) -> object:
        hydrations.append(tup)
        return original(tup)

    dm.hydrate = _counting
    try:
        # Construct the operation table the way generated models.py does.
        op_a: APIOperation[Any, Any] = APIOperation(
            static_schema=mod.OP_A, model_registry=registry
        )
        APIOperation(static_schema=mod.OP_B, model_registry=registry)
        assert registry._classes == {}  # no class built by constructing the table
        assert hydrations == []  # no schema hydrated by constructing the table

        built: type = op_a.input  # using one operation
        assert built.__name__ == "AInput"
        # Only AInput was built; sibling and unrelated shapes stayed lazy.
        assert set(registry._classes) == {"AInput"}
    finally:
        dm.hydrate = original
