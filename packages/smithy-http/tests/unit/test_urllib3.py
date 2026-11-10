#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import threading
import tracemalloc
from collections.abc import Iterator
from hashlib import sha256
from io import BytesIO
from typing import Any
from unittest.mock import Mock

import pytest
import urllib3
from smithy_core import URI
from smithy_core.exceptions import ClientTimeoutError
from smithy_core.interfaces import is_bytes_reader
from smithy_core.utils import read_streaming_blob
from smithy_http import Field, Fields, HTTPRequest
from smithy_http.exceptions import SmithyHTTPError
from smithy_http.interfaces import HTTPRequestConfiguration
from smithy_http.urllib3 import Urllib3HTTPClient, Urllib3HTTPClientConfig

from ._local_server import LocalHTTPServer, Reply


def _send(
    config: Urllib3HTTPClientConfig | None = None,
    request_config: HTTPRequestConfiguration | None = None,
) -> Any:
    pool = Mock()
    pool.request.return_value = Mock(
        status=200, headers=urllib3.HTTPHeaderDict(), data=b"", reason="OK"
    )
    client = Urllib3HTTPClient(client_config=config, _pool=pool)
    request = HTTPRequest(
        destination=URI(host="example.com"), method="GET", fields=Fields()
    )
    client.send(request, request_config=request_config)
    return pool.request.call_args.kwargs["timeout"]


def test_requests_time_out_by_default() -> None:
    timeout = _send()
    assert timeout.connect_timeout == 60.0
    assert timeout.read_timeout == 60.0


def test_client_config_sets_the_timeouts() -> None:
    timeout = _send(Urllib3HTTPClientConfig(connect_timeout=1.0, read_timeout=None))
    assert timeout.connect_timeout == 1.0
    assert timeout.read_timeout is None


@pytest.mark.parametrize("client_read_timeout", [None, 30.0])
def test_request_read_timeout_takes_precedence(
    client_read_timeout: float | None,
) -> None:
    timeout = _send(
        Urllib3HTTPClientConfig(read_timeout=client_read_timeout),
        HTTPRequestConfiguration(read_timeout=5.0),
    )
    assert timeout.read_timeout == 5.0


@pytest.mark.parametrize(
    ("config", "maxsize"),
    [(None, 10), (Urllib3HTTPClientConfig(max_pool_connections=25), 25)],
)
def test_pool_keeps_the_configured_connections_per_host(
    config: Urllib3HTTPClientConfig | None, maxsize: int
) -> None:
    client = Urllib3HTTPClient(client_config=config)
    pool = client._pool.connection_from_host("example.com")  # pyright: ignore[reportPrivateUsage]
    assert pool.pool is not None
    assert pool.pool.maxsize == maxsize
    client.close()


def test_repeated_response_headers_are_merged_case_insensitively() -> None:
    pool = Mock()
    raw_headers = urllib3.HTTPHeaderDict()
    raw_headers.add("X-Values", "a")
    raw_headers.add("x-values", "b")
    pool.request.return_value = Mock(
        status=200, headers=raw_headers, data=b"", reason="OK"
    )
    client = Urllib3HTTPClient(_pool=pool)
    request = HTTPRequest(
        destination=URI(host="example.com"), method="GET", fields=Fields()
    )

    response = client.send(request)

    assert response.fields["x-values"].values == ["a", "b"]
    assert response.fields["x-values"].kind == "header"


def test_trailer_fields_are_not_sent_as_headers() -> None:
    pool = Mock()
    pool.request.return_value = Mock(
        status=200, headers=urllib3.HTTPHeaderDict(), data=b"", reason="OK"
    )
    client = Urllib3HTTPClient(_pool=pool)
    request = HTTPRequest(
        destination=URI(host="example.com"),
        method="PUT",
        fields=Fields(
            [
                Field(name="x-amz-meta-a", values=["1"]),
                Field(name="x-amz-checksum-crc32", values=["AAAAAA=="], kind="trailer"),
            ]
        ),
    )

    client.send(request)

    headers = pool.request.call_args.kwargs["headers"]
    assert list(headers.items()) == [("x-amz-meta-a", "1")]


# The tests below send real requests to a local server, so they exercise urllib3's
# connection pooling rather than a mock of it.


@pytest.fixture
def server() -> Iterator[LocalHTTPServer]:
    with LocalHTTPServer() as server:
        yield server


def _local_body(client: Urllib3HTTPClient, server: LocalHTTPServer) -> Any:
    request = HTTPRequest(
        destination=URI(scheme="http", host="127.0.0.1", port=server.port),
        method="GET",
        fields=Fields(),
    )
    body = client.send(request).body
    assert is_bytes_reader(body)
    return body


def _connection_pool(
    pool: urllib3.PoolManager, server: LocalHTTPServer
) -> urllib3.HTTPConnectionPool:
    return pool.connection_from_host("127.0.0.1", server.port, scheme="http")


