# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Protocol, Self, Any


class InputEventStream[E](Protocol):
    """Asynchronously sends events to a service."""

    async def send(self, event: E) -> None:
        """Sends an event to the service.
        
        :param event: The event to send.
        """
        ...

    def close(self) -> None:
        """Closes the event stream."""
        ...

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        self.close()


class OutputEventStream[E](Protocol):
    """Asynchronously receives events from a service."""

    async def receive(self) -> E | None:
        """Receive a single event from the service.
        
        :returns: An event or None. None indicates that no more events will be sent by
            the service.
        """
        ...

    def close(self) -> None:
        """Closes the event stream."""
        ...

    async def __anext__(self) -> E:
        result = await self.receive()
        if result is None:
            self.close()
            raise StopAsyncIteration
        return result

    def __aiter__(self) -> Self:
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        self.close()


class EventStream[I: InputEventStream[Any] | None, O: OutputEventStream[Any] | None, R](Protocol):
    """A unidirectional or bidirectional event stream."""

    input_stream: I
    _output_stream: O | None = None
    _response: R | None = None

    async def await_output(self) -> tuple[R, O]:
        if self._response is not None:
            self._response, self._output_stream = await self._await_output()

        return self._response, self._output_stream  # type: ignore


    async def _await_output(self) -> tuple[R, O]: ...

    async def close(self) -> None:
        if self._output_stream is None:
            _, self._output_stream = await self.await_output()

        if self._output_stream is not None:
            self._output_stream.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()
