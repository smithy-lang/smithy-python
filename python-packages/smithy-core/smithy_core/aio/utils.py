#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from asyncio import sleep
from collections.abc import AsyncIterable, Iterable
from typing import TypeVar

from ..exceptions import AsyncBodyException
from ..interfaces import ByteStream
from ..interfaces import StreamingBlob as SyncStreamingBlob
from .interfaces import AsyncByteStream, StreamingBlob

_ListEl = TypeVar("_ListEl")


async def async_list(lst: Iterable[_ListEl]) -> AsyncIterable[_ListEl]:
    """Turn an Iterable into an AsyncIterable."""
    for x in lst:
        await sleep(0)
        yield x


async def read_streaming_blob_async(body: StreamingBlob) -> bytes:
    """Asynchronously reads a streaming blob into bytes.

    :param body: The streaming blob to read from.
    """
    match body:
        case AsyncByteStream():
            return await body.read()
        case AsyncIterable():
            full = b""
            async for chunk in body:
                full += chunk
            return full
        case _:
            return read_streaming_blob(body)


def read_streaming_blob(body: StreamingBlob) -> bytes:
    """Synchronously reads a streaming blob into bytes.

    :param body: The streaming blob to read from.
    :raises AsyncBodyException: If the body is an async type.
    """
    match body:
        case bytes():
            return body
        case bytearray():
            return bytes(body)
        case ByteStream():
            return body.read()
        case _:
            raise AsyncBodyException(
                f"Expected type {SyncStreamingBlob}, but was {type(body)}"
            )
