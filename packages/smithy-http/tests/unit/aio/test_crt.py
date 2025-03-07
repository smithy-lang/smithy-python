#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from copy import deepcopy

import pytest

from smithy_http.aio.crt import AWSCRTHTTPClient, BufferableByteStream


def test_deepcopy_client() -> None:
    client = AWSCRTHTTPClient()
    deepcopy(client)


def test_stream_write() -> None:
    stream = BufferableByteStream()
    stream.write(b"foo")
    assert stream.read() == b"foo"


def test_stream_reads_individual_chunks() -> None:
    stream = BufferableByteStream()
    stream.write(b"foo")
    stream.write(b"bar")
    assert stream.read() == b"foo"
    assert stream.read() == b"bar"


def test_stream_empty_read() -> None:
    stream = BufferableByteStream()
    with pytest.raises(BlockingIOError):
        stream.read()


def test_stream_partial_chunk_read() -> None:
    stream = BufferableByteStream()
    stream.write(b"foobar")
    assert stream.read(3) == b"foo"
    assert stream.read() == b"bar"


def test_stream_write_empty_bytes() -> None:
    stream = BufferableByteStream()
    stream.write(b"")
    stream.write(b"foo")
    stream.write(b"")
    assert stream.read() == b"foo"


def test_stream_write_non_bytes() -> None:
    stream = BufferableByteStream()
    with pytest.raises(ValueError):
        stream.write(memoryview(b"foo"))


def test_closed_stream_write() -> None:
    stream = BufferableByteStream()
    stream.close()
    with pytest.raises(IOError):
        stream.write(b"foo")


def test_closed_stream_read() -> None:
    stream = BufferableByteStream()
    stream.write(b"foo")
    stream.close()
    assert stream.read() == b""


def test_stream_read1() -> None:
    stream = BufferableByteStream()
    stream.write(b"foo")
    stream.write(b"bar")
    assert stream.read1() == b"foo"
    assert stream.read1() == b"bar"
    with pytest.raises(BlockingIOError):
        stream.read()


def test_stream_readinto_memoryview() -> None:
    buffer = memoryview(bytearray(b"   "))
    stream = BufferableByteStream()
    stream.write(b"foobar")
    stream.readinto(buffer)
    assert bytes(buffer) == b"foo"


def test_stream_readinto_bytearray() -> None:
    buffer = bytearray(b"   ")
    stream = BufferableByteStream()
    stream.write(b"foobar")
    stream.readinto(buffer)
    assert bytes(buffer) == b"foo"


def test_end_stream() -> None:
    stream = BufferableByteStream()
    stream.write(b"foo")
    stream.end_stream()

    assert not stream.closed
    assert stream.read() == b"foo"
    assert stream.closed
