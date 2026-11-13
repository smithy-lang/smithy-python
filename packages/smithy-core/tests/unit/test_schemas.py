# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from dataclasses import asdict, fields, replace
from types import ModuleType
from typing import Any

import pytest
from smithy_core._dynamic_models import ModelRegistry
from smithy_core._pipeline import (
    _expand_host_prefix,  # pyright: ignore[reportPrivateUsage]
)
from smithy_core._schema_compact import StaticSchema
from smithy_core.exceptions import ExpectationNotMetError, SmithyError
from smithy_core.schemas import APIOperation, Schema, SchemaExtension
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    DynamicTrait,
    InternalTrait,
    SensitiveTrait,
    Trait,
)
from smithy_core.types import TypedProperties

ID: ShapeID = ShapeID("ns.foo#bar")
STRING = Schema(id=ShapeID("smithy.api#String"), shape_type=ShapeType.STRING)


class _StubRegistry:
    def __init__(self, classes: dict[str, type]) -> None:
        self._classes = classes

    def build(self, name: str) -> type:
        return self._classes[name]


def test_traits_list():
    trait = InternalTrait()
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.traits == {InternalTrait.id: trait}


def test_get_trait_by_class():
    trait = InternalTrait()
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.get_trait(InternalTrait) is trait


def test_get_unknown_trait_by_class():
    trait = InternalTrait()
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.get_trait(SensitiveTrait) is None


def test_get_trait_by_id():
    trait = InternalTrait()
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.get_trait(InternalTrait.id) is trait


def test_get_unknown_trait_by_id():
    trait = InternalTrait()
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, traits=[trait])
    assert schema.get_trait(SensitiveTrait.id) is None


def test_schema_extension_is_built_once_and_cached() -> None:
    calls = 0

    def build_extension(schema: Schema) -> tuple[ShapeID, int]:
        nonlocal calls
        calls += 1
        return schema.id, calls

    extension = SchemaExtension(build_extension)
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE)

    first = schema.get_extension(extension)
    second = schema.get_extension(extension)

    assert first == (ID, 1)
    assert second is first
    assert calls == 1


def test_schema_extension_caches_none() -> None:
    calls = 0

    def build_extension(schema: Schema) -> None:
        nonlocal calls
        calls += 1

    extension = SchemaExtension(build_extension)
    schema = Schema(id=ID, shape_type=ShapeType.STRING)

    assert schema.get_extension(extension) is None
    assert schema.get_extension(extension) is None
    assert calls == 1


def test_schema_extensions_use_dense_indexed_slots() -> None:
    first = SchemaExtension(lambda schema: ("first", schema.id))
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE)

    assert schema.get_extension(first) == ("first", ID)

    second = SchemaExtension(lambda schema: ("second", schema.id))
    assert schema.get_extension(second) == ("second", ID)

    extensions: list[Any] = getattr(schema, "_extensions")
    assert isinstance(extensions, list)
    assert len(extensions) == second.id + 1
    assert extensions[first.id] == ("first", ID)
    assert extensions[second.id] == ("second", ID)


def test_schema_extension_cache_is_not_dataclass_state() -> None:
    extension = SchemaExtension(lambda schema: schema)
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE)

    assert schema.get_extension(extension) is schema
    assert "_extensions" not in {schema_field.name for schema_field in fields(schema)}
    assert "_extensions" not in asdict(schema)

    replaced = replace(schema)
    assert replaced.get_extension(extension) is replaced


def test_members_list():
    member_name = "baz"
    member = Schema(
        id=ID.with_member(member_name),
        shape_type=ShapeType.STRING,
        member_target=STRING,
        member_index=0,
    )
    schema = Schema(id=ID, shape_type=ShapeType.STRUCTURE, members=[member])
    assert schema.members == {"baz": member}


