#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Hand-authored Smithy model for the protocol throughput benchmark.

This mirrors what smithy-python codegen emits for a client (see
``codegen/protocol-test/build/smithyprojections/protocol-test/rpcv2-cbor/
python-client-codegen/src/rpcv2cbor/{_private/schemas.py,models.py}``): a set of
``Schema`` declarations, ``SerializeableShape``/``DeserializeableShape`` dataclasses
with ``serialize``/``serialize_members``/``deserialize_kwargs``, and an ``APIOperation``
tying them together. It is written by hand because we do not want to invoke codegen in
the test tree; the shape below is shared verbatim by both the rpcv2Cbor and awsJson1_0
protocols so the comparison is apples-to-apples.

The modeled shape (per the benchmark spec): the operation input and output are each a
list of ``Record`` structs. Each ``Record`` has a timestamp, mixed string/int/float
scalars, a nested struct, a list, and a map.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Self

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.prelude import (
    DOUBLE,
    INTEGER,
    LONG,
    STRING,
    TIMESTAMP,
)
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType

_NS = "smithy.benchmark"


# --- Schema declarations (mirroring _private/schemas.py) -------------------------

NESTED = Schema.collection(
    id=ShapeID(f"{_NS}#Nested"),
    members={
        "label": {"target": STRING},
        "score": {"target": DOUBLE},
    },
)

TAG_LIST = Schema.collection(
    id=ShapeID(f"{_NS}#TagList"),
    shape_type=ShapeType.LIST,
    members={"member": {"target": STRING}},
)

ATTRIBUTE_MAP = Schema.collection(
    id=ShapeID(f"{_NS}#AttributeMap"),
    shape_type=ShapeType.MAP,
    members={"key": {"target": STRING}, "value": {"target": INTEGER}},
)

RECORD = Schema.collection(
    id=ShapeID(f"{_NS}#Record"),
    members={
        "id": {"target": STRING},
        "name": {"target": STRING},
        "count": {"target": INTEGER},
        "size": {"target": LONG},
        "ratio": {"target": DOUBLE},
        "weight": {"target": DOUBLE},
        "created_at": {"target": TIMESTAMP},
        "nested": {"target": NESTED},
        "tags": {"target": TAG_LIST},
        "attributes": {"target": ATTRIBUTE_MAP},
    },
)

RECORD_LIST = Schema.collection(
    id=ShapeID(f"{_NS}#RecordList"),
    shape_type=ShapeType.LIST,
    members={"member": {"target": RECORD}},
)

PUT_RECORDS_INPUT = Schema.collection(
    id=ShapeID(f"{_NS}#PutRecordsInput"),
    members={"records": {"target": RECORD_LIST}},
)

PUT_RECORDS_OUTPUT = Schema.collection(
    id=ShapeID(f"{_NS}#PutRecordsOutput"),
    members={"records": {"target": RECORD_LIST}},
)

PUT_RECORDS = Schema(
    id=ShapeID(f"{_NS}#PutRecords"),
    shape_type=ShapeType.OPERATION,
)

SERVICE = Schema(
    id=ShapeID(f"{_NS}#BenchmarkService"),
    shape_type=ShapeType.SERVICE,
)


# --- Shape dataclasses (mirroring models.py) -----------------------------------


@dataclass(kw_only=True)
class Nested:
    label: str
    score: float

    def serialize(self, serializer: ShapeSerializer) -> None:
        serializer.write_struct(NESTED, self)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_string(NESTED.members["label"], self.label)
        serializer.write_double(NESTED.members["score"], self.score)

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls(**cls.deserialize_kwargs(deserializer))

    @classmethod
    def deserialize_kwargs(cls, deserializer: ShapeDeserializer) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["label"] = de.read_string(NESTED.members["label"])
                case 1:
                    kwargs["score"] = de.read_double(NESTED.members["score"])
                case _:
                    pass

        deserializer.read_struct(NESTED, consumer=_consumer)
        return kwargs


def _serialize_tag_list(
    serializer: ShapeSerializer, schema: Schema, value: list[str]
) -> None:
    member_schema = schema.members["member"]
    with serializer.begin_list(schema, len(value)) as ls:
        for e in value:
            ls.write_string(member_schema, e)


def _deserialize_tag_list(deserializer: ShapeDeserializer, schema: Schema) -> list[str]:
    result: list[str] = []
    member_schema = schema.members["member"]

    def _read_value(d: ShapeDeserializer) -> None:
        if d.is_null():
            d.read_null()
        else:
            result.append(d.read_string(member_schema))

    deserializer.read_list(schema, _read_value)
    return result


def _serialize_attribute_map(
    serializer: ShapeSerializer, schema: Schema, value: dict[str, int]
) -> None:
    with serializer.begin_map(schema, len(value)) as m:
        value_schema = schema.members["value"]
        for k, v in value.items():
            m.entry(k, lambda vs, v=v: vs.write_integer(value_schema, v))


def _deserialize_attribute_map(
    deserializer: ShapeDeserializer, schema: Schema
) -> dict[str, int]:
    result: dict[str, int] = {}
    value_schema = schema.members["value"]

    def _read_value(k: str, d: ShapeDeserializer) -> None:
        if d.is_null():
            d.read_null()
        else:
            result[k] = d.read_integer(value_schema)

    deserializer.read_map(schema, _read_value)
    return result


