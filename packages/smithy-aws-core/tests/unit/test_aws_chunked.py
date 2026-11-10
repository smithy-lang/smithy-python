#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

import io
from collections.abc import AsyncIterator
from typing import Any

import pytest
from smithy_aws_core._aws_chunked import CHUNK_SIZE, AwsChunkedReader
from smithy_aws_core.aio._aws_chunked import AsyncAwsChunkedReader
from smithy_core.exceptions import SmithyError

DATA = b"Hello world"
# The CRC32 of DATA, from the flexible checksums test cases.
CRC32 = "i9aeUg=="


class _TrickleReader:
    """Returns a few bytes per read, as some streams do."""

    def __init__(self, data: bytes, step: int = 1000) -> None:
        self._data = io.BytesIO(data)
        self._step = step

    def read(self, size: int = -1) -> bytes:
        return self._data.read(self._step if size < 0 else min(size, self._step))


async def _chunks(data: bytes, step: int = 1000) -> AsyncIterator[bytes]:
    for i in range(0, len(data), step):
        yield data[i : i + step]


def _encode(payload: bytes, source: Any = None, **kwargs: Any) -> bytes:
    """Encode ``payload``, read from ``source`` if given."""
    return AwsChunkedReader(
        payload if source is None else source,
        decoded_length=len(payload),
        checksum_algorithm="CRC32",
        **kwargs,
    ).read()


def _decode(encoded: bytes) -> tuple[list[bytes], bytes]:
    """Split an encoded payload into its chunks and its trailer."""
    chunks: list[bytes] = []
    rest = encoded
    while True:
        size_line, rest = rest.split(b"\r\n", 1)
        size = int(size_line, 16)
        if size == 0:
            return chunks, rest
        chunks.append(rest[:size])
        assert rest[size : size + 2] == b"\r\n"
        rest = rest[size + 2 :]


def test_encodes_the_payload_with_a_trailing_checksum() -> None:
    assert _encode(DATA) == (
        b"b\r\nHello world\r\n0\r\nx-amz-checksum-crc32:" + CRC32.encode() + b"\r\n\r\n"
    )


def test_encodes_an_empty_payload() -> None:
    assert _encode(b"") == b"0\r\nx-amz-checksum-crc32:AAAAAA==\r\n\r\n"


def test_chunks_are_a_fixed_size_however_the_source_is_read() -> None:
    payload = bytes(range(256)) * 600  # 153,600 bytes

    encoded = _encode(payload, _TrickleReader(payload))

    chunks, _ = _decode(encoded)
    assert [len(chunk) for chunk in chunks] == [CHUNK_SIZE, CHUNK_SIZE, 22528]
    assert b"".join(chunks) == payload
    assert encoded == _encode(payload)


def test_reports_the_checksum_once_the_payload_is_read() -> None:
    payload = b"x" * (CHUNK_SIZE * 2)
    reported: list[str] = []
    reader = AwsChunkedReader(
        payload,
        decoded_length=len(payload),
        checksum_algorithm="CRC32",
        on_checksum=reported.append,
    )

    # A partly read payload has no checksum to reuse on a retry.
    reader.read(10)
    assert reported == []
    reader.read()
    assert len(reported) == 1


def test_sends_a_given_checksum_without_calculating_one() -> None:
    reported: list[str] = []

    encoded = _encode(DATA, checksum="AAAAAA==", on_checksum=reported.append)

    assert encoded.endswith(b"x-amz-checksum-crc32:AAAAAA==\r\n\r\n")
    assert reported == []


def test_sync_reader_is_an_io_stream() -> None:
    # The CRT HTTP client only sends io streams.
    reader = AwsChunkedReader(
        DATA, decoded_length=len(DATA), checksum_algorithm="CRC32"
    )

    assert isinstance(reader, io.RawIOBase)
    assert reader.readable()
    assert not reader.seekable()
    assert b"".join(iter(lambda: reader.read(7), b"")) == _encode(DATA)


