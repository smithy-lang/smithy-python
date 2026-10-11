#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Cached schema metadata used by the CBOR codec."""

from dataclasses import dataclass

from smithy_core.schemas import Schema, SchemaExtension
from smithy_core.shapes import ShapeType


@dataclass(frozen=True, slots=True)
class CBORMemberLookup:
    """Matches raw UTF-8 CBOR field names to member schemas."""

    ordered_schemas: tuple[Schema, ...]
    ordered_name_bytes: tuple[bytes, ...]
    entries_by_name: dict[bytes, Schema]

    def lookup(
        self,
        data: bytes,
        start: int,
        end: int,
        expected_next: int,
    ) -> Schema | None:
        """Look up a member without decoding its field name to a string."""
        name_length = end - start
        if 0 <= expected_next < len(self.ordered_name_bytes):
            expected = self.ordered_name_bytes[expected_next]
            if len(expected) == name_length and data.startswith(expected, start, end):
                return self.ordered_schemas[expected_next]

        return self.entries_by_name.get(data[start:end])


@dataclass(frozen=True, slots=True)
class CBORSchemaMetadata:
    """Precomputed CBOR data stored on a schema."""

    member_name_bytes: bytes | None = None
    member_lookup: CBORMemberLookup | None = None
    field_name_table: tuple[bytes | None, ...] = ()
    member_count: int = 0
    struct_header_width: int = 1


def _encode_member_name(name: str) -> bytes:
    encoded = name.encode("utf-8")
    length = len(encoded)
    if length < 24:
        return bytes((0x60 | length,)) + encoded
    if length < 0x100:
        return b"\x78" + bytes((length,)) + encoded
    if length < 0x10000:
        return b"\x79" + length.to_bytes(2, "big") + encoded
    if length < 0x100000000:
        return b"\x7a" + length.to_bytes(4, "big") + encoded
    return b"\x7b" + length.to_bytes(8, "big") + encoded


def _head_width(arg: int) -> int:
    if arg < 24:
        return 1
    if arg < 0x100:
        return 2
    if arg < 0x10000:
        return 3
    if arg < 0x100000000:
        return 5
    return 9


def _build_cbor_schema_metadata(schema: Schema) -> CBORSchemaMetadata | None:
    if schema.member_target is not None:
        return CBORSchemaMetadata(
            member_name_bytes=_encode_member_name(schema.expect_member_name())
        )

    if schema.shape_type not in (ShapeType.STRUCTURE, ShapeType.UNION):
        return None

    members = tuple(
        sorted(schema.members.values(), key=lambda member: member.expect_member_index())
    )
    member_count = len(members)
    if not members:
        return CBORSchemaMetadata()

    max_index = max(member.expect_member_index() for member in members)
    field_name_table: list[bytes | None] = [None] * (max_index + 1)
    ordered_name_bytes: list[bytes] = []
    entries_by_name: dict[bytes, Schema] = {}

    for member in members:
        raw_name = member.expect_member_name().encode("utf-8")
        ordered_name_bytes.append(raw_name)
        entries_by_name[raw_name] = member
        field_name_table[member.expect_member_index()] = _encode_member_name(
            member.expect_member_name()
        )

    return CBORSchemaMetadata(
        member_lookup=CBORMemberLookup(
            ordered_schemas=members,
            ordered_name_bytes=tuple(ordered_name_bytes),
            entries_by_name=entries_by_name,
        ),
        field_name_table=tuple(field_name_table),
        member_count=member_count,
        struct_header_width=_head_width(member_count),
    )


CBOR_SCHEMA_EXTENSION = SchemaExtension(_build_cbor_schema_metadata)
"""Shared descriptor for lazily cached CBOR schema metadata."""