@dataclass(kw_only=True)
class Record:
    id: str
    name: str
    count: int
    size: int
    ratio: float
    weight: float
    created_at: datetime
    nested: Nested
    tags: list[str]
    attributes: dict[str, int]

    def serialize(self, serializer: ShapeSerializer) -> None:
        serializer.write_struct(RECORD, self)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        serializer.write_string(RECORD.members["id"], self.id)
        serializer.write_string(RECORD.members["name"], self.name)
        serializer.write_integer(RECORD.members["count"], self.count)
        serializer.write_long(RECORD.members["size"], self.size)
        serializer.write_double(RECORD.members["ratio"], self.ratio)
        serializer.write_double(RECORD.members["weight"], self.weight)
        serializer.write_timestamp(RECORD.members["created_at"], self.created_at)
        serializer.write_struct(RECORD.members["nested"], self.nested)
        _serialize_tag_list(serializer, RECORD.members["tags"], self.tags)
        _serialize_attribute_map(
            serializer, RECORD.members["attributes"], self.attributes
        )

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls(**cls.deserialize_kwargs(deserializer))

    @classmethod
    def deserialize_kwargs(cls, deserializer: ShapeDeserializer) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["id"] = de.read_string(RECORD.members["id"])
                case 1:
                    kwargs["name"] = de.read_string(RECORD.members["name"])
                case 2:
                    kwargs["count"] = de.read_integer(RECORD.members["count"])
                case 3:
                    kwargs["size"] = de.read_long(RECORD.members["size"])
                case 4:
                    kwargs["ratio"] = de.read_double(RECORD.members["ratio"])
                case 5:
                    kwargs["weight"] = de.read_double(RECORD.members["weight"])
                case 6:
                    kwargs["created_at"] = de.read_timestamp(
                        RECORD.members["created_at"]
                    )
                case 7:
                    kwargs["nested"] = Nested.deserialize(de)
                case 8:
                    kwargs["tags"] = _deserialize_tag_list(de, RECORD.members["tags"])
                case 9:
                    kwargs["attributes"] = _deserialize_attribute_map(
                        de, RECORD.members["attributes"]
                    )
                case _:
                    pass

        deserializer.read_struct(RECORD, consumer=_consumer)
        return kwargs


def _serialize_record_list(
    serializer: ShapeSerializer, schema: Schema, value: list[Record]
) -> None:
    member_schema = schema.members["member"]
    with serializer.begin_list(schema, len(value)) as ls:
        for e in value:
            ls.write_struct(member_schema, e)


def _deserialize_record_list(
    deserializer: ShapeDeserializer, schema: Schema
) -> list[Record]:
    result: list[Record] = []

    def _read_value(d: ShapeDeserializer) -> None:
        if d.is_null():
            d.read_null()
        else:
            result.append(Record.deserialize(d))

    deserializer.read_list(schema, _read_value)
    return result


@dataclass(kw_only=True)
class PutRecordsInput:
    records: list[Record] = field(default_factory=list[Record])

    def serialize(self, serializer: ShapeSerializer) -> None:
        serializer.write_struct(PUT_RECORDS_INPUT, self)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        _serialize_record_list(
            serializer, PUT_RECORDS_INPUT.members["records"], self.records
        )

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls(**cls.deserialize_kwargs(deserializer))

    @classmethod
    def deserialize_kwargs(cls, deserializer: ShapeDeserializer) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["records"] = _deserialize_record_list(
                        de, PUT_RECORDS_INPUT.members["records"]
                    )
                case _:
                    pass

        deserializer.read_struct(PUT_RECORDS_INPUT, consumer=_consumer)
        if "records" not in kwargs:
            kwargs["records"] = []
        return kwargs


@dataclass(kw_only=True)
class PutRecordsOutput:
    records: list[Record] = field(default_factory=list[Record])

    def serialize(self, serializer: ShapeSerializer) -> None:
        serializer.write_struct(PUT_RECORDS_OUTPUT, self)

    def serialize_members(self, serializer: ShapeSerializer) -> None:
        _serialize_record_list(
            serializer, PUT_RECORDS_OUTPUT.members["records"], self.records
        )

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls(**cls.deserialize_kwargs(deserializer))

    @classmethod
    def deserialize_kwargs(cls, deserializer: ShapeDeserializer) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}

        def _consumer(schema: Schema, de: ShapeDeserializer) -> None:
            match schema.expect_member_index():
                case 0:
                    kwargs["records"] = _deserialize_record_list(
                        de, PUT_RECORDS_OUTPUT.members["records"]
                    )
                case _:
                    pass

        deserializer.read_struct(PUT_RECORDS_OUTPUT, consumer=_consumer)
        if "records" not in kwargs:
            kwargs["records"] = []
        return kwargs


PUT_RECORDS_OPERATION: APIOperation[PutRecordsInput, PutRecordsOutput] = APIOperation(
    input=PutRecordsInput,
    output=PutRecordsOutput,
    schema=PUT_RECORDS,
    input_schema=PUT_RECORDS_INPUT,
    output_schema=PUT_RECORDS_OUTPUT,
    error_registry=TypeRegistry({}),
    effective_auth_schemes=[ShapeID("smithy.api#noAuth")],
    error_schemas=[],
)
