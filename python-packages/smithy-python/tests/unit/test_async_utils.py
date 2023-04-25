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
import pytest

from smithy_python.async_utils import SeekableAsyncIterable


@pytest.fixture(scope="function")
def seekable_async_iterable() -> SeekableAsyncIterable:
    return SeekableAsyncIterable([b"a" * 10, b"b" * 10, b"c" * 10])


@pytest.mark.asyncio
async def test_seekable_async_iterable_stop_iteration(
    seekable_async_iterable: SeekableAsyncIterable,
) -> None:
    with pytest.raises(StopAsyncIteration):
        while True:
            await anext(seekable_async_iterable)


@pytest.mark.asyncio
async def test_seekable_async_iterable_anext(
    seekable_async_iterable: SeekableAsyncIterable,
) -> None:
    assert await anext(seekable_async_iterable) == b"a" * 10
    assert seekable_async_iterable.tell() == 10
    assert await anext(seekable_async_iterable) == b"b" * 10
    assert seekable_async_iterable.tell() == 20
    assert await anext(seekable_async_iterable) == b"c" * 10
    assert seekable_async_iterable.tell() == 30


@pytest.mark.parametrize(
    "offset, expected_result",
    [
        (0, b"a" * 10 + b"b" * 10 + b"c" * 10),
        (5, b"a" * 5 + b"b" * 10 + b"c" * 10),
        (10, b"b" * 10 + b"c" * 10),
        (11, b"b" * 9 + b"c" * 10),
        (20, b"c" * 10),
        (29, b"c"),
        (50, b""),
    ],
)
@pytest.mark.asyncio
async def test_seek(
    seekable_async_iterable: SeekableAsyncIterable,
    offset: int,
    expected_result: bytes,
) -> None:
    await seekable_async_iterable.seek(offset)
    assert seekable_async_iterable.tell() == offset
    assert await seekable_async_iterable.read() == expected_result


@pytest.mark.asyncio
async def test_negative_seek_raises(
    seekable_async_iterable: SeekableAsyncIterable,
) -> None:
    with pytest.raises(ValueError):
        await seekable_async_iterable.seek(-1)


@pytest.mark.parametrize(
    "size, expected_result",
    [(0, b""), (5, b"a" * 5), (10, b"a" * 10), (-1, b"a" * 10 + b"b" * 10 + b"c" * 10)],
)
@pytest.mark.asyncio
async def test_read(
    seekable_async_iterable: SeekableAsyncIterable, size: int, expected_result: bytes
) -> None:
    assert await seekable_async_iterable.read(size) == expected_result
