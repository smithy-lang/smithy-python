#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from asyncio import iscoroutine, sleep
from collections.abc import AsyncIterable, Iterable
from inspect import isawaitable
from typing import Any

from .._pipeline import _seek  # pyright: ignore[reportPrivateUsage]
from ..utils import read_streaming_blob
from .interfaces import AsyncByteStream, StreamingBlob

__all__ = [
    "close_async",
    "list_async",
    "read_streaming_blob",
    "read_streaming_blob_async",
    "seek_async",
]


async def list_async[E](lst: Iterable[E]) -> AsyncIterable[E]:
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
            # runtime_checkable can't tell sync readers apart, and a sync read may
            # return an awaitable.
            data: Any = body.read()
            if isawaitable(data):
                data = await data
            return bytes(data)
        case AsyncIterable():
            full = b""
            async for chunk in body:
                full += chunk
            return full
        case _:
            return read_streaming_blob(body)


async def close_async(stream: Any) -> None:
    """Close a stream, awaiting it if it's async."""
    if (close := getattr(stream, "close", None)) is not None:
        if iscoroutine(result := close()):
            await result


async def seek_async(stream: Any, offset: int, whence: int = 0) -> int | None:
    """Seek a stream to a specified point."""
    result = _seek(stream, offset, whence)
    if iscoroutine(result):
        return await result
    return result
