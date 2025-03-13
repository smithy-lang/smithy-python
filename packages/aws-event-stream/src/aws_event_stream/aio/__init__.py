# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import asyncio
from collections.abc import Callable

from smithy_core.aio.interfaces import AsyncByteStream
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.exceptions import ExpectationNotMetException
from smithy_core.serializers import SerializeableShape
from smithy_core.aio.interfaces.eventstream import EventPublisher, EventReceiver
from smithy_core.aio.interfaces import AsyncWriter

from .._private.serializers import EventSerializer as _EventSerializer
from .._private.deserializers import EventDeserializer as _EventDeserializer
from ..events import Event, EventMessage


type Signer = Callable[[EventMessage], EventMessage]
"""A function that takes an event message and signs it, and returns it signed."""


class AWSEventPublisher[E: SerializeableShape](EventPublisher[E]):
    def __init__(
        self,
        payload_codec: Codec,
        async_writer: AsyncWriter,
        signer: Signer | None = None,
        is_client_mode: bool = True,
    ):
        self._writer = async_writer
        self._signer = signer
        self._serializer = _EventSerializer(
            payload_codec=payload_codec, is_client_mode=is_client_mode
        )

    async def send(self, event: E) -> None:
        event.serialize(self._serializer)
        result = self._serializer.get_result()
        if result is None:
            raise ExpectationNotMetException(
                "Expected an event message to be serialized, but was None."
            )
        if self._signer is not None:
            result = self._signer(result)
        await self._writer.write(result.encode())

    async def close(self) -> None:
        if (close := getattr(self._writer, "close", None)) is not None:
            if asyncio.iscoroutine(result := close()):
                await result


class AWSEventReceiver[E: DeserializeableShape](EventReceiver[E]):
    def __init__(
        self,
        payload_codec: Codec,
        source: AsyncByteStream,
        deserializer: Callable[[ShapeDeserializer], E],
        is_client_mode: bool = True,
    ) -> None:
        self._payload_codec = payload_codec
        self._source = source
        self._is_client_mode = is_client_mode
        self._deserializer = deserializer

    async def receive(self) -> E | None:
        event = await Event.decode_async(self._source)
        if event is None:
            return None

        deserializer = _EventDeserializer(
            event=event,
            payload_codec=self._payload_codec,
            is_client_mode=self._is_client_mode,
        )
        result = self._deserializer(deserializer)
        if isinstance(getattr(result, "value"), Exception):
            raise result.value  # type: ignore
        return result

    async def close(self) -> None:
        if (close := getattr(self._source, "close", None)) is not None:
            if asyncio.iscoroutine(result := close()):
                await result
