#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
#  pyright: reportPrivateUsage=false
from collections.abc import AsyncIterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

from smithy_core import URI
from smithy_core.aio.types import AsyncBytesReader
from smithy_http import Field, Fields
from smithy_http.aio import HTTPRequest
from smithy_http.aio.aiohttp import AIOHTTPClient


def _create_client() -> tuple[AIOHTTPClient, MagicMock]:
    response = MagicMock(status=200, headers={}, reason="OK")
    response.read = AsyncMock(return_value=b"")

    session = MagicMock()
    session.request.return_value.__aenter__ = AsyncMock(return_value=response)
    session.request.return_value.__aexit__ = AsyncMock(return_value=None)
    return AIOHTTPClient(_session=cast(Any, session)), session


async def test_send_omits_empty_async_reader_body() -> None:
    client, session = _create_client()
    request = HTTPRequest(
        method="GET",
        destination=URI(scheme="https", host="example.com", path="/"),
        body=AsyncBytesReader(b""),
        fields=Fields(),
    )

    await client.send(request)

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
    request = HTTPRequest(
        method="GET",
        destination=URI(scheme="https", host="example.com", path="/"),
        body=AsyncBytesReader(b""),
        fields=Fields(),
    )

    await client.send(request)

    assert session.request.call_args.kwargs["allow_redirects"] is False


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
