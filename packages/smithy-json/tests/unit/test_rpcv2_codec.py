# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests for a JSONCodec configured for smithy.protocols#rpcv2Json."""

from datetime import UTC, datetime

import pytest
import smithy_json
from smithy_core.documents import Document
from smithy_core.prelude import DOCUMENT, TIMESTAMP
from smithy_core.schemas import Schema
from smithy_core.types import TimestampFormat
from smithy_json import JSONCodec, JSONDocument
from smithy_json._private import JSONValueError
from smithy_json.settings import JSONSettings

from . import SCHEMA, SerdeShape, rpcv2_json_codec

TIMESTAMP_VALUE = datetime(2024, 5, 15, tzinfo=UTC)
EPOCH_SECONDS = b"1715731200"


def _settings(codec: JSONCodec) -> JSONSettings:
    return codec._settings  # type: ignore[reportPrivateUsage]


def test_public_api_has_no_rpcv2_json_symbols() -> None:
    assert smithy_json.__all__ == ("JSONCodec", "JSONDocument", "JSONSettings")


def test_media_type() -> None:
    assert rpcv2_json_codec().media_type == "application/json"


def test_settings_are_configured_for_rpcv2_json() -> None:
    settings = _settings(rpcv2_json_codec())
    assert settings.use_json_name is False
    assert settings.use_timestamp_format is False
    assert settings.default_timestamp_format is TimestampFormat.EPOCH_SECONDS
    assert settings.arbitrary_precision_as_string is True
    assert settings.default_namespace is None
    assert settings.document_class is JSONDocument


def test_default_namespace_is_honored() -> None:
    codec = rpcv2_json_codec(default_namespace="com.example")
    assert _settings(codec).default_namespace == "com.example"


class CustomDocument(JSONDocument):
    pass


def test_document_class_is_honored() -> None:
    codec = rpcv2_json_codec(document_class=CustomDocument)
    assert _settings(codec).document_class is CustomDocument
    actual = codec.create_deserializer(b'{"foo": "bar"}').read_document(DOCUMENT)
    assert isinstance(actual, CustomDocument)


def test_serialize_ignores_json_name() -> None:
    actual = rpcv2_json_codec().serialize(SerdeShape(json_name_member="foo"))
    assert actual == b'{"jsonNameMember":"foo"}'


def test_deserialize_ignores_json_name() -> None:
    codec = rpcv2_json_codec()
    actual = codec.deserialize(b'{"jsonNameMember":"foo"}', SerdeShape)
    assert actual == SerdeShape(json_name_member="foo")

    # The jsonName value is not recognized as a member name, so it's ignored.
    actual = codec.deserialize(b'{"jsonName":"foo"}', SerdeShape)
    assert actual == SerdeShape()


def test_typed_document_ignores_json_name() -> None:
    codec = rpcv2_json_codec()
    serialized = codec.serialize(Document({"jsonNameMember": "foo"}, schema=SCHEMA))
    assert serialized == b'{"jsonNameMember":"foo"}'

    document = codec.create_deserializer(b'{"jsonNameMember":"foo"}').read_document(
        SCHEMA
    )
    assert document.as_value() == {"jsonNameMember": "foo"}


@pytest.mark.parametrize(
    "shape, expected",
    [
        (
            SerdeShape(timestamp_member=TIMESTAMP_VALUE),
            b'{"timestampMember":' + EPOCH_SECONDS + b"}",
        ),
        (
            SerdeShape(date_time_member=TIMESTAMP_VALUE),
            b'{"dateTimeMember":' + EPOCH_SECONDS + b"}",
        ),
        (
            SerdeShape(http_date_member=TIMESTAMP_VALUE),
            b'{"httpDateMember":' + EPOCH_SECONDS + b"}",
        ),
        (
            SerdeShape(epoch_seconds_member=TIMESTAMP_VALUE),
            b'{"epochSecondsMember":' + EPOCH_SECONDS + b"}",
        ),
    ],
)
def test_timestamps_are_epoch_seconds(shape: SerdeShape, expected: bytes) -> None:
    codec = rpcv2_json_codec()
    assert codec.serialize(shape) == expected
    assert codec.deserialize(expected, SerdeShape) == shape


@pytest.mark.parametrize(
    "member_name",
    ["dateTimeMember", "httpDateMember"],
)
def test_timestamp_format_trait_string_is_rejected(member_name: str) -> None:
    # The timestampFormat trait is ignored, so a value in the trait's format is not
    # accepted in place of epoch-seconds.
    source = b'{"' + member_name.encode() + b'":"2024-05-15T00:00:00Z"}'
    with pytest.raises(JSONValueError):
        rpcv2_json_codec().deserialize(source, SerdeShape)


@pytest.mark.parametrize(
    "schema",
    [
        TIMESTAMP,
        SCHEMA.members["dateTimeMember"],
        SCHEMA.members["httpDateMember"],
    ],
)
def test_timestamp_documents_are_epoch_seconds(schema: Schema) -> None:
    codec = rpcv2_json_codec()
    assert codec.serialize(Document(TIMESTAMP_VALUE, schema=schema)) == EPOCH_SECONDS

    document = codec.create_deserializer(EPOCH_SECONDS).read_document(schema)
    assert document.as_timestamp() == TIMESTAMP_VALUE
