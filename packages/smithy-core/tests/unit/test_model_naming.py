#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from smithy_core._model_naming import union_unknown_name, variant_class_name


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
