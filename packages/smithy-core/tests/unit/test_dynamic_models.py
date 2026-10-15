#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
from enum import IntEnum, StrEnum
from types import ModuleType
from typing import cast

from smithy_core import _schema_compact
from smithy_core._dynamic_models import ModelRegistry
from smithy_core._schema_compact import StaticSchema
from smithy_core.exceptions import ModeledError
from smithy_core.shapes import ShapeType
from smithy_core.types import UnknownEnumMixin

NS = "ns.example"


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


def _error_struct(name: str, members: tuple[tuple[str, object], ...]) -> StaticSchema:
    return (
        ShapeType.STRUCTURE.value,
        NS,
        name,
        {_ERROR_TRAIT: "client"},
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
