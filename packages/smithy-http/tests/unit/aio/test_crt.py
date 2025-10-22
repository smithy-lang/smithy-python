#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
#  pyright: reportPrivateUsage=false
import asyncio
from collections.abc import AsyncIterator
from copy import deepcopy
from io import BytesIO
from unittest.mock import AsyncMock, Mock, patch

import pytest
from awscrt import http as crt_http  # type: ignore
from smithy_core import URI
from smithy_core.aio.types import AsyncBytesReader
from smithy_http import Field, Fields
from smithy_http.aio import HTTPRequest
from smithy_http.aio.crt import (
    AWSCRTHTTPClient,
    AWSCRTHTTPClientConfig,
    AWSCRTHTTPResponse,
)
from smithy_http.exceptions import SmithyHTTPError


def test_deepcopy_client() -> None:
    """Test that AWSCRTHTTPClient can be deep copied."""
    client = AWSCRTHTTPClient()
    deepcopy(client)


def test_client_marshal_request() -> None:
    """Test that HTTPRequest is correctly marshaled to CRT HttpRequest."""
    client = AWSCRTHTTPClient()
    request = HTTPRequest(
        method="GET",
        destination=URI(
            host="example.com", path="/path", query="key1=value1&key2=value2"
        ),
        body=BytesIO(),
        fields=Fields(),
    )
    crt_request = client._marshal_request(request)
    assert crt_request.headers.get("host") == "example.com"
    assert crt_request.headers.get("accept") == "*/*"
    assert crt_request.method == "GET"
    assert crt_request.path == "/path?key1=value1&key2=value2"


@pytest.mark.parametrize(
    "host,expected",
    [
        ("example.com", "example.com:8443"),
        ("2001:db8::1", "[2001:db8::1]:8443"),
    ],
)
async def test_port_included_in_host_header(host: str, expected: str) -> None:
    client = AWSCRTHTTPClient()
    request = HTTPRequest(
        method="GET",
        destination=URI(
            host=host, path="/path", query="key1=value1&key2=value2", port=8443
        ),
        body=BytesIO(),
        fields=Fields(),
    )
    crt_request = client._marshal_request(request)  # type: ignore
    assert crt_request.headers.get("host") == expected  # type: ignore


async def test_body_generator_bytes() -> None:
    """Test body generator with bytes input."""
    client = AWSCRTHTTPClient()
    body = b"Hello, World!"

    chunks: list[bytes] = []
    async for chunk in client._create_body_generator(body):
        chunks.append(chunk)

    assert chunks == [b"Hello, World!"]


async def test_body_generator_bytearray() -> None:
    """Test body generator with bytearray input (should convert to bytes)."""
    client = AWSCRTHTTPClient()
    body = bytearray(b"mutable data")

    chunks: list[bytes] = []
    async for chunk in client._create_body_generator(body):
        chunks.append(chunk)

    assert chunks == [b"mutable data"]
    assert all(isinstance(chunk, bytes) for chunk in chunks)


async def test_body_generator_bytesio() -> None:
    """Test body generator with BytesIO (sync reader)."""
    client = AWSCRTHTTPClient()
    body = BytesIO(b"data from BytesIO")

    chunks: list[bytes] = []
    async for chunk in client._create_body_generator(body):
        chunks.append(chunk)

    result = b"".join(chunks)
    assert result == b"data from BytesIO"


async def test_body_generator_async_bytes_reader() -> None:
    """Test body generator with AsyncBytesReader."""
    client = AWSCRTHTTPClient()
    body = AsyncBytesReader(b"async reader data")

    chunks: list[bytes] = []
    async for chunk in client._create_body_generator(body):
        chunks.append(chunk)

    result = b"".join(chunks)
    assert result == b"async reader data"


async def test_body_generator_async_iterable() -> None:
    """Test body generator with custom AsyncIterable."""

    async def custom_generator() -> AsyncIterator[bytes]:
        yield b"chunk1"
        yield b"chunk2"
        yield b"chunk3"

    client = AWSCRTHTTPClient()
    body = custom_generator()

    chunks: list[bytes] = []
    async for chunk in client._create_body_generator(body):
        chunks.append(chunk)

    assert chunks == [b"chunk1", b"chunk2", b"chunk3"]


