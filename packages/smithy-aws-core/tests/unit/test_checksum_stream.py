#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from io import BytesIO

import pytest
from smithy_aws_core.checksums import ChecksumMismatchError, ChecksumStream

DATA = b"hello world"
CRC32 = b"\x0dJ\x11\x85"
WRONG = b"\x00\x00\x00\x00"


def _stream(source: object = DATA, expected: bytes = CRC32) -> ChecksumStream:
    return ChecksumStream(
        source,  # type: ignore[arg-type]
        checksum_algorithm="CRC32",
        expected=expected,
    )


def test_read_all_validates() -> None:
    stream = _stream()
    assert stream.checksum_algorithm == "CRC32"
    assert not stream.validated

    assert stream.read() == DATA
    assert stream.validated


def test_sized_reads_validate_at_end_of_stream() -> None:
    stream = _stream(BytesIO(DATA))

    assert stream.read(5) == b"hello"
    assert not stream.validated
    assert stream.read(100) == b" world"
    # A short read isn't the end of the stream.
    assert not stream.validated
    assert stream.read(100) == b""
    assert stream.validated


def test_iteration_validates() -> None:
    stream = _stream(BytesIO(DATA))

    assert b"".join(stream) == DATA
    assert stream.validated


def test_mismatch_raises_from_the_read_that_reaches_the_end() -> None:
    stream = _stream(BytesIO(DATA), expected=WRONG)

    assert stream.read(5) == b"hello"
    assert stream.read(100) == b" world"
    with pytest.raises(ChecksumMismatchError) as exc_info:
        stream.read(100)

    error = exc_info.value
    assert error.algorithm == "CRC32"
    assert error.expected == WRONG
    assert error.actual == CRC32
    assert error.is_retry_safe is False
    assert str(error) == (
        "Expected a CRC32 checksum of AAAAAA==, but the payload's checksum was "
        "DUoRhQ==."
    )
    assert not stream.validated


def test_mismatch_raises_when_iterating() -> None:
    stream = _stream(BytesIO(DATA), expected=WRONG)

    with pytest.raises(ChecksumMismatchError):
        for _ in stream:
            pass


def test_partial_read_is_not_validated() -> None:
    stream = _stream(BytesIO(DATA), expected=WRONG)

    assert stream.read(5) == b"hello"
    stream.close()
    assert not stream.validated


def test_reading_after_the_end_does_not_validate_again() -> None:
    stream = _stream()

    stream.read()
    assert stream.read() == b""
    assert stream.validated


def test_zero_length_read_does_not_validate() -> None:
    stream = _stream(BytesIO(DATA))

    assert stream.read(0) == b""
    assert not stream.validated
    assert stream.read() == DATA
    assert stream.validated


def test_iter_chunks_validates() -> None:
    stream = _stream(BytesIO(DATA))

    assert b"".join(stream.iter_chunks(4)) == DATA
    assert stream.validated


def test_has_the_interface_of_a_bytes_reader() -> None:
    stream = _stream(BytesIO(DATA))

    assert stream.readable()
    assert not stream.seekable()
    assert not stream.closed
    with pytest.raises(NotImplementedError):
        stream.seek(0)
    stream.close()
    assert stream.closed


def test_wrong_size_checksum_fails_validation() -> None:
    stream = _stream(expected=b"not-a-checksum")

    with pytest.raises(ChecksumMismatchError) as exc_info:
        stream.read()
    assert exc_info.value.expected == b"not-a-checksum"
    assert exc_info.value.actual == CRC32


def test_close_closes_the_source() -> None:
    source = BytesIO(DATA)
    stream = _stream(source)

    stream.close()
    assert source.closed
