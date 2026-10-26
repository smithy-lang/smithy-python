#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
#  pyright: reportPrivateUsage=false
import gzip
from asyncio import CancelledError
from collections.abc import AsyncIterator
from hashlib import sha256
from io import BytesIO
from typing import Any, Self, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from smithy_core import URI
from smithy_core.aio.types import AsyncBytesReader
from smithy_http import Field, Fields
from smithy_http.aio import HTTPRequest
from smithy_http.aio.aiohttp import AIOHTTPClient, _AIOHTTPStreamingBody
from smithy_http.compression import RequestCompression
from smithy_http.exceptions import SmithyHTTPError


def _create_client() -> tuple[AIOHTTPClient, MagicMock]:
    response = MagicMock(status=200, headers={}, reason="OK")
    response.read = AsyncMock(return_value=b"")

    session = MagicMock()
    session.close = AsyncMock()
    session.request = AsyncMock(return_value=response)
    return AIOHTTPClient(_session=cast(Any, session)), session


def _create_request() -> HTTPRequest:
    return HTTPRequest(
        method="GET",
        destination=URI(scheme="https", host="example.com", path="/"),
        body=AsyncBytesReader(b""),
        fields=Fields(),
    )


async def test_close_closes_session() -> None:
    client, session = _create_client()

    await client.close()
    await client.close()

    session.close.assert_awaited_once()


async def test_send_after_close_raises() -> None:
    client, _ = _create_client()
    await client.close()

    with pytest.raises(SmithyHTTPError, match="has been closed"):
        await client.send(MagicMock())


async def test_context_manager_closes_session() -> None:
    client, session = _create_client()

    async with client as entered:
        assert entered is client

    session.close.assert_awaited_once()

    with pytest.raises(SmithyHTTPError, match="has been closed"):
        async with client:
            pass


async def test_send_omits_empty_async_reader_body() -> None:
    client, session = _create_client()

    await client.send(_create_request())

    assert session.request.call_args.kwargs["data"] is None


async def test_send_preserves_explicitly_framed_empty_body() -> None:
    client, session = _create_client()
    body = AsyncBytesReader(b"")
    request = HTTPRequest(
        method="GET",
        destination=URI(scheme="https", host="example.com", path="/"),
        body=body,
        fields=Fields([Field(name="content-length", values=["0"])]),
    )

    await client.send(request)

    assert session.request.call_args.kwargs["data"] is body


@pytest.mark.parametrize("position", [0, 17])
async def test_send_prepares_compressed_seekable_body_with_bounded_reads(
    position: int,
) -> None:
    class CountingSource(BytesIO):
        bytes_read = 0

        def read(self, size: int | None = -1) -> bytes:
            data = super().read(size)
            self.bytes_read += len(data)
            return data

    payload = b"".join(
        sha256(index.to_bytes(4, "big")).digest() for index in range(32768)
    )
    source = CountingSource(payload)
    fields = Fields()
    body = RequestCompression(encoding="gzip", minimum_size=0).compress(
        source, fields, streaming=True
    )
    assert isinstance(body, AsyncBytesReader)
    await body.seek(position)
    source.bytes_read = 0
    client, session = _create_client()
    request = HTTPRequest(
        method="POST",
        destination=URI(scheme="https", host="example.com"),
        body=body,
        fields=fields,
    )

    await client.send(request)

    assert source.bytes_read <= 128 * 1024
    assert session.request.call_args.kwargs["data"] is body
    assert body.tell() == position
    await body.seek(0)
    assert gzip.decompress(await body.read()) == payload
    await body.close()
    await client.close()


async def test_send_omits_body_at_nonzero_end_position() -> None:
    client, session = _create_client()
    body = AsyncBytesReader(b"prefix")
    await body.seek(6)
    request = _create_request()
    request.body = body
    await client.send(request)
    assert session.request.call_args.kwargs["data"] is None
    assert body.tell() == 6
    await body.close()
    await client.close()


@pytest.mark.parametrize("error", [OSError, CancelledError])
async def test_send_restores_position_when_body_probe_fails(
    error: type[BaseException],
) -> None:
    class FailingProbeReader(AsyncBytesReader):
        async def read(self, size: int = -1) -> bytes:
            await super().read(size)
            raise error("probe failed")

    client, session = _create_client()
    body = FailingProbeReader(b"payload")
    await body.seek(2)
    request = _create_request()
    request.body = body
    with pytest.raises(error, match="probe failed"):
        await client.send(request)
    assert body.tell() == 2
    session.request.assert_not_awaited()
    await body.close()
    await client.close()


@pytest.mark.parametrize("error", [OSError, CancelledError])
async def test_send_rewinds_gzip_source_after_probe_consumes_then_fails(
    error: type[BaseException],
) -> None:
    class FailOnceSource(BytesIO):
        failed = False

        def read(self, size: int | None = -1) -> bytes:
            if not self.failed:
                self.failed = True
                super().read(1)
                raise error("source probe failed")
            return super().read(size)

    payload = b"complete gzip source after retry"
    source = FailOnceSource(b"prefix" + payload)
    source.seek(6)
    fields = Fields()
    body = RequestCompression(encoding="gzip", minimum_size=0).compress(
        source, fields, streaming=True
    )
    assert isinstance(body, AsyncBytesReader)
    client, session = _create_client()
    request = HTTPRequest(
        method="POST",
        destination=URI(scheme="https", host="example.com"),
        body=body,
        fields=fields,
    )
    with pytest.raises(error, match="source probe failed"):
        await client.send(request)
    session.request.assert_not_awaited()
    assert source.tell() == 6
    assert body.tell() == 0
    assert gzip.decompress(await body.read()) == payload
    await body.close()
    await client.close()


