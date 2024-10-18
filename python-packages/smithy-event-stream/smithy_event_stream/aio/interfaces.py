# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Protocol, Self

from smithy_core.deserializers import DeserializeableShape
from smithy_core.serializers import SerializeableShape


class InputEventStream[E: SerializeableShape](Protocol):
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


class OutputEventStream[E: DeserializeableShape](Protocol):
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


class EventStream[I: InputEventStream[Any] | None, O: OutputEventStream[Any] | None, R](
    Protocol
):
    """A unidirectional or bidirectional event stream.

    To ensure that streams are closed upon exiting, this class may be used as an async
    context manager.

    .. code-block:: python

        async def main():
            client = ChatClient()
            input = StreamMessagesInput(chat_room="aws-python-sdk", username="hunter7")

            async with client.stream_messages(input=input) as stream:
                stream.input_stream.send(MessageStreamMessage("Chat logger starting up."))
                response_task = asyncio.create_task(handle_output(stream))
                stream.input_stream.send(MessageStreamMessage("Chat logger active."))
                await response_handler

            async def handle_output(stream: EventStream) -> None:
                _, output_stream = await stream.await_output()
                async for event in output_stream:
                    match event:
                        case MessageStreamMessage():
                            print(event.value)
                        case MessageStreamShutdown():
                            return
                        case _:
                            stream.input_stream.send(
                                MessageStreamMessage("Unknown message type received. Shutting down.")
                            )
                            return
    """

    input_stream: I
    """An event stream that sends events to the service.

    This value will be None if the operation has no input stream.
    """

    output_stream: O | None = None
    """An event stream that receives events from the service.

    This value may be None until ``await_output`` has been called.

    This value will also be None if the operation has no output stream.
    """

    response: R | None = None
    """The initial response from the service.

    This value may be None until ``await_output`` has been called.

    This may include context necessary to interpret output events or prepare
    input events. It will always be available before any events.
    """

    async def await_output(self) -> tuple[R, O]:
        """Await the operation's output.

        The EventStream will be returned as soon as the input stream is ready to
        receive events, which may be before the initial response has been received
        and the service is ready to send events.

        Awaiting this method will wait until the initial response was received and the
        service is ready to send events. The initial response and output stream will
        be returned by this operation and also cached in ``response`` and
        ``output_stream``, respectively.

        The default implementation of this method performs the caching behavior,
        delegating to the abstract ``_await_output`` method to actually retrieve the
        initial response and output stream.

        :returns: A tuple containing the initial response and output stream. If the
            operation has no output stream, the second value will be None.
        """
        if self.response is not None:
            self.response, self.output_stream = await self._await_output()

        return self._response, self._output_stream  # type: ignore

    async def _await_output(self) -> tuple[R, O]:
        """Await the operation's output without caching.

        This method is meant to be used with the default implementation of await_output.
        It should return the output directly without caching.
        """
        ...

    async def close(self) -> None:
        """Closes the event stream.

        This closes both the input and output streams.
        """
        if self.output_stream is None:
            _, self.output_stream = await self.await_output()

        if self.output_stream is not None:
            await self.output_stream.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()
