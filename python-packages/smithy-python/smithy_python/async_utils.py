# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from asyncio import sleep
from collections.abc import AsyncGenerator, AsyncIterable, Iterable
from typing import TypeVar

_ListEl = TypeVar("_ListEl")


async def async_list(lst: Iterable[_ListEl]) -> AsyncIterable[_ListEl]:
    """Turn an Iterable into an AsyncIterable."""
    for x in lst:
        await sleep(0)
        yield x


class SeekableAsyncIterable(AsyncIterable[bytes]):
    """An AsyncIterable constructed from a list of bytes that can be moved forward or
    backward to a specific offset."""

    def __init__(self, values: list[bytes]) -> None:
        self._values = values
        self._position: int = 0
        self._chunk_offset: int = 0
        self._tell: int = 0

    def __aiter__(self) -> AsyncGenerator[bytes, None]:
        return self._async_generator()

    async def __anext__(self) -> bytes:
        try:
            value = self._values[self._position]
        except IndexError:
            raise StopAsyncIteration()
        else:
            self._move_pos(len(value))
            return value

    async def _async_generator(self) -> AsyncGenerator[bytes, None]:
        for i, value in enumerate(self._values[self._position :]):
            if i == 0:
                value = value[self._chunk_offset :]
            await sleep(0)
            yield value
            self._move_pos(len(value))

    def _move_pos(self, offset: int) -> None:
        self._tell += offset
        self._position += 1

    async def seek(self, offset: int, whence: int = 0) -> None:
        """Seek to a specific offset in the iterable.

        :param offset: The offset to seek to.
        :param whence: The reference point to seek from in the stream. 0 will seek
        from the beginning, 1 will seek from the current position, and 2 will seek
        from the end.
        """
        if whence == 0 and offset < 0:
            raise ValueError(
                "Cannot seek to a negative offset when seeking from the beginning "
                "of the stream."
            )

        if offset == self.tell():
            return
        # TODO: Support seeking from the current position and end of the stream.
        # AKA whence = 1 or 2.

        self._reset()
        total_offset = 0
        async for chunk in self:
            chunk_size = len(chunk)
            if total_offset + chunk_size > offset:
                self._offset_chunk(offset - total_offset)
                return
            total_offset += chunk_size

        # Ensure that tell is set to the provided offset rather than the position
        # at the end of the stream.
        self._tell = offset

    def _reset(self) -> None:
        self._tell = 0
        self._chunk_offset = 0
        self._position = 0

    def tell(self) -> int:
        """Return the current offset."""
        return self._tell

    async def read(self, size: int = -1) -> bytes:
        """Read a chunk of bytes from the iterable.

        :param size: The number of bytes to read. If less than zero,
        read the entire remaining contents of the iterable.
        """
        data = b""
        if size < 0:
            async for chunk in self:
                data += chunk
        elif size > 0:
            total_size = 0
            async for chunk in self:
                chunk_size = len(chunk)
                if total_size + chunk_size > size:
                    data += chunk[: size - total_size]
                    self._offset_chunk(size - total_size)
                    break
                total_size += chunk_size
                data += chunk
        return data

    def _offset_chunk(self, offset: int) -> None:
        self._chunk_offset = offset
        self._tell += self._chunk_offset