def _as_bytes(data: bytes) -> Any:
    return data


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(_as_bytes, id="bytes"),
        pytest.param(io.BytesIO, id="sync-reader"),
        pytest.param(_chunks, id="async-iterable"),
    ],
)
async def test_async_reader_matches_the_sync_reader(source: Any) -> None:
    payload = bytes(range(256)) * 600
    reader = AsyncAwsChunkedReader(
        source(payload), decoded_length=len(payload), checksum_algorithm="CRC32"
    )

    encoded = b"".join([chunk async for chunk in reader])

    assert encoded == _encode(payload)


async def test_async_reader_reports_and_reuses_checksums() -> None:
    reported: list[str] = []
    reader = AsyncAwsChunkedReader(
        _chunks(DATA),
        decoded_length=len(DATA),
        checksum_algorithm="CRC32",
        on_checksum=reported.append,
    )
    assert await reader.read() == _encode(DATA)
    assert reported == [CRC32]

    retried = AsyncAwsChunkedReader(
        b"changed!!!!",
        decoded_length=len(DATA),
        checksum_algorithm="CRC32",
        checksum=CRC32,
    )
    assert (await retried.read()).endswith(b":" + CRC32.encode() + b"\r\n\r\n")


# A payload longer than its declared length is cut off at that length, and a shorter
# one fails.
SNAPSHOT_SIZES = pytest.mark.parametrize(
    "size", [10, CHUNK_SIZE, CHUNK_SIZE + 10], ids=["small", "one-chunk", "two-chunks"]
)


@SNAPSHOT_SIZES
def test_sends_only_the_declared_length_of_a_longer_payload(size: int) -> None:
    payload = bytes(range(256)) * (size // 256 + 1)

    reader = AwsChunkedReader(
        io.BytesIO(payload + b"excess"),
        decoded_length=size,
        checksum_algorithm="CRC32",
    )
    encoded = reader.read()

    assert encoded == _encode(payload[:size])


@SNAPSHOT_SIZES
def test_fails_a_payload_shorter_than_its_declared_length(size: int) -> None:
    reported: list[str] = []
    reader = AwsChunkedReader(
        io.BytesIO(b"x" * (size - 1)),
        decoded_length=size,
        checksum_algorithm="CRC32",
        on_checksum=reported.append,
    )

    with pytest.raises(SmithyError, match=f"after {size - 1} bytes.*length is {size}"):
        reader.read()
    # A short payload's checksum mustn't be reused on a retry.
    assert reported == []


def test_fails_a_source_with_no_data_ready() -> None:
    # A non-blocking raw stream returns None when no data is ready yet.
    source = io.BytesIO(DATA)
    source.read = lambda size=-1: None  # type: ignore[method-assign]
    reader = AwsChunkedReader(
        source, decoded_length=len(DATA), checksum_algorithm="CRC32"
    )

    with pytest.raises(SmithyError, match="after 0 bytes"):
        reader.read()


@SNAPSHOT_SIZES
async def test_async_reader_sends_only_the_declared_length(size: int) -> None:
    payload = bytes(range(256)) * (size // 256 + 1)
    reader = AsyncAwsChunkedReader(
        _chunks(payload + b"excess"), decoded_length=size, checksum_algorithm="CRC32"
    )

    assert await reader.read() == _encode(payload[:size])


@SNAPSHOT_SIZES
async def test_async_reader_fails_a_shorter_payload(size: int) -> None:
    reported: list[str] = []
    reader = AsyncAwsChunkedReader(
        _chunks(b"x" * (size - 1)),
        decoded_length=size,
        checksum_algorithm="CRC32",
        on_checksum=reported.append,
    )

    with pytest.raises(SmithyError, match=f"after {size - 1} bytes.*length is {size}"):
        await reader.read()
    assert reported == []


async def test_async_reader_close_leaves_the_payload_open() -> None:
    # The caller owns the payload, and a retry rewinds it to send it again.
    source = io.BytesIO(DATA)
    reader = AsyncAwsChunkedReader(
        source, decoded_length=len(DATA), checksum_algorithm="CRC32"
    )
    await reader.read()

    await reader.close()

    assert not source.closed
    source.seek(0)
