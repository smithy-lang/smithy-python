#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from collections.abc import AsyncIterator
from io import BytesIO

import pytest
from smithy_aws_core.checksums import ChecksumMismatchError, ChecksumValidatingStream

DATA = b"hello world"
CRC32 = "DUoRhQ=="
WRONG = "AAAAAA=="


def _stream(source: object = DATA, expected: str = CRC32) -> ChecksumValidatingStream:
    return ChecksumValidatingStream(
        source,  # type: ignore[arg-type]
        checksum_algorithm="CRC32",
        expected=expected,
    )


async def _chunks(*parts: bytes) -> AsyncIterator[bytes]:
    for part in parts:
        yield part


async def test_read_all_validates() -> None:
    stream = _stream()
    assert stream.checksum_algorithm == "CRC32"
    assert not stream.validated

    assert await stream.read() == DATA
    assert stream.validated


async def test_sized_reads_validate_at_end_of_stream() -> None:
    stream = _stream(BytesIO(DATA))

    assert await stream.read(5) == b"hello"
    assert not stream.validated
    assert await stream.read(100) == b" world"
    # A short read isn't the end of the stream.
    assert not stream.validated
    assert await stream.read(100) == b""
    assert stream.validated


async def test_iteration_validates() -> None:
    stream = _stream(_chunks(b"hello", b" ", b"world"))

    assert b"".join([chunk async for chunk in stream]) == DATA
    assert stream.validated


async def test_mismatch_raises_from_the_read_that_reaches_the_end() -> None:
    stream = _stream(BytesIO(DATA), expected=WRONG)

    assert await stream.read(5) == b"hello"
    assert await stream.read(100) == b" world"
    with pytest.raises(ChecksumMismatchError) as exc_info:
        await stream.read(100)

    error = exc_info.value
    assert error.algorithm == "CRC32"
    assert error.expected == WRONG
    assert error.actual == CRC32
    assert error.is_retry_safe is False
    assert WRONG in str(error) and CRC32 in str(error)
    assert not stream.validated


async def test_mismatch_raises_when_iterating() -> None:
    stream = _stream(_chunks(DATA), expected=WRONG)

    with pytest.raises(ChecksumMismatchError):
        async for _ in stream:
            pass


async def test_partial_read_is_not_validated() -> None:
    stream = _stream(BytesIO(DATA), expected=WRONG)

    assert await stream.read(5) == b"hello"
    await stream.close()
    assert not stream.validated


async def test_reading_after_the_end_does_not_validate_again() -> None:
    stream = _stream()

    await stream.read()
    assert await stream.read() == b""
    assert stream.validated


async def test_zero_length_read_does_not_validate() -> None:
    stream = _stream(BytesIO(DATA))

    assert await stream.read(0) == b""
    assert not stream.validated
    assert await stream.read() == DATA
    assert stream.validated


async def test_iter_chunks_validates() -> None:
    stream = _stream(BytesIO(DATA))

    assert b"".join([chunk async for chunk in stream.iter_chunks(4)]) == DATA
    assert stream.validated


async def test_has_the_interface_of_an_async_bytes_reader() -> None:
    stream = _stream(BytesIO(DATA))

    assert stream.readable()
    assert not stream.seekable()
    assert not stream.closed
    with pytest.raises(NotImplementedError):
        await stream.seek(0)
    await stream.close()
    assert stream.closed


@pytest.mark.parametrize(
    "expected", ["", "DUoRhQ==-3", "DUoRhQ==,DUoRhQ==", "not base64!"]
)
def test_rejects_an_expected_value_that_is_not_a_checksum(expected: str) -> None:
    with pytest.raises(ValueError, match="Invalid CRC32 checksum"):
        _stream(expected=expected)


async def test_wrong_size_checksum_fails_validation() -> None:
    # The SEP's failure cases send base64 of "not-a-checksum".
    stream = _stream(expected="bm90LWEtY2hlY2tzdW0=")

    with pytest.raises(ChecksumMismatchError) as exc_info:
        await stream.read()
    assert exc_info.value.expected == "bm90LWEtY2hlY2tzdW0="
    assert exc_info.value.actual == CRC32


async def test_close_closes_the_source() -> None:
    source = BytesIO(DATA)
    stream = _stream(source)

    await stream.close()
    assert source.closed
