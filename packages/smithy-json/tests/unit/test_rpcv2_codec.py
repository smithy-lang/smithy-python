# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests for the RpcV2JSONCodec preset."""

from datetime import UTC, datetime
from typing import Any

import pytest
from smithy_core.documents import Document
from smithy_core.prelude import DOCUMENT, TIMESTAMP
from smithy_core.schemas import Schema
from smithy_core.types import TimestampFormat
from smithy_json import JSONCodec, JSONDocument, RpcV2JSONCodec
from smithy_json._private import JSONValueError
from smithy_json.settings import JSONSettings

from . import SCHEMA, SerdeShape

TIMESTAMP_VALUE = datetime(2024, 5, 15, tzinfo=UTC)
EPOCH_SECONDS = b"1715731200"


def _settings(codec: JSONCodec) -> JSONSettings:
    return codec._settings  # type: ignore[reportPrivateUsage]


def test_is_json_codec_subclass() -> None:
    assert isinstance(RpcV2JSONCodec(), JSONCodec)


def test_media_type() -> None:
    assert RpcV2JSONCodec().media_type == "application/json"


def test_settings_are_fixed_for_rpcv2_json() -> None:
    settings = _settings(RpcV2JSONCodec())
    assert settings.use_json_name is False
    assert settings.use_timestamp_format is False
    assert settings.default_timestamp_format is TimestampFormat.EPOCH_SECONDS
    assert settings.arbitrary_precision_as_string is True
    assert settings.default_namespace is None
    assert settings.document_class is JSONDocument


def test_default_namespace_is_honored() -> None:
    codec = RpcV2JSONCodec(default_namespace="com.example")
    assert _settings(codec).default_namespace == "com.example"


class CustomDocument(JSONDocument):
    pass


def test_document_class_is_honored() -> None:
    codec = RpcV2JSONCodec(document_class=CustomDocument)
    assert _settings(codec).document_class is CustomDocument
    actual = codec.create_deserializer(b'{"foo": "bar"}').read_document(DOCUMENT)
    assert isinstance(actual, CustomDocument)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"use_json_name": True},
        {"use_timestamp_format": True},
        {"default_timestamp_format": TimestampFormat.DATE_TIME},
        {"arbitrary_precision_as_string": False},
    ],
)
def test_rejects_other_constructor_arguments(kwargs: dict[str, Any]) -> None:
    with pytest.raises(TypeError):
        RpcV2JSONCodec(**kwargs)


def test_serialize_ignores_json_name() -> None:
    actual = RpcV2JSONCodec().serialize(SerdeShape(json_name_member="foo"))
    assert actual == b'{"jsonNameMember":"foo"}'


def test_deserialize_ignores_json_name() -> None:
    codec = RpcV2JSONCodec()
    actual = codec.deserialize(b'{"jsonNameMember":"foo"}', SerdeShape)
    assert actual == SerdeShape(json_name_member="foo")

    # The jsonName value is not recognized as a member name, so it's ignored.
    actual = codec.deserialize(b'{"jsonName":"foo"}', SerdeShape)
    assert actual == SerdeShape()


def test_typed_document_ignores_json_name() -> None:
    codec = RpcV2JSONCodec()
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
    codec = RpcV2JSONCodec()
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
        RpcV2JSONCodec().deserialize(source, SerdeShape)


@pytest.mark.parametrize(
    "schema",
    [
        TIMESTAMP,
        SCHEMA.members["dateTimeMember"],
        SCHEMA.members["httpDateMember"],
    ],
)
def test_timestamp_documents_are_epoch_seconds(schema: Schema) -> None:
    codec = RpcV2JSONCodec()
    assert codec.serialize(Document(TIMESTAMP_VALUE, schema=schema)) == EPOCH_SECONDS

    document = codec.create_deserializer(EPOCH_SECONDS).read_document(schema)
    assert document.as_timestamp() == TIMESTAMP_VALUE