def test_members_by_index_is_dense_and_cached() -> None:
    first = Schema.member(id=ID.with_member("first"), target=STRING, index=0)
    second = Schema.member(id=ID.with_member("second"), target=STRING, index=1)
    schema = Schema(
        id=ID,
        shape_type=ShapeType.STRUCTURE,
        members={"second": second, "first": first},
    )

    members_by_index = schema.members_by_index

    assert members_by_index == (first, second)
    assert schema.members_by_index is members_by_index
    assert "_members_by_index" not in {
        schema_field.name for schema_field in fields(schema)
    }
    assert "_members_by_index" not in asdict(schema)


def test_members_by_index_rejects_sparse_indices() -> None:
    member = Schema.member(id=ID.with_member("member"), target=STRING, index=1)
    schema = Schema(
        id=ID,
        shape_type=ShapeType.STRUCTURE,
        members={"member": member},
    )

    with pytest.raises(SmithyError, match="dense and zero-based"):
        _ = schema.members_by_index


def test_expect_member_schema():
    member_schema = Schema(
        id=ID.with_member("baz"),
        shape_type=ShapeType.STRING,
        member_target=STRING,
        member_index=0,
    )
    assert member_schema.expect_member_name() == "baz"
    assert member_schema.member_name == "baz"

    assert member_schema.expect_member_target() == STRING
    assert member_schema.member_target == STRING

    assert member_schema.expect_member_index() == 0
    assert member_schema.member_index == 0


def test_member_expectations_raise_on_non_members():
    with pytest.raises(ExpectationNotMetError):
        STRING.expect_member_name()

    with pytest.raises(ExpectationNotMetError):
        STRING.expect_member_target()

    with pytest.raises(ExpectationNotMetError):
        STRING.expect_member_index()


def test_collection_constructor():
    trait_value = DynamicTrait(id=ShapeID("smithy.example#trait"), document_value="foo")
    member_name = "baz"
    member = Schema(
        id=ID.with_member(member_name),
        shape_type=ShapeType.STRING,
        traits=[trait_value],
        member_target=STRING,
        member_index=0,
    )
    schema = Schema.collection(
        id=ID,
        members={member_name: {"target": STRING, "traits": [trait_value]}},
    )
    assert schema.members == {member_name: member}


def test_member_constructor():
    target = Schema.collection(
        id=ShapeID("smithy.example#target"),
        traits=[
            SensitiveTrait(),
            DynamicTrait(id=ShapeID("smithy.example#foo"), document_value="bar"),
        ],
        members={"spam": {"target": STRING}},
    )

    member_id = ShapeID("smithy.example#Spam$eggs")
    expected = replace(
        target,
        id=member_id,
        member_target=target,
        member_index=1,
        traits=[
            SensitiveTrait(),
            DynamicTrait(id=ShapeID("smithy.example#foo"), document_value="baz"),
        ],
    )

    actual = Schema.member(
        id=member_id,
        target=target,
        index=1,
        member_traits=[
            DynamicTrait(id=ShapeID("smithy.example#foo"), document_value="baz")
        ],
    )

    assert actual == expected


def test_member_constructor_asserts_id():
    with pytest.raises(ExpectationNotMetError):
        Schema.member(id=ShapeID("smithy.example#foo"), target=STRING, index=0)


def test_member_constructor_asserts_target_is_not_member():
    target = Schema.member(
        id=ShapeID("smithy.example#Spam$eggs"), target=STRING, index=0
    )
    with pytest.raises(ExpectationNotMetError):
        Schema.member(id=ShapeID("smithy.example#Foo$bar"), target=target, index=0)


@pytest.mark.parametrize(
    "item, contains",
    [
        (SensitiveTrait, True),
        (SensitiveTrait.id, True),
        (InternalTrait, False),
        (InternalTrait.id, False),
        ("baz", True),
        (ID.with_member("baz"), True),
        (ID, False),
    ],
)
def test_contains(item: Any, contains: bool):
    schema = Schema.collection(
        id=ID,
        members={"baz": {"target": STRING}},
        traits=[SensitiveTrait()],
    )

    assert (item in schema) == contains


