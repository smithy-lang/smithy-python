# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol, Self

from ...deserializers import DeserializeableShape
from ...serializers import SerializeableShape


class EventPublisher[E: SerializeableShape](Protocol):
    """Asynchronously sends events to a service.

    This may be used as a context manager to ensure the stream is closed before exiting.
    """

    async def send(self, event: E) -> None:
        """Sends an event to the service.

        :param event: The event to send.
        """
        ...

    async def close(self) -> None:
        """Closes the event stream."""
        ...

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()


class EventReceiver[E: DeserializeableShape](Protocol):
    """Asynchronously receives events from a service.

    Events may be received via the ``receive`` method or by using this class as
    an async iterable.

    This may also be used as a context manager to ensure the stream is closed before
    exiting.
    """

    async def receive(self) -> E | None:
        """Receive a single event from the service.

        :returns: An event or None. None indicates that no more events will be sent by
            the service.
        """
        ...

    async def close(self) -> None:
        """Closes the event stream."""
        ...

    async def __anext__(self) -> E:
        result = await self.receive()
        if result is None:
            await self.close()
            raise StopAsyncIteration
        return result

    def __aiter__(self) -> Self:
        return self

    async def __enter__(self) -> Self:
        return self

    async def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()
