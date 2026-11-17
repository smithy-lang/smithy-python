# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import sys
from typing import Any, Protocol, Self

from ...deserializers import DeserializeableShape
from ...serializers import SerializeableShape

if sys.version_info >= (3, 12):
    from typing import TypeVar
else:
    from typing_extensions import TypeVar


_IE = TypeVar("_IE", bound=SerializeableShape, infer_variance=True)
_OE = TypeVar("_OE", bound=DeserializeableShape, infer_variance=True)


class AsyncEventPublisher(Protocol[_IE]):
    """Asynchronously sends events to a service.

    This may be used as a context manager to ensure the stream is closed before exiting.
    """

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.close()

    async def send(self, event: _IE) -> None:
        """Sends an event to the service.

        :param event: The event to send.
        """
        ...

    async def close(self) -> None:
        """Closes the event stream."""
        ...


class AsyncEventReceiver(Protocol[_OE]):
    """Asynchronously receives events from a service.

    Events may be received via the ``receive`` method or by using this class as
    an async iterable.

    This may also be used as a context manager to ensure the stream is closed before
    exiting.
    """

    async def __anext__(self) -> _OE:
        result = await self.receive()
        if result is None:
            await self.close()
            raise StopAsyncIteration
        return result

    def __aiter__(self) -> Self:
        return self

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.close()

    async def receive(self) -> _OE | None:
        """Receive a single event from the service.

        :returns: An event or None. None indicates that no more events will be sent by
            the service.
        """
        ...

    async def close(self) -> None:
        """Closes the event stream."""
        ...
