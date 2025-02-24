# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import asyncio
from collections.abc import Callable
from typing import Self

from smithy_core.aio.interfaces import AsyncByteStream, AsyncWriter
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.serializers import SerializeableShape
from smithy_event_stream.aio.interfaces import (
    AsyncEventReceiver,
    DuplexEventStream,
    InputEventStream,
    OutputEventStream,
)

from .._private.deserializers import AWSAsyncEventReceiver as _AWSEventReceiver
from .._private.serializers import AWSAsyncEventPublisher as _AWSEventPublisher
from .._private.serializers import Signer
from ..exceptions import MissingInitialResponse


class AWSDuplexEventStream[
    I: SerializeableShape,
    O: DeserializeableShape,
    R: DeserializeableShape,
](DuplexEventStream[I, O, R]):
    """A duplex event stream using the application/vnd.amazon.eventstream format."""

    def __init__(
        self,
        payload_codec: Codec,
        async_writer: AsyncWriter,
        deserializer: Callable[[ShapeDeserializer], O],
        async_reader: AsyncByteStream | None = None,
        initial_response: R | None = None,
        deserializeable_response: type[R] | None = None,
        signer: Signer | None = None,
        is_client_mode: bool = True,
    ) -> None:
        """Construct an AWSDuplexEventStream.

        :param payload_codec: The codec to encode the event payload with.
        :param async_writer: The writer to write event bytes to.
        :param deserializer: A callable to deserialize events with. This should be the
            union's deserialize method.
        :param async_reader: The reader to read event bytes from, if available. If not
            immediately available, output will be blocked on it becoming available.
        :param initial_response: The deserialized operation response, if available. If
            not immediately available, output will be blocked on it becoming available.
        :param deserializeable_response: The deserializeable response class. Setting
            this indicates that the initial response is sent over the event stream. The
            deserialize method of this class will be used to deserialize it upon
            calling ``await_output``.
        :param signer: An optional callable to sign events with prior to them being
            encoded.
        :param is_client_mode: Whether the stream is being constructed for a client or
            server implementation.
        """
        self.input_stream = _AWSEventPublisher(
            payload_codec=payload_codec,
            async_writer=async_writer,
            signer=signer,
            is_client_mode=is_client_mode,
        )

        self._deserializer = deserializer
        self._payload_codec = payload_codec
        self._is_client_mode = is_client_mode

        # Create a future to allow awaiting the reader
        loop = asyncio.get_event_loop()
        self._reader_future: asyncio.Future[AsyncByteStream] = loop.create_future()
        if async_reader is not None:
            self._reader_future.set_result(async_reader)

        # Create a future to allow awaiting the initial response
        self._response = initial_response
        self._deserializerable_response = deserializeable_response
        self._response_future: asyncio.Future[R] = loop.create_future()

    @property
    def response(self) -> R | None:
        return self._response

    @response.setter
    def response(self, value: R) -> None:
        self._response_future.set_result(value)
        self._response = value

    def set_reader(self, value: AsyncByteStream) -> None:
        """Sets the object to read events from.

        :param value: An async readable object to read event bytes from.
        """
        self._reader_future.set_result(value)

    async def await_output(self) -> tuple[R, AsyncEventReceiver[O]]:
        async_reader = await self._reader_future
        if self.output_stream is None:
            self.output_stream = _AWSEventReceiver[O](
                payload_codec=self._payload_codec,
                source=async_reader,
                deserializer=self._deserializer,
                is_client_mode=self._is_client_mode,
            )

        if self.response is None:
            if self._deserializerable_response is None:
                initial_response = await self._response_future
            else:
                initial_response_stream = _AWSEventReceiver(
                    payload_codec=self._payload_codec,
                    source=async_reader,
                    deserializer=self._deserializerable_response.deserialize,
                    is_client_mode=self._is_client_mode,
                )
                initial_response = await initial_response_stream.receive()
                if initial_response is None:
                    raise MissingInitialResponse()
                self.response = initial_response
        else:
            initial_response = self.response

        return initial_response, self.output_stream


