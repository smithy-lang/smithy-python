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
from collections.abc import AsyncIterable, Iterable
from typing import TypeVar

_ListEl = TypeVar("_ListEl")


async def async_list(lst: Iterable[_ListEl]) -> AsyncIterable[_ListEl]:
    """Turn an Iterable into an AsyncIterable."""
    for x in lst:
        await sleep(0)
        yield x
