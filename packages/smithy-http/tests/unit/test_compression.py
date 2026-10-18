# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import gzip
from collections.abc import AsyncIterator
from io import BytesIO
from types import SimpleNamespace
from typing import Any, cast

import pytest
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.aio.utils import close
from smithy_core.schemas import APIOperation, Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    DynamicTrait,
    RequestCompressionTrait,
    RequiresLengthTrait,
    Trait,
)
from smithy_core.types import TypedProperties
from smithy_http import Field, Fields
from smithy_http.compression import RequestCompression


def make_policy(
    *,
    encodings: list[str] | None = None,
    modeled: bool = True,
    explicit: str | None = None,
    disabled: bool = False,
    threshold: int = 10240,
    stream: Schema | None = None,
) -> RequestCompression:
    traits: list[Trait | DynamicTrait] = (
        [RequestCompressionTrait({"encodings": encodings or ["gzip"]})]
        if modeled
        else []
    )
    operation = SimpleNamespace(
        schema=Schema(
            id=ShapeID("example#Compress"),
            shape_type=ShapeType.OPERATION,
            traits=traits,
        ),
        input_schema=Schema.collection(id=ShapeID("example#Input")),
        input_stream_member=stream,
    )
    context = TypedProperties(
        {
            "config": SimpleNamespace(
                request_compression_encoding=explicit,
                disable_request_compression=disabled,
                request_min_compression_size_bytes=threshold,
            )
        }
    )
    return RequestCompression.from_operation(
        cast(APIOperation[Any, Any], operation), context
    )


@pytest.mark.parametrize(
    "payload", [b"", b"hello", bytearray(b"hello"), BytesIO(b"hello")]
)
async def test_explicit_gzip_round_trip_below_threshold(
    payload: bytes | bytearray | BytesIO,
) -> None:
    expected = payload.getvalue() if isinstance(payload, BytesIO) else payload
    fields = Fields([Field(name="Content-Length", values=["999"])])
    result = make_policy(explicit="gzip").compress(payload, fields)
    wire = await AsyncBytesReader(result).read()
    assert gzip.decompress(wire) == expected
    assert fields["Content-Encoding"].as_string() == "gzip"
    assert int(fields["Content-Length"].as_string()) == len(wire)


@pytest.mark.parametrize(
    "size, compressed", [(10239, False), (10240, True), (10241, True)]
)
async def test_automatic_compression_threshold(size: int, compressed: bool) -> None:
    payload = b"x" * size
    fields = Fields()
    result = make_policy().compress(payload, fields)
    wire = await AsyncBytesReader(result).read()
    if compressed:
        assert gzip.decompress(wire) == payload
        assert fields["Content-Encoding"].as_string() == "gzip"
    else:
        assert wire == payload
        assert "Content-Encoding" not in fields


@pytest.mark.parametrize(
    "kwargs", [{"modeled": False}, {"disabled": True}, {"encodings": ["unknown"]}]
)
async def test_automatic_compression_skips_ineligible_request(
    kwargs: dict[str, Any],
) -> None:
    payload = b"x" * 11000
    fields = Fields()
    result = make_policy(**kwargs).compress(payload, fields)
    assert await AsyncBytesReader(result).read() == payload
    assert "Content-Encoding" not in fields


@pytest.mark.parametrize(
    "kwargs", [{"modeled": False}, {"disabled": True}, {"encodings": ["unknown"]}]
)
def test_explicit_gzip_fails_instead_of_silent_fallback(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match=r"gzip|compression"):
        make_policy(explicit="gzip", **kwargs).compress(b"hello", Fields())


def test_unknown_explicit_codec_is_rejected() -> None:
    with pytest.raises(ValueError, match=r"zstd|encoding"):
        make_policy(explicit="zstd").compress(b"hello", Fields())


async def test_gzip_appends_existing_content_encoding() -> None:
    fields = Fields([Field(name="Content-Encoding", values=["identity"])])
    wire = await AsyncBytesReader(
        make_policy(explicit="gzip").compress(b"hello", fields)
    ).read()
    assert gzip.decompress(wire) == b"hello"
    assert "identity" in fields["Content-Encoding"].as_string()
    assert "gzip" in fields["Content-Encoding"].as_string()


async def test_streaming_gzip_is_lazy_and_lossless() -> None:
    reads: list[bytes] = []

    async def source() -> AsyncIterator[bytes]:
        for part in (b"first", b"", b"second" * 20000):
            reads.append(part)
            yield part

    fields = Fields([Field(name="Content-Length", values=["123"])])
    result = make_policy().compress(source(), fields, streaming=True)
    assert reads == []
    assert "Content-Length" not in fields
    wire = await AsyncBytesReader(result).read()
    assert gzip.decompress(wire) == b"first" + b"second" * 20000
    assert len(reads) == 3


async def test_closing_compressed_stream_closes_underlying_source() -> None:
    source = BytesIO(b"hello")
    result = make_policy().compress(source, Fields(), streaming=True)
    await close(result)
    assert source.closed


async def test_closing_partially_read_compressed_async_generator_closes_source() -> (
    None
):
    closed = False

    async def source() -> AsyncIterator[bytes]:
        nonlocal closed
        try:
            yield b"x" * 65536
            yield b"second chunk"
        finally:
            closed = True

    stream = source()
    result = AsyncBytesReader(make_policy().compress(stream, Fields(), streaming=True))
    assert await result.read(1)
    assert not closed
    await close(result)
    assert closed
    with pytest.raises(StopAsyncIteration):
        await anext(stream)


@pytest.mark.parametrize("kind", ["requires_length", "eventstream"])
async def test_incompatible_streams_are_skipped_or_rejected(kind: str) -> None:
    target = Schema(
        id=ShapeID("example#Stream"),
        shape_type=ShapeType.BLOB if kind == "requires_length" else ShapeType.UNION,
        traits=[RequiresLengthTrait()] if kind == "requires_length" else [],
    )
    stream = Schema.member(ShapeID("example#Input$payload"), target, 0)
    fields = Fields()
    body = b"wire-stream"
    assert (
        await AsyncBytesReader(
            make_policy(stream=stream).compress(body, fields, streaming=True)
        ).read()
        == body
    )
    assert "Content-Encoding" not in fields
    with pytest.raises(ValueError, match="gzip"):
        make_policy(explicit="gzip", stream=stream)