def _idle_connections(pool: urllib3.PoolManager, server: LocalHTTPServer) -> int:
    """Connections back in the pool, open or not."""
    queue = _connection_pool(pool, server).pool
    assert queue is not None
    return queue.qsize()


def test_response_body_is_streamed(server: LocalHTTPServer) -> None:
    payload = bytes(range(256)) * 32 * 1024  # 8 MiB
    server.replies = [Reply(body=payload)]
    with Urllib3HTTPClient() as client:
        body = _local_body(client, server)

        first = body.read(1024)
        chunks = [first, *body.iter_chunks(1024 * 1024)]
        # Generic consumers such as read_streaming_blob treat it as a sync reader.
        assert is_bytes_reader(body)

    assert all(len(chunk) <= 1024 * 1024 for chunk in chunks)
    assert len(chunks) > 8
    assert b"".join(chunks) == payload


def test_body_read_to_the_end_returns_connection_to_the_pool(
    server: LocalHTTPServer,
) -> None:
    server.replies = [Reply(body=b"first"), Reply(body=b"second")]
    pool = urllib3.PoolManager()
    client = Urllib3HTTPClient(_pool=pool)

    assert read_streaming_blob(_local_body(client, server)) == b"first"
    assert _idle_connections(pool, server) == 1
    assert read_streaming_blob(_local_body(client, server)) == b"second"

    assert server.ports[0] == server.ports[1]
    assert _connection_pool(pool, server).num_connections == 1


def test_closing_a_partly_read_body_discards_its_connection(
    server: LocalHTTPServer,
) -> None:
    server.replies = [Reply(body=b"x" * 100_000), Reply(body=b"next")]
    pool = urllib3.PoolManager()
    client = Urllib3HTTPClient(_pool=pool)

    with _local_body(client, server) as body:
        assert body.read(10) == b"x" * 10
        assert _idle_connections(pool, server) == 0
    assert body.closed
    # The slot is back in the pool, but its connection is closed, so the next
    # request opens a new one.
    assert _idle_connections(pool, server) == 1

    assert read_streaming_blob(_local_body(client, server)) == b"next"
    assert server.ports[0] != server.ports[1]


def test_close_after_reading_to_the_end_keeps_the_connection(
    server: LocalHTTPServer,
) -> None:
    server.replies = [Reply(body=b"first"), Reply(body=b"second")]
    client = Urllib3HTTPClient()

    body = _local_body(client, server)
    assert body.read() == b"first"
    body.close()
    body.close()
    assert _local_body(client, server).read() == b"second"

    assert server.ports[0] == server.ports[1]


def test_read_after_close_raises(server: LocalHTTPServer) -> None:
    server.replies = [Reply(body=b"data")]
    body = _local_body(Urllib3HTTPClient(), server)
    body.close()

    with pytest.raises(ValueError, match="closed"):
        body.read()


def test_empty_body_reads_as_empty(server: LocalHTTPServer) -> None:
    server.replies = [Reply(status=204), Reply(body=b"next")]
    client = Urllib3HTTPClient()

    assert _local_body(client, server).read() == b""
    assert _local_body(client, server).read() == b"next"
    assert server.ports[0] == server.ports[1]


def test_truncated_body_raises_http_error(server: LocalHTTPServer) -> None:
    server.replies = [Reply(body=b"short", truncate=True)]
    body = _local_body(Urllib3HTTPClient(), server)

    with pytest.raises(SmithyHTTPError, match="Failed to read the response body"):
        body.read()


def test_stalled_body_raises_client_timeout(server: LocalHTTPServer) -> None:
    server.replies = [Reply(body=b"x" * 100, stall_after=10)]
    client = Urllib3HTTPClient(client_config=Urllib3HTTPClientConfig(read_timeout=0.2))
    body = _local_body(client, server)

    assert body.read(10) == b"x" * 10
    with pytest.raises(ClientTimeoutError):
        body.read()


def test_body_can_be_read_after_the_client_closes(server: LocalHTTPServer) -> None:
    server.replies = [Reply(body=b"x" * 100_000)]
    client = Urllib3HTTPClient()
    body = _local_body(client, server)

    client.close()

    assert body.read() == b"x" * 100_000


def test_send_returns_before_the_body_arrives(server: LocalHTTPServer) -> None:
    gate = threading.Event()
    server.replies = [Reply(body=b"late", gate=gate)]
    client = Urllib3HTTPClient()

    body = _local_body(client, server)
    gate.set()

    assert body.read() == b"late"


def test_exact_size_read_returns_the_connection(server: LocalHTTPServer) -> None:
    server.replies = [Reply(body=b"0123456789"), Reply(body=b"next")]
    pool = urllib3.PoolManager()
    client = Urllib3HTTPClient(_pool=pool)

    body = _local_body(client, server)
    assert body.read(10) == b"0123456789"
    # Reading the whole Content-Length ends the body without another, empty read.
    assert _idle_connections(pool, server) == 1

    assert _local_body(client, server).read() == b"next"
    assert server.ports[0] == server.ports[1]