@pytest.mark.parametrize("compressed", [False, True])
async def test_send_preserves_seekable_async_iterable_payload(compressed: bool) -> None:
    class SeekableChunks:
        def __init__(self, payload: bytes) -> None:
            self.source = BytesIO(payload)

        def __aiter__(self) -> Self:
            return self

        async def __anext__(self) -> bytes:
            chunk = self.source.read()
            if not chunk:
                raise StopAsyncIteration
            return chunk

        async def seek(self, offset: int, whence: int = 0) -> int:
            return self.source.seek(offset, whence)

        def tell(self) -> int:
            return self.source.tell()

        async def close(self) -> None:
            self.source.close()

    payload = b"".join(
        sha256(index.to_bytes(4, "big")).digest() for index in range(8192)
    )
    source = SeekableChunks(payload)
    fields = Fields()
    body = (
        RequestCompression(encoding="gzip", minimum_size=0).compress(
            source, fields, streaming=True
        )
        if compressed
        else AsyncBytesReader(source)
    )
    assert isinstance(body, AsyncBytesReader)
    client, session = _create_client()
    request = HTTPRequest(
        method="POST",
        destination=URI(scheme="https", host="example.com"),
        body=body,
        fields=fields,
    )
    await client.send(request)
    assert session.request.call_args.kwargs["data"] is body
    wire = await body.read()
    actual = gzip.decompress(wire) if compressed else wire
    assert actual == payload
    await body.seek(0)
    replay = await body.read()
    assert replay == wire
    await body.close()
    await client.close()


async def test_send_disables_redirects() -> None:
    client, session = _create_client()

    await client.send(_create_request())

    assert session.request.call_args.kwargs["allow_redirects"] is False


async def test_send_skips_automatic_content_type() -> None:
    client, session = _create_client()

    await client.send(_create_request())

    assert session.request.call_args.kwargs["skip_auto_headers"] == {"Content-Type"}


@pytest.mark.parametrize(
    "query",
    [
        "",
        "sync",
        "key=",
        "a=1&a=2",
        "sync&filter=a%2Fb&q=hello%20world&plus=a%2Bb",
    ],
)
async def test_send_preserves_encoded_query_string(query: str) -> None:
    client, session = _create_client()
    request = HTTPRequest(
        method="POST",
        destination=URI(scheme="https", host="example.com", path="/p", query=query),
        body=AsyncBytesReader(b""),
        fields=Fields(),
    )

    await client.send(request)

    url = session.request.call_args.kwargs["url"]
    assert url.raw_path_qs == (f"/p?{query}" if query else "/p")
    assert "params" not in session.request.call_args.kwargs


async def test_send_streams_response_body_and_releases_it_on_close() -> None:
    async def chunks() -> AsyncIterator[bytes]:
        yield b"first"
        yield b"second"

    client, session = _create_client()
    aiohttp_response = session.request.return_value
    aiohttp_response.content.iter_any.return_value = chunks()

    response = await client.send(_create_request())

    aiohttp_response.read.assert_not_awaited()
    aiohttp_response.content.iter_any.assert_not_called()
    assert isinstance(response.body, _AIOHTTPStreamingBody)
    assert [chunk async for chunk in response.body] == [
        b"first",
        b"second",
    ]
    aiohttp_response.content.iter_any.assert_called_once_with()
    aiohttp_response.release.assert_not_called()

    await response.body.close()
    aiohttp_response.release.assert_called_once_with()


async def test_non_streaming_response_body_can_be_consumed() -> None:
    async def chunks() -> AsyncIterator[bytes]:
        yield b'{"message":'
        yield b'"hello"}'

    client, session = _create_client()
    aiohttp_response = session.request.return_value
    aiohttp_response.content.iter_any.return_value = chunks()

    response = await client.send(_create_request())

    assert await response.consume_body_async() == b'{"message":"hello"}'
    aiohttp_response.content.iter_any.assert_called_once_with()


async def test_response_body_close_releases_partially_consumed_response() -> None:
    async def chunks() -> AsyncIterator[bytes]:
        yield b"first"
        yield b"second"

    client, session = _create_client()
    aiohttp_response = session.request.return_value
    aiohttp_response.content.iter_any.return_value = chunks()

    response = await client.send(_create_request())
    assert isinstance(response.body, _AIOHTTPStreamingBody)
    body_iterator = aiter(response.body)
    assert await anext(body_iterator) == b"first"

    await response.body.close()

    aiohttp_response.release.assert_called_once_with()


async def test_send_releases_response_when_marshaling_fails() -> None:
    client, session = _create_client()
    aiohttp_response = session.request.return_value

    with (
        patch.object(
            client, "_marshal_response", side_effect=ValueError("invalid response")
        ),
        pytest.raises(ValueError, match="invalid response"),
    ):
        await client.send(_create_request())

    aiohttp_response.release.assert_called_once_with()


async def test_prepare_body_preserves_nonempty_reader_position() -> None:
    client, _ = _create_client()
    body = AsyncBytesReader(b"request body")
    assert await body.read(4) == b"requ"

    prepared = await client._prepare_body(body)

    assert prepared is body
    assert await body.read() == b"est body"


async def test_prepare_body_does_not_consume_nonseekable_body() -> None:
    started = False

    async def body() -> AsyncIterator[bytes]:
        nonlocal started
        started = True
        yield b"request body"

    client, _ = _create_client()
    request_body = body()

    prepared = await client._prepare_body(request_body)

    assert started is False
    assert prepared is not None
    assert await prepared.read() == b"request body"


def test_does_not_support_duplex_streaming() -> None:
    assert AIOHTTPClient.SUPPORTS_DUPLEX_STREAMING is False
