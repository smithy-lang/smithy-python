# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol, Self, TypeVar

from ..deserializers import DeserializeableShape
from ..serializers import SerializeableShape

__all__ = ["EventPublisher", "EventReceiver"]

_IE_contra = TypeVar("_IE_contra", bound=SerializeableShape, contravariant=True)
_OE_co = TypeVar("_OE_co", bound=DeserializeableShape, covariant=True)


class EventPublisher(Protocol[_IE_contra]):
    """Sends events to a service.

    This may be used as a context manager to ensure the stream is closed before exiting.
    """

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def send(self, event: _IE_contra) -> None:
        """Sends an event to the service.

        :param event: The event to send.
        """
        ...

    def close(self) -> None:
        """Closes the event stream."""
        ...


class EventReceiver(Protocol[_OE_co]):
    """Receives events from a service.

    Events may be received via the ``receive`` method or by using this class as an
    iterable. This may also be used as a context manager to ensure the stream is closed
    before exiting.
    """

    def __next__(self) -> _OE_co:
        result = self.receive()
        if result is None:
            self.close()
            raise StopIteration
        return result

    def __iter__(self) -> Self:
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def receive(self) -> _OE_co | None:
        """Receive a single event from the service.

        :returns: An event or None. None indicates that no more events will be sent by
            the service.
        """
        ...

    def close(self) -> None:
        """Closes the event stream."""
        ...
