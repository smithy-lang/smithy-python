#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
#  pyright: reportPrivateUsage=false
from collections.abc import AsyncIterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from smithy_core import URI
from smithy_core.aio.types import AsyncBytesReader
from smithy_http import Field, Fields
from smithy_http.aio import HTTPRequest
from smithy_http.aio.aiohttp import AIOHTTPClient, _AIOHTTPStreamingBody
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


async def test_send_disables_redirects() -> None:
    client, session = _create_client()

    await client.send(_create_request())

    assert session.request.call_args.kwargs["allow_redirects"] is False


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