def test_chunked_body_is_streamed(server: LocalHTTPServer) -> None:
    payload = b"x" * 300_000
    server.replies = [Reply(body=payload, chunked=True, chunk_size=1000)]
    pool = urllib3.PoolManager()
    client = Urllib3HTTPClient(_pool=pool)

    body = _local_body(client, server)
    chunks = list(body.iter_chunks(64 * 1024))

    assert b"".join(chunks) == payload
    assert all(len(chunk) <= 64 * 1024 for chunk in chunks)
    assert _idle_connections(pool, server) == 1


def test_body_is_a_read_only_stream(server: LocalHTTPServer) -> None:
    server.replies = [Reply(body=b"data")]
    with _local_body(Urllib3HTTPClient(), server) as body:
        assert body.readable()
        assert not body.writeable()
        assert not body.seekable()


def test_large_body_is_not_buffered(server: LocalHTTPServer) -> None:
    size = 32 * 1024 * 1024
    server.replies = [Reply(body=b"\0" * size)]

    tracemalloc.start()
    try:
        body = _local_body(Urllib3HTTPClient(), server)
        received = sum(len(chunk) for chunk in body.iter_chunks(64 * 1024))
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert received == size
    assert peak < size // 8


def _sent_body(request: HTTPRequest) -> Any:
    """The body the client gives urllib3 for a request."""
    pool = Mock()
    pool.request.return_value = Mock(
        status=200, headers=urllib3.HTTPHeaderDict(), data=b"", reason="OK"
    )
    Urllib3HTTPClient(_pool=pool).send(request)
    return pool.request.call_args.kwargs["body"]


def _upload(body: Any, fields: list[Field], port: int = 443) -> HTTPRequest:
    return HTTPRequest(
        destination=URI(scheme="http", host="127.0.0.1", port=port, path="/k"),
        method="PUT",
        body=body,
        fields=Fields(fields),
    )


@pytest.mark.parametrize(
    "framing",
    [
        pytest.param(Field(name="Content-Length", values=["5"]), id="content-length"),
        pytest.param(Field(name="Transfer-Encoding", values=["chunked"]), id="chunked"),
    ],
)
def test_request_readers_with_framing_are_streamed(framing: Field) -> None:
    body = BytesIO(b"hello")

    assert _sent_body(_upload(body, [framing])) is body


def test_request_bodies_are_streamed_in_large_blocks() -> None:
    pool = Urllib3HTTPClient()._pool  # pyright: ignore[reportPrivateUsage]

    assert pool.connection_pool_kw["blocksize"] == 128 * 1024


def test_request_readers_of_unknown_length_are_read_first() -> None:
    # urllib3 would send a reader without a length chunked, which services such as
    # S3 reject, so it's read and sent with its length.
    assert _sent_body(_upload(BytesIO(b"hello"), [])) == b"hello"


def test_request_bytes_are_sent_as_is() -> None:
    assert _sent_body(_upload(b"hello", [])) == b"hello"


class _GeneratedReader:
    """Produces ``size`` bytes as it's read, without holding them."""

    def __init__(self, size: int) -> None:
        self._left = size
        self.digest = sha256()

    def read(self, size: int = -1) -> bytes:
        n = self._left if size < 0 else min(size, self._left)
        self._left -= n
        data = b"\0" * n
        self.digest.update(data)
        return data


def test_large_request_body_is_not_buffered(server: LocalHTTPServer) -> None:
    size = 32 * 1024 * 1024
    body = _GeneratedReader(size)
    request = _upload(
        body, [Field(name="Content-Length", values=[str(size)])], server.port
    )

    tracemalloc.start()
    try:
        with Urllib3HTTPClient() as client:
            read_streaming_blob(client.send(request).body)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert server.bodies == [(size, body.digest.hexdigest())]
    assert peak < size // 8


class _FailingReader(_GeneratedReader):
    """Raises after ``fail_after`` bytes, as a payload that ends early does."""

    def __init__(self, size: int, fail_after: int) -> None:
        super().__init__(size)
        self._fail_after = fail_after

    def read(self, size: int = -1) -> bytes:
        if self._fail_after <= 0:
            raise ValueError("the payload ended early")
        data = super().read(min(size, self._fail_after))
        self._fail_after -= len(data)
        return data


def test_request_body_errors_raise_and_leave_the_client_usable(
    server: LocalHTTPServer,
) -> None:
    size = 4 * 1024 * 1024
    length = [Field(name="Content-Length", values=[str(size)])]

    with Urllib3HTTPClient() as client:
        with pytest.raises(ValueError, match="ended early"):
            client.send(_upload(_FailingReader(size, size // 2), length, server.port))

        body = _GeneratedReader(size)
        read_streaming_blob(client.send(_upload(body, length, server.port)).body)

    assert server.bodies[-1] == (size, body.digest.hexdigest())