class AWSInputEventStream[I: SerializeableShape, R](InputEventStream[I, R]):
    """An input event stream using the application/vnd.amazon.eventstream format."""

    def __init__(
        self,
        payload_codec: Codec,
        async_writer: AsyncWriter,
        initial_response: R | None = None,
        signer: Signer | None = None,
        is_client_mode: bool = True,
    ) -> None:
        """Construct an AWSInputEventStream.

        :param payload_codec: The codec to encode the event payload with.
        :param async_writer: The writer to write event bytes to.
        :param initial_response: The deserialized operation response, if available.
        :param signer: An optional callable to sign events with prior to them being
            encoded.
        :param is_client_mode: Whether the stream is being constructed for a client or
            server implementation.
        """
        self._response = initial_response

        # Create a future to allow awaiting the initial response.
        loop = asyncio.get_event_loop()
        self._response_future: asyncio.Future[R] = loop.create_future()
        if initial_response is not None:
            self._response_future.set_result(initial_response)

        self.input_stream = _AWSEventPublisher(
            payload_codec=payload_codec,
            async_writer=async_writer,
            signer=signer,
            is_client_mode=is_client_mode,
        )

    @property
    def response(self) -> R | None:
        return self._response

    @response.setter
    def response(self, value: R) -> None:
        self._response_future.set_result(value)
        self._response = value

    async def await_output(self) -> R:
        return await self._response_future


class AWSOutputEventStream[O: DeserializeableShape, R: DeserializeableShape](
    OutputEventStream[O, R]
):
    """An output event stream using the application/vnd.amazon.eventstream format."""

    def __init__(
        self,
        payload_codec: Codec,
        initial_response: R,
        async_reader: AsyncByteStream,
        deserializer: Callable[[ShapeDeserializer], O],
        is_client_mode: bool = True,
    ) -> None:
        """Construct an AWSOutputEventStream.

        :param payload_codec: The codec to decode event payloads with.
        :param initial_response: The deserialized operation response. If this is not
            available immediately, use ``AWSOutputEventStream.create``.
        :param async_reader: An async reader to read event bytes from.
        :param deserializer: A callable to deserialize events with. This should be the
            union's deserialize method.
        :param is_client_mode: Whether the stream is being constructed for a client or
            server implementation.
        """
        self.response = initial_response
        self.output_stream = _AWSEventReceiver[O](
            payload_codec=payload_codec,
            source=async_reader,
            deserializer=deserializer,
            is_client_mode=is_client_mode,
        )

    @classmethod
    async def create(
        cls,
        payload_codec: Codec,
        deserializeable_response: type[R],
        async_reader: AsyncByteStream,
        deserializer: Callable[[ShapeDeserializer], O],
        is_client_mode: bool = True,
    ) -> Self:
        """Construct an AWSOutputEventStream and decode the initial response.

        :param payload_codec: The codec to decode event payloads with.
        :param deserializeable_response: The deserializeable response class. The
            deserialize method of this class will be used to deserialize the
            initial response from the stream..
        :param initial_response: The deserialized operation response. If this is not
            available immediately, use ``AWSOutputEventStream.create``.
        :param async_reader: An async reader to read event bytes from.
        :param deserializer: A callable to deserialize events with. This should be the
            union's deserialize method.
        :param is_client_mode: Whether the stream is being constructed for a client or
            server implementation.
        """
        initial_response_stream = _AWSEventReceiver(
            payload_codec=payload_codec,
            source=async_reader,
            deserializer=deserializeable_response.deserialize,
            is_client_mode=is_client_mode,
        )
        initial_response = await initial_response_stream.receive()
        if initial_response is None:
            raise MissingInitialResponse()

        return cls(
            payload_codec=payload_codec,
            initial_response=initial_response,
            async_reader=async_reader,
            deserializer=deserializer,
            is_client_mode=is_client_mode,
        )
