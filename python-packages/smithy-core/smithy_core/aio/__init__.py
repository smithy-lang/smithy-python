# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncIterable
from typing import Protocol

from ..interfaces import URI


class Request(Protocol):
    """Protocol-agnostic representation of a request."""

    destination: URI
    body: AsyncIterable[bytes]

    async def consume_body(self) -> bytes:
        """Iterate over request body and return as bytes."""
        ...


class Response(Protocol):
    """Protocol-agnostic representation of a response."""

    @property
    def body(self) -> AsyncIterable[bytes]:
        """The response payload as iterable of chunks of bytes."""
        ...

    async def consume_body(self) -> bytes:
        """Iterate over response body and return as bytes."""
        ...
