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
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterable,
    Iterable,
    Protocol,
    Sequence,
    TypeVar,
)

T = TypeVar("T", covariant=True)


class Sliceable(Protocol[T]):
    def __getitem__(self, index: slice) -> T:
        ...

    def __len__(self) -> int:
        ...

    def __iter__(self) -> Iterable[T]:
        ...


_ListEl = TypeVar("_ListEl", bound=Sliceable[Any])


async def aenumerate(
    aiterable: AsyncIterable[_ListEl], start: int | None = None
) -> AsyncGenerator[tuple[int, _ListEl], None]:
    """An async version of enumerate."""
    if start is None:
        idx = 0
    else:
        idx = start
    async for x in aiterable:
        yield idx, x
        idx += 1


class AsyncList(AsyncIterable[_ListEl]):
    """An AsyncIterable constructed from a list."""

    def __init__(self, lst: Iterable[_ListEl]) -> None:
        self._generator = (x for x in lst)

    def __aiter__(self) -> AsyncGenerator[_ListEl, None]:
        return self._async_generator()

    async def __anext__(self) -> _ListEl:
        return await anext(self)

    async def _async_generator(self) -> AsyncGenerator[_ListEl, None]:
        for value in self._generator:
            await sleep(0)
            yield value


class RewindableAsyncIterable(AsyncIterable[_ListEl]):
    def __init__(self, lst: Sequence[_ListEl]) -> None:
        self._lst = lst
        self._position = 0
        self._chunk_offset = 0
        self._tell = 0

    def __aiter__(self) -> AsyncGenerator[_ListEl, None]:
        return self._async_generator()

    async def __anext__(self) -> _ListEl:
        try:
            value = self._lst[self._position]
        except IndexError:
            raise StopAsyncIteration()
        else:
            self._position += 1
            self._tell += len(value)
            return value

    async def _async_generator(self) -> AsyncGenerator[_ListEl, None]:
        for i, value in enumerate(self._lst[self._position :]):
            if i == 0:
                value = value[self._chunk_offset :]
            await sleep(0)
            yield value

    async def seek(self, offset: int) -> None:
        if offset < 0:
            raise ValueError("Cannot seek to a negative offset.")

        if offset == self.tell():
            return

        self._reset()
        total_offset = 0
        async for i, chunk in aenumerate(self):
            chunk_size = len(chunk)
            if total_offset + chunk_size >= offset:
                self._position = i
                self._chunk_offset = offset - total_offset
                self._tell = offset
                return
            total_offset += chunk_size

        raise ValueError("Offset is greater than the length of the iterable.")

    def tell(self) -> int:
        return self._tell

    def _reset(self) -> None:
        self._tell = 0
        self._chunk_offset = 0
        self._position = 0
