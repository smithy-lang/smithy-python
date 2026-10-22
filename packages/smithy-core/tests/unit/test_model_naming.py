#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core._model_naming import (
    member_field_name,
    to_snake_case,
    union_unknown_name,
    variant_class_name,
)


def test_snake_case_preserves_prefix_for_leading_digit() -> None:
    assert to_snake_case("_1") == "_1"
    assert to_snake_case("_2HTTPServer") == "_2_http_server"


def test_snake_case_preserves_existing_underscores() -> None:
    assert to_snake_case("_value") == "_value"
    assert to_snake_case("value_") == "value_"
    assert to_snake_case("some__value") == "some__value"


def test_enum_names_escape_before_uppercasing() -> None:
    assert (
        member_field_name(
            "CLASS",
            is_error=False,
            carries_response_metadata=False,
            is_enum=True,
        )
        == "CLASS_"
    )


def test_enum_sunder_names_are_escaped() -> None:
    assert (
        member_field_name(
            "_VALUE_",
            is_error=False,
            carries_response_metadata=False,
            is_enum=True,
        )
        == "_VALUE__"
    )


def test_enum_dunder_names_are_escaped() -> None:
    assert (
        member_field_name(
            "__VALUE__",
            is_error=False,
            carries_response_metadata=False,
            is_enum=True,
        )
        == "__VALUE___"
    )


def test_runtime_method_names_are_reserved() -> None:
    for name in (
        "serialize",
        "serializeMembers",
        "deserialize",
        "__init__",
        "__post_init__",
        "_smithy_default",
        "__repr__",
        "__annotations__",
    ):
        assert member_field_name(
            name,
            is_error=False,
            carries_response_metadata=False,
            is_enum=False,
        ).endswith("_")


def test_double_leading_underscore_names_avoid_name_mangling() -> None:
    assert (
        member_field_name(
            "__value",
            is_error=False,
            carries_response_metadata=False,
            is_enum=False,
        )
        == "__value___"
    )


def test_variant_class_name_default() -> None:
    assert variant_class_name("Foo", "bar") == "FooBar"


def test_variant_class_name_disambiguates_shape_collision() -> None:
    # Union "AgenticRetrieveWarning" member "message" would synthesize
    # "AgenticRetrieveWarningMessage", colliding with the real structure of that
    # name; PythonSymbolProvider.memberShape inserts a "_" separator.
    names = {"AgenticRetrieveWarningMessage"}
    assert (
        variant_class_name("AgenticRetrieveWarning", "message", names)
        == "AgenticRetrieveWarning_Message"
    )


def test_variant_class_name_no_collision_keeps_base() -> None:
    assert variant_class_name("Foo", "bar", {"Baz"}) == "FooBar"


def test_union_unknown_name_default() -> None:
    assert union_unknown_name("Foo") == "FooUnknown"


def test_union_unknown_name_disambiguates_shape_collision() -> None:
    assert union_unknown_name("Foo", {"FooUnknown"}) == "Foo_Unknown"