def test_operation_idempotency_token_member():
    input_schema = Schema.collection(
        id=ShapeID("com.example#OperationInput"),
        members={
            "other": {"target": STRING},
            "token": {
                "target": STRING,
                "traits": [Trait.new(id=ShapeID("smithy.api#idempotencyToken"))],
            },
        },
    )
    operation = APIOperation[Any, Any](
        static_schema=(
            ShapeType.OPERATION.value,
            "com.example",
            "Operation",
            0,
            input_schema,
            input_schema,
            (),
        ),
        model_registry=_StubRegistry({"OperationInput": object}),
        effective_auth_schemes=[],
    )
    assert operation.idempotency_token_member is input_schema.members["token"]


def _token_operation(
    members: tuple[str, ...], token: str, *, is_input: bool
) -> APIOperation[Any, Any]:
    """An operation whose input model is built by a real registry, as generated."""
    input_schema: StaticSchema = (
        ShapeType.STRUCTURE.value,
        "com.example",
        "OperationInput",
        {"smithy.api#input": None} if is_input else 0,
        members,
        tuple(
            (
                ShapeType.STRING.value,
                {"smithy.api#idempotencyToken": None} if name == token else 0,
            )
            for name in members
        ),
    )
    schemas = ModuleType("com.example._private.schemas")
    schemas.__dict__["OPERATION_INPUT"] = input_schema
    return APIOperation[Any, Any](
        static_schema=(
            ShapeType.OPERATION.value,
            "com.example",
            "Operation",
            0,
            input_schema,
            input_schema,
            (),
        ),
        model_registry=ModelRegistry(schemas),
        effective_auth_schemes=[],
    )


@pytest.mark.parametrize(
    ("members", "token", "is_input", "expected"),
    [
        pytest.param(
            ("clientToken",), "clientToken", True, "client_token", id="unreserved"
        ),
        pytest.param(("self",), "self", True, "self_", id="self"),
        pytest.param(("plugins",), "plugins", True, "plugins_", id="plugins"),
        pytest.param(("_models",), "_models", True, "_models_", id="models"),
        # Only a structure with the input trait has its members escaped.
        pytest.param(("plugins",), "plugins", False, "plugins", id="not-an-input"),
        pytest.param(
            ("_models",), "_models", False, "_models", id="models-not-an-input"
        ),
        # Escaped past a sibling that already has the underscore-suffixed name.
        pytest.param(
            ("self", "self_"), "self", True, "self__", id="self-beside-sibling"
        ),
        pytest.param(
            ("plugins_", "plugins"),
            "plugins",
            True,
            "plugins__",
            id="plugins-after-sibling",
        ),
        pytest.param(
            ("self", "self_", "self__"),
            "self",
            True,
            "self___",
            id="self-beside-siblings",
        ),
        pytest.param(
            ("_models", "_models_"),
            "_models",
            True,
            "_models__",
            id="models-beside-sibling",
        ),
        # The sibling that already has the suffixed name keeps it.
        pytest.param(
            ("plugins", "plugins_"),
            "plugins_",
            True,
            "plugins_",
            id="token-is-the-sibling",
        ),
    ],
)
def test_operation_idempotency_token_field_is_the_generated_input_field(
    members: tuple[str, ...], token: str, is_input: bool, expected: str
) -> None:
    operation = _token_operation(members, token, is_input=is_input)
    member = operation.idempotency_token_member
    assert member is not None

    # The input model's fields are in member order, so this is the field the
    # generated client actually gives the token member.
    generated = [model_field.name for model_field in fields(operation.input)]
    assert generated[member.expect_member_index()] == expected

    # The pipeline fills the token on this name, and skips the fill with a warning
    # when the input model has no such field.
    field_name = operation._idempotency_token_field  # pyright: ignore[reportPrivateUsage]
    assert field_name == expected


