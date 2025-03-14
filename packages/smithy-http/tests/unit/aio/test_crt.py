#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
from copy import deepcopy
from io import BytesIO
from unittest.mock import Mock
from concurrent.futures import Future as ConcurrentFuture

import pytest
from awscrt.http import HttpClientStream  # type: ignore

from smithy_core import URI
from smithy_http import Fields
from smithy_http.aio import HTTPRequest
from smithy_http.aio.crt import AWSCRTHTTPClient, BufferableByteStream, CRTResponseBody


def test_deepcopy_client() -> None:
    client = AWSCRTHTTPClient()
    deepcopy(client)


async def test_client_marshal_request() -> None:
    client = AWSCRTHTTPClient()
    request = HTTPRequest(
        method="GET",
        destination=URI(
            host="example.com", path="/path", query="key1=value1&key2=value2"
        ),
        body=BytesIO(),
        fields=Fields(),
    )
    crt_request, _ = await client._marshal_request(request)  # type: ignore
    assert crt_request.headers.get("host") == "example.com"  # type: ignore
    assert crt_request.headers.get("accept") == "*/*"  # type: ignore
    assert crt_request.method == "GET"  # type: ignore
    assert crt_request.path == "/path?key1=value1&key2=value2"  # type: ignore


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


def test_done_stream_read() -> None:
    stream = BufferableByteStream()
    stream.write(b"foo")
    stream.end_stream()
    assert stream.read() == b"foo"
    assert stream.read() == b""


def test_end_empty_stream() -> None:
    stream = BufferableByteStream()
    stream.end_stream()
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


async def test_response_body_completed_stream() -> None:
    completion_future = ConcurrentFuture[int]()
    mock_stream = Mock(spec=HttpClientStream)
    mock_stream.completion_future = completion_future

    response_body = CRTResponseBody()
    response_body.set_stream(mock_stream)
    completion_future.set_result(200)

    assert await response_body.next() == b""


async def test_response_body_empty_stream() -> None:
    completion_future = ConcurrentFuture[int]()
    mock_stream = Mock(spec=HttpClientStream)
    mock_stream.completion_future = completion_future

    response_body = CRTResponseBody()
    response_body.set_stream(mock_stream)

    read_task = asyncio.create_task(response_body.next())

    # Sleep briefly so the read task gets priority. It should
    # add a chunk future and then await it.
    await asyncio.sleep(0.01)

    assert len(response_body._chunk_futures) == 1  # type: ignore
    response_body.on_body(b"foo")
    assert await read_task == b"foo"


async def test_response_body_stream_completion_clears_buffer() -> None:
    completion_future = ConcurrentFuture[int]()
    mock_stream = Mock(spec=HttpClientStream)
    mock_stream.completion_future = completion_future

    response_body = CRTResponseBody()
    response_body.set_stream(mock_stream)

    read_tasks = (
        asyncio.create_task(response_body.next()),
        asyncio.create_task(response_body.next()),
        asyncio.create_task(response_body.next()),
        asyncio.create_task(response_body.next()),
    )

    # Sleep briefly so the read tasks gets priority. It should
    # add a chunk future and then await it.
    await asyncio.sleep(0.01)

    assert len(response_body._chunk_futures) == 4  # type: ignore
    completion_future.set_result(200)
    await asyncio.sleep(0.01)

    # Tasks should have been drained
    assert len(response_body._chunk_futures) == 0  # type: ignore

    # Tasks should still be awaited, and should all return empty
    results = asyncio.gather(*read_tasks)
    assert results.result() == [b"", b"", b"", b""]


async def test_response_body_non_empty_stream() -> None:
    completion_future = ConcurrentFuture[int]()
    mock_stream = Mock(spec=HttpClientStream)
    mock_stream.completion_future = completion_future

    response_body = CRTResponseBody()
    response_body.set_stream(mock_stream)
    response_body.on_body(b"foo")

    assert await response_body.next() == b"foo"
