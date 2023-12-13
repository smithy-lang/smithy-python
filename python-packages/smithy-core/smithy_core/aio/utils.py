#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from asyncio import sleep
from collections.abc import AsyncIterable, Iterable
from typing import TypeVar

_ListEl = TypeVar("_ListEl")


async def async_list(lst: Iterable[_ListEl]) -> AsyncIterable[_ListEl]:
    """Turn an Iterable into an AsyncIterable."""
    for x in lst:
        await sleep(0)
        yield x