async def test_body_generator_async_iterable_with_bytearray() -> None:
    """Test that AsyncIterable yielding bytearray converts to bytes."""

    async def generator_with_bytearray() -> AsyncIterator[bytes | bytearray]:
        yield b"bytes chunk"
        yield bytearray(b"bytearray chunk")
        yield b"more bytes"

    client = AWSCRTHTTPClient()
    body = generator_with_bytearray()

    chunks: list[bytes] = []
    async for chunk in client._create_body_generator(body):  # type: ignore
        chunks.append(chunk)

    assert chunks == [b"bytes chunk", b"bytearray chunk", b"more bytes"]
    assert all(isinstance(chunk, bytes) for chunk in chunks)


async def test_body_generator_async_byte_stream() -> None:
    """Test body generator with AsyncByteStream (object with async read)."""

    class CustomAsyncStream:
        def __init__(self, data: bytes):
            self._data = BytesIO(data)

        async def read(self, size: int = -1) -> bytes:
            # Simulate async read
            await asyncio.sleep(0)
            return self._data.read(size)

    client = AWSCRTHTTPClient()
    body = CustomAsyncStream(b"x" * 100000)  # 100KB of data

    chunks: list[bytes] = []
    async for chunk in client._create_body_generator(body):
        chunks.append(chunk)

    # Should read in 64KB chunks
    result = b"".join(chunks)
    assert len(result) == 100000
    assert result == b"x" * 100000


async def test_body_generator_empty_bytes() -> None:
    """Test body generator with empty bytes."""
    client = AWSCRTHTTPClient()
    body = b""

    chunks: list[bytes] = []
    async for chunk in client._create_body_generator(body):
        chunks.append(chunk)

    assert chunks == [b""]


async def test_build_connection_http() -> None:
    """Test building HTTP connection."""
    client = AWSCRTHTTPClient()
    url = URI(scheme="http", host="example.com", port=8080)

    with patch("smithy_http.aio.crt.AIOHttpClientConnectionUnified.new") as mock_new:
        mock_connection = AsyncMock()
        mock_connection.version = crt_http.HttpVersion.Http1_1
        mock_connection.is_open = Mock(return_value=True)
        mock_new.return_value = mock_connection

        connection = await client._build_new_connection(url)

        assert connection is mock_connection
        mock_new.assert_called_once()
        call_kwargs = mock_new.call_args[1]
        assert call_kwargs["host_name"] == "example.com"
        assert call_kwargs["port"] == 8080
        assert call_kwargs["tls_connection_options"] is None


async def test_build_connection_https() -> None:
    """Test building HTTPS connection with TLS."""
    client = AWSCRTHTTPClient()
    url = URI(scheme="https", host="secure.example.com")

    with patch("smithy_http.aio.crt.AIOHttpClientConnectionUnified.new") as mock_new:
        mock_connection = AsyncMock()
        mock_connection.version = crt_http.HttpVersion.Http2
        mock_connection.is_open = Mock(return_value=True)
        mock_new.return_value = mock_connection

        connection = await client._build_new_connection(url)

        assert connection is mock_connection
        mock_new.assert_called_once()
        call_kwargs = mock_new.call_args[1]
        assert call_kwargs["host_name"] == "secure.example.com"
        assert call_kwargs["port"] == 443
        assert call_kwargs["tls_connection_options"] is not None


async def test_build_connection_unsupported_scheme() -> None:
    """Test that unsupported URL schemes raise error."""
    client = AWSCRTHTTPClient()
    url = URI(scheme="ftp", host="example.com")

    with pytest.raises(SmithyHTTPError, match="does not support URL scheme ftp"):
        await client._build_new_connection(url)


async def test_validate_connection_http2_required() -> None:
    """Test connection validation when force_http_2 is enabled."""
    config = AWSCRTHTTPClientConfig(force_http_2=True)
    client = AWSCRTHTTPClient(client_config=config)

    # Mock HTTP/1.1 connection
    mock_connection = AsyncMock()
    mock_connection.version = crt_http.HttpVersion.Http1_1
    mock_connection.close = AsyncMock()

    with pytest.raises(SmithyHTTPError, match="HTTP/2 could not be negotiated"):
        await client._validate_connection(mock_connection)

    mock_connection.close.assert_called_once()


