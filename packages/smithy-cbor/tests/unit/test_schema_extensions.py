#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_cbor._private.schema_extensions import CBOR_SCHEMA_EXTENSION
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType

STRING = Schema(id=ShapeID("smithy.api#String"), shape_type=ShapeType.STRING)


def test_member_name_bytes_are_cached_with_utf8_length() -> None:
    member = Schema.member(
        id=ShapeID("smithy.example#Example$é"),
        target=STRING,
        index=0,
    )

    metadata = member.get_extension(CBOR_SCHEMA_EXTENSION)

    assert metadata is not None
    assert metadata.member_name_bytes == b"\x62\xc3\xa9"
    assert member.get_extension(CBOR_SCHEMA_EXTENSION) is metadata


def test_scalar_schema_has_no_cbor_metadata() -> None:
    assert STRING.get_extension(CBOR_SCHEMA_EXTENSION) is None


def test_struct_metadata_is_ordered_and_indexed_by_member_index() -> None:
    schema_id = ShapeID("smithy.example#Example")
    first = Schema.member(id=schema_id.with_member("first"), target=STRING, index=0)
    third = Schema.member(id=schema_id.with_member("third"), target=STRING, index=2)
    schema = Schema(
        id=schema_id,
        shape_type=ShapeType.STRUCTURE,
        members=[third, first],
    )

    metadata = schema.get_extension(CBOR_SCHEMA_EXTENSION)
    assert metadata is not None
    lookup = metadata.member_lookup

    assert lookup is not None
    assert lookup.ordered_schemas == (first, third)
    assert lookup.ordered_name_bytes == (b"first", b"third")
    assert metadata.field_name_table == (b"\x65first", None, b"\x65third")
    assert metadata.member_count == 2
    assert metadata.struct_header_width == 1


def test_member_lookup_supports_speculative_and_out_of_order_matches() -> None:
    schema = Schema.collection(
        id=ShapeID("smithy.example#Example"),
        members={
            "first": {"target": STRING},
            "second": {"target": STRING},
        },
    )
    metadata = schema.get_extension(CBOR_SCHEMA_EXTENSION)

    assert metadata is not None
    lookup = metadata.member_lookup
    assert lookup is not None
    assert lookup.lookup(b"first", 0, 5, 0) is schema.members["first"]
    assert lookup.lookup(b"second", 0, 6, 0) is schema.members["second"]
    assert lookup.lookup(b"unknown", 0, 7, 0) is None
