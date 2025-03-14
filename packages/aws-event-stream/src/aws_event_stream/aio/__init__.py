# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from typing import Self, Awaitable

from smithy_core.aio.interfaces import AsyncByteStream, AsyncWriter, Response
from smithy_core.aio.types import AsyncBytesReader
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
from .._private.serializers import EventSigner
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
        awaitable_response: Awaitable[Response],
        awaitable_output: Awaitable[R],
        deserializeable_response: type[R] | None = None,
        signer: EventSigner | None = None,
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
        self._deserializeable_response = deserializeable_response

        self._awaitable_response = awaitable_response
        self._awaitable_output = awaitable_output
        self.response: R | None = None

    async def await_output(self) -> tuple[R, AsyncEventReceiver[O]]:
        try:
            async_reader = AsyncBytesReader((await self._awaitable_response).body)
            if self.output_stream is None:
                self.output_stream = _AWSEventReceiver[O](
                    payload_codec=self._payload_codec,
                    source=async_reader,
                    deserializer=self._deserializer,
                    is_client_mode=self._is_client_mode,
                )

            if self.response is None:
                if self._deserializeable_response is None:
                    initial_response = await self._awaitable_output
                else:
                    initial_response_stream = _AWSEventReceiver(
                        payload_codec=self._payload_codec,
                        source=async_reader,
                        deserializer=self._deserializeable_response.deserialize,
                        is_client_mode=self._is_client_mode,
                    )
                    initial_response = await initial_response_stream.receive()
                    if initial_response is None:
                        raise MissingInitialResponse()
                    self.response = initial_response
            else:
                initial_response = self.response
        except Exception:
            await self.input_stream.close()
            raise

        return initial_response, self.output_stream


class AWSInputEventStream[I: SerializeableShape, R](InputEventStream[I, R]):
    """An input event stream using the application/vnd.amazon.eventstream format."""

    def __init__(
        self,
        payload_codec: Codec,
        async_writer: AsyncWriter,
        awaitable_output: Awaitable[R],
        signer: EventSigner | None = None,
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
        self.response: R | None = None
        self._awaitable_response = awaitable_output

        self.input_stream = _AWSEventPublisher(
            payload_codec=payload_codec,
            async_writer=async_writer,
            signer=signer,
            is_client_mode=is_client_mode,
        )

    async def await_output(self) -> R:
        if self.response is None:
            try:
                self.response = await self._awaitable_response
            except Exception:
                await self.input_stream.close()
                raise
        return self.response


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