@pytest.mark.parametrize(
    ("members", "label", "is_input", "field_names"),
    [
        pytest.param(("self",), "self", True, ("self_",), id="self"),
        pytest.param(("plugins",), "plugins", True, ("plugins_",), id="plugins"),
        # Escaped past a sibling that already has the underscore-suffixed name.
        pytest.param(
            ("plugins_", "plugins"),
            "plugins",
            True,
            ("plugins_", "plugins__"),
            id="plugins-beside-sibling",
        ),
        # Only a structure with the input trait has its members escaped.
        pytest.param(("plugins",), "plugins", False, ("plugins",), id="not-an-input"),
        # The sibling that already has the suffixed name keeps it.
        pytest.param(
            ("plugins", "plugins_"),
            "plugins_",
            True,
            ("plugins__", "plugins_"),
            id="label-is-the-sibling",
        ),
    ],
)
def test_host_prefix_reads_generated_input_field(
    members: tuple[str, ...],
    label: str,
    is_input: bool,
    field_names: tuple[str, ...],
) -> None:
    input_schema: StaticSchema = (
        ShapeType.STRUCTURE.value,
        "com.example",
        "OperationInput",
        {"smithy.api#input": None} if is_input else 0,
        members,
        tuple(
            (
                ShapeType.STRING.value,
                {"smithy.api#hostLabel": None, "smithy.api#required": None}
                if name == label
                else 0,
            )
            for name in members
        ),
    )
    schemas = ModuleType("com.example._private.schemas")
    schemas.__dict__["OPERATION_INPUT"] = input_schema
    operation = APIOperation[Any, Any](
        static_schema=(
            ShapeType.OPERATION.value,
            "com.example",
            "Operation",
            {"smithy.api#endpoint": {"hostPrefix": "{" + label + "}."}},
            input_schema,
            input_schema,
            (),
        ),
        model_registry=ModelRegistry(schemas),
        effective_auth_schemes=[],
    )

    # The input model's fields are in member order, as the generated client has them.
    assert tuple(model_field.name for model_field in fields(operation.input)) == (
        field_names
    )

    # Every member is set, each to a different valid host label, so reading any
    # field but the label's own gives a different host.
    input = operation.input(
        **{
            field_name: "data" if member == label else f"sibling{index}"
            for index, (member, field_name) in enumerate(
                zip(members, field_names, strict=True)
            )
        }
    )
    assert _expand_host_prefix(input, operation, TypedProperties()) == "data."


def test_operation_builds_types_by_shape_id_name_by_default() -> None:
    io: StaticSchema = (ShapeType.STRUCTURE.value, "com.example", "OperationIO", 0)
    operation = APIOperation[Any, Any](
        static_schema=(ShapeType.OPERATION.value, "com.example", "Op", 0, io, io, ()),
        model_registry=_StubRegistry({"OperationIO": int, "Failure": str}),
        error_ids=[ShapeID("com.example#Failure")],
    )
    assert operation.input is int
    assert operation.output is int
    assert operation.error_registry[ShapeID("com.example#Failure")] is str


def test_operation_builds_renamed_types_by_shape_id() -> None:
    inputs: StaticSchema = (ShapeType.STRUCTURE.value, "com.example", "Shared", 0)
    output: StaticSchema = (ShapeType.STRUCTURE.value, "other.example", "Shared", 0)
    error_id = ShapeID("com.example#Failure")
    operation = APIOperation[Any, Any](
        static_schema=(
            ShapeType.OPERATION.value,
            "com.example",
            "Op",
            0,
            inputs,
            output,
            (),
        ),
        model_registry=_StubRegistry(
            {"Shared": int, "OtherShared": float, "ServiceFailure": str}
        ),
        error_ids=[error_id],
        type_names={
            ShapeID("other.example#Shared"): "OtherShared",
            error_id: "ServiceFailure",
        },
    )
    assert operation.input is int
    assert operation.output is float
    assert operation.error_registry[error_id] is str
