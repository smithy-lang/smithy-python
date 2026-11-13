#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
#  pyright: reportPrivateUsage=false
from collections.abc import AsyncIterator
from io import BytesIO
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import smithy_http.aio.aiohttp
from smithy_core import URI
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.aio.utils import read_streaming_blob_async
from smithy_core.exceptions import MissingDependencyError
from smithy_http import Field, Fields, HTTPRequest
from smithy_http.aio.aiohttp import AIOHTTPClient, _AIOHTTPStreamingBody
from smithy_http.exceptions import SmithyHTTPError

from .._local_server import LocalHTTPServer, Reply


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


def test_missing_aiohttp_recommends_installing_the_extra(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(smithy_http.aio.aiohttp, "HAS_AIOHTTP", False)

    with pytest.raises(MissingDependencyError) as error:
        AIOHTTPClient()

    message = str(error.value)
    assert 'Install the optional dependency "smithy-http[aiohttp]".' in message


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

    data = session.request.call_args.kwargs["data"]
    assert data is not None
    assert [chunk async for chunk in data] == []


async def test_send_reads_bodies_in_large_chunks() -> None:
    # AsyncBytesReader iterates in 1 KiB chunks by default, which made uploads
    # about 25x slower than larger chunks.
    client, session = _create_client()
    size = 300 * 1024
    request = HTTPRequest(
        method="PUT",
        destination=URI(scheme="https", host="example.com", path="/"),
        body=BytesIO(b"x" * size),
        fields=Fields([Field(name="content-length", values=[str(size)])]),
    )

    await client.send(request)

    chunks = [chunk async for chunk in session.request.call_args.kwargs["data"]]
    assert [len(chunk) for chunk in chunks] == [128 * 1024, 128 * 1024, 44 * 1024]


async def test_send_passes_async_iterables_through() -> None:
    # Re-chunking would hold back each item until a full chunk had arrived.
    client, session = _create_client()

    async def chunks() -> AsyncIterator[bytes]:
        yield b"a" * 10
        yield b"b" * 10

    body = chunks()
    request = HTTPRequest(
        method="PUT",
        destination=URI(scheme="https", host="example.com", path="/"),
        body=body,
        fields=Fields([Field(name="content-length", values=["20"])]),
    )

    await client.send(request)

    assert session.request.call_args.kwargs["data"] is body


async def test_send_disables_redirects() -> None:
    client, session = _create_client()

    await client.send(_create_request())

    assert session.request.call_args.kwargs["allow_redirects"] is False


async def test_trailer_fields_are_not_sent_as_headers() -> None:
    client, session = _create_client()
    request = _create_request()
    request.fields.set_field(Field(name="x-amz-meta-a", values=["1"]))
    request.fields.set_field(
        Field(name="x-amz-checksum-crc32", values=["AAAAAA=="], kind="trailer")
    )

    await client.send(request)

    assert session.request.call_args.kwargs["headers"] == [("x-amz-meta-a", "1")]


async def test_chunked_transfer_encoding_is_requested_with_the_flag() -> None:
    # aiohttp raises ValueError if the header is passed along with chunked=True,
    # and only chunks a body when asked with the flag.
    client, session = _create_client()
    request = _create_request()
    request.method = "PUT"
    request.fields.set_field(Field(name="Transfer-Encoding", values=["chunked"]))
    request.fields.set_field(Field(name="x-amz-meta-a", values=["1"]))

    await client.send(request)

    kwargs = session.request.call_args.kwargs
    assert kwargs["chunked"] is True
    assert kwargs["headers"] == [("x-amz-meta-a", "1")]


async def test_requests_without_chunked_transfer_encoding_leave_framing_to_aiohttp() -> (
    None
):
    client, session = _create_client()

    await client.send(_create_request())

    assert session.request.call_args.kwargs["chunked"] is None


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

    assert await read_streaming_blob_async(response.body) == b'{"message":"hello"}'
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


async def test_closing_a_read_body_keeps_its_connection() -> None:
    # The client closes the bodies of failed attempts, which it has usually read
    # already, so that close must leave the connection reusable.
    with LocalHTTPServer() as server:
        server.replies = [Reply(status=503, body=b"busy"), Reply(body=b"ok")]
        request = HTTPRequest(
            destination=URI(scheme="http", host="127.0.0.1", port=server.port),
            method="GET",
            fields=Fields(),
        )
        async with AIOHTTPClient() as client:
            failed = await client.send(request)
            assert await read_streaming_blob_async(failed.body) == b"busy"
            await cast(Any, failed.body).close()

            succeeded = await client.send(request)
            assert await read_streaming_blob_async(succeeded.body) == b"ok"

        assert server.ports[0] == server.ports[1]
