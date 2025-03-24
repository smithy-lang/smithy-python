# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from asyncio import Future
from typing import Any, Self

from ..deserializers import DeserializeableShape
from ..serializers import SerializeableShape
from .interfaces.eventstream import EventPublisher, EventReceiver


class DuplexEventStream[
    IE: SerializeableShape,
    OE: DeserializeableShape,
    O: DeserializeableShape,
]:
    """An event stream that both sends and receives messages.

    To ensure that streams are closed upon exiting, this class may be used as an async
    context manager.

    .. code-block:: python

        async def main():
            client = ChatClient()
            input = StreamMessagesInput(chat_room="aws-python-sdk", username="hunter7")

            async with client.stream_messages(input=input) as stream:
                stream.input_stream.send(
                    MessageStreamMessage("Chat logger starting up.")
                )
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
                                MessageStreamMessage(
                                    "Unknown message type received. Shutting down."
                                )
                            )
                            return
    """

    input_stream: EventPublisher[IE]
    """An event stream that sends events to the service."""

    output_stream: EventReceiver[OE] | None = None
    """An event stream that receives events from the service.

    This value may be None until ``await_output`` has been called.

    This value will also be None if the operation has no output stream.
    """

    output: O | None = None
    """The initial response from the service.

    This value may be None until ``await_output`` has been called.

    This may include context necessary to interpret output events or prepare
    input events. It will always be available before any events.
    """

    def __init__(
        self,
        *,
        input_stream: EventPublisher[IE],
        output_future: Future[tuple[O, EventReceiver[OE]]],
    ) -> None:
        self.input_stream = input_stream
        self._output_future = output_future

    async def await_output(self) -> tuple[O, EventReceiver[OE]]:
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
        self.output, self.output_stream = await self._output_future
        return self.output, self.output_stream

    async def close(self) -> None:
        """Closes the event stream.

        This closes both the input and output streams.
        """
        if self.output_stream is None:
            _, self.output_stream = await self.await_output()

        await self.input_stream.close()
        await self.output_stream.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()


class InputEventStream[IE: SerializeableShape, O]:
    """An event stream that streams messages to the service.

    To ensure that streams are closed upon exiting, this class may be used as an async
    context manager.

    .. code-block:: python

        async def main():
            client = ChatClient()
            input = PublishMessagesInput(chat_room="aws-python-sdk", username="hunter7")

            async with client.publish_messages(input=input) as stream:
                stream.input_stream.send(
                    MessageStreamMessage("High severity ticket alert!")
                )
                await stream.await_output()
    """

    input_stream: EventPublisher[IE]
    """An event stream that sends events to the service."""

    output: O | None = None
    """The initial response from the service.

    This value may be None until ``await_output`` has been called.

    This may include context necessary to interpret output events or prepare
    input events. It will always be available before any events.
    """

    def __init__(
        self,
        *,
        input_stream: EventPublisher[IE],
        output_future: Future[O],
    ) -> None:
        self.input_stream = input_stream
        self._output_future = output_future

    async def await_output(self) -> O:
        """Await the operation's initial response.

        The EventStream will be returned as soon as the input stream is ready to receive
        events, which may be before the initial response has been received and the
        service is ready to send events.

        Awaiting this method will wait until the initial response was received.

        :returns: The service's initial response.
        """
        if self.output is None:
            self.output = await self._output_future
        return self.output

    async def close(self) -> None:
        """Closes the event stream."""
        await self.input_stream.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()


class OutputEventStream[OE: DeserializeableShape, O: DeserializeableShape]:
    """An event stream that streams messages from the service.

    To ensure that streams are closed upon exiting, this class may be used as an async
    context manager.

    .. code-block:: python

        async def main():
            client = ChatClient()
            input = ReceiveMessagesInput(chat_room="aws-python-sdk")

            async with client.receive_messages(input=input) as stream:
                async for event in stream.output_stream:
                    match event:
                        case MessageStreamMessage():
                            print(event.value)
                        case _:
                            return
    """

    output_stream: EventReceiver[OE]
    """An event stream that receives events from the service.

    This value will also be None if the operation has no output stream.
    """

    output: O
    """The initial response from the service.

    This may include context necessary to interpret output events or prepare input
    events. It will always be available before any events.
    """

    def __init__(self, output_stream: EventReceiver[OE], output: O) -> None:
        self.output_stream = output_stream
        self.output = output

    async def close(self) -> None:
        """Closes the event stream."""
        await self.output_stream.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        await self.close()