async def test_validate_connection_http2_success() -> None:
    """Test connection validation succeeds with HTTP/2."""
    config = AWSCRTHTTPClientConfig(force_http_2=True)
    client = AWSCRTHTTPClient(client_config=config)

    # Mock HTTP/2 connection
    mock_connection = AsyncMock()
    mock_connection.version = crt_http.HttpVersion.Http2

    # Should not raise
    await client._validate_connection(mock_connection)


async def test_connection_pooling() -> None:
    """Test that connections are pooled and reused."""
    client = AWSCRTHTTPClient()
    url = URI(scheme="https", host="example.com")

    # Mock connection
    mock_connection = AsyncMock()
    mock_connection.version = crt_http.HttpVersion.Http2
    # is_open() should be a regular method, not async
    mock_connection.is_open = Mock(return_value=True)

    with patch("smithy_http.aio.crt.AIOHttpClientConnectionUnified.new") as mock_new:
        mock_new.return_value = mock_connection

        # First call should create new connection
        conn1 = await client._get_connection(url)
        assert mock_new.call_count == 1

        # Second call should reuse connection
        conn2 = await client._get_connection(url)
        assert mock_new.call_count == 1  # Not called again
        assert conn1 is conn2


async def test_connection_pooling_different_hosts() -> None:
    """Test that different hosts get different connections."""
    client = AWSCRTHTTPClient()
    url1 = URI(scheme="https", host="example1.com")
    url2 = URI(scheme="https", host="example2.com")

    # Create two distinct mock connections
    mock_conn1 = AsyncMock()
    mock_conn1.version = crt_http.HttpVersion.Http2
    mock_conn1.is_open = Mock(return_value=True)

    mock_conn2 = AsyncMock()
    mock_conn2.version = crt_http.HttpVersion.Http2
    mock_conn2.is_open = Mock(return_value=True)

    with patch("smithy_http.aio.crt.AIOHttpClientConnectionUnified.new") as mock_new:
        mock_new.side_effect = [mock_conn1, mock_conn2]

        conn1 = await client._get_connection(url1)
        conn2 = await client._get_connection(url2)

        assert mock_new.call_count == 2
        assert conn1 is mock_conn1
        assert conn2 is mock_conn2
        assert conn1 is not conn2


async def test_connection_pooling_closed_connection() -> None:
    """Test that closed connections are replaced."""
    client = AWSCRTHTTPClient()
    url = URI(scheme="https", host="example.com")

    mock_connection1 = AsyncMock()
    mock_connection1.version = crt_http.HttpVersion.Http2
    mock_connection1.is_open = Mock(return_value=False)  # Closed

    mock_connection2 = AsyncMock()
    mock_connection2.version = crt_http.HttpVersion.Http2
    mock_connection2.is_open = Mock(return_value=True)

    with patch("smithy_http.aio.crt.AIOHttpClientConnectionUnified.new") as mock_new:
        mock_new.side_effect = [mock_connection1, mock_connection2]

        # First call
        conn1 = await client._get_connection(url)
        assert conn1 is mock_connection1

        # Connection is now closed, should create new one
        conn2 = await client._get_connection(url)
        assert conn2 is mock_connection2
        assert mock_new.call_count == 2


async def test_response_chunks() -> None:
    """Test reading response body chunks."""
    mock_stream = AsyncMock()
    mock_stream.get_next_response_chunk.side_effect = [
        b"chunk1",
        b"chunk2",
        b"chunk3",
        b"",  # End of stream
    ]

    response = AWSCRTHTTPResponse(status=200, fields=Fields(), stream=mock_stream)

    chunks: list[bytes] = []
    async for chunk in response.chunks():
        chunks.append(chunk)

    assert chunks == [b"chunk1", b"chunk2", b"chunk3"]


async def test_response_body_property() -> None:
    """Test that body property returns chunks."""
    mock_stream = AsyncMock()
    mock_stream.get_next_response_chunk.side_effect = [b"data", b""]

    response = AWSCRTHTTPResponse(status=200, fields=Fields(), stream=mock_stream)

    chunks: list[bytes] = []
    async for chunk in response.body:
        chunks.append(chunk)

    assert chunks == [b"data"]


def test_response_properties() -> None:
    """Test response property accessors."""
    fields = Fields()
    fields.set_field(Field(name="content-type", values=["application/json"]))

    mock_stream = Mock()
    response = AWSCRTHTTPResponse(status=404, fields=fields, stream=mock_stream)

    assert response.status == 404
    assert response.fields == fields
    assert response.reason is None
