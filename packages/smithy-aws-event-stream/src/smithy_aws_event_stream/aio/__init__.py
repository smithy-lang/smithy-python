# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import contextlib
import logging
from collections.abc import Callable, Mapping
from typing import Any

from smithy_core.aio.interfaces import AsyncByteStream, AsyncWriter
from smithy_core.aio.interfaces.eventstream import (
    AsyncEventPublisher,
    AsyncEventReceiver,
)
from smithy_core.aio.interfaces.identity import AsyncIdentityResolver
from smithy_core.aio.program import run_program_async
from smithy_core.aio.utils import close_async
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.exceptions import ExpectationNotMetError
from smithy_core.interfaces.identity import Identity
from smithy_core.serializers import SerializeableShape

from .._private.deserializers import EventDeserializer as _EventDeserializer
from .._private.serializers import EventSerializer as _EventSerializer
from ..events import Event, EventMessage
from ..exceptions import EventError
from ..signing import SigningConfig

__all__ = ["AsyncAWSEventPublisher", "AsyncAWSEventReceiver", "decode_event_async"]

logger: logging.Logger = logging.getLogger(__name__)


async def decode_event_async(source: AsyncByteStream) -> Event | None:
    """Decode an event from an async byte stream.

    :param source: An object to read event bytes from. It must have an async `read`
        method that accepts a number of bytes to read.

    :returns: An Event representing the next event on the source, or None if no
        data can be read from the source.
    """
    return await run_program_async(Event._decode(source.read))  # pyright: ignore[reportPrivateUsage]


class AsyncAWSEventPublisher[E: SerializeableShape](AsyncEventPublisher[E]):
    """Publishes events to an AWS event stream."""

    def __init__[I: Identity, IP: Mapping[str, Any], SP: Mapping[str, Any]](
        self,
        payload_codec: Codec,
        async_writer: AsyncWriter,
        signing_config: "_AsyncSigningConfig[I, IP, SP] | None" = None,
        is_client_mode: bool = True,
        initial_message: EventMessage | None = None,
    ):
        self._writer = async_writer
        # The publisher only hands the resolved identity to the signer, so it stores
        # whichever consistent identity and property types the caller chose.
        self._signing_config: _AsyncSigningConfig[Any, Any, Any] | None = signing_config
        self._serializer = _EventSerializer(
            payload_codec=payload_codec, is_client_mode=is_client_mode
        )
        self._initial_message = initial_message
        self._closed = False

    async def prepare(self) -> None:
        """Flush the initial-request event, if any, before the first user event.

        Duplex peers may gate their initial-response on it, so the caller flushes it
        at stream creation rather than leaving it until the first ``send``.
        """
        await self._write_initial()

    async def send(self, event: E) -> None:
        if self._closed:
            raise OSError("Attempted to write to closed stream.")
        await self._write_initial()
        event.serialize(self._serializer)
        result = self._serializer.get_result()
        if result is None:
            raise ExpectationNotMetError(
                "Expected an event message to be serialized, but was None."
            )
        await self._write(result)

    async def close(self) -> None:
        if self._closed:
            return
        # The initial-request is part of the stream even if no user event follows, so
        # it must go out before the terminating frame.
        await self._write_initial()
        self._closed = True

        try:
            # Send a signed empty frame to signal stream completion.
            if self._signing_config is not None:
                end_frame = EventMessage()
                identity = await self._signing_config.identity_resolver.get_identity(
                    properties=self._signing_config.identity_properties
                )
                end_frame = self._signing_config.signer.sign_empty(
                    event=end_frame,
                    identity=identity,
                    properties=self._signing_config.signing_properties,
                )
                logger.debug(
                    "Sending signed empty message to terminate the event stream."
                )
                await self._writer.write(end_frame.encode())
        finally:
            await close_async(self._writer)

    @property
    def closed(self) -> bool:
        """Whether the publisher has been closed."""
        return self._closed

    async def _write_initial(self) -> None:
        # The initial-request seeds the event signature chain off the request
        # signature, so it must be the first frame signed and written -- not poured
        # into the body unsigned ahead of the signer.
        if (initial := self._initial_message) is not None:
            # Clear only after a successful write: signing or the socket write can
            # fail, and the frame must stay pending rather than be silently skipped.
            await self._write(initial)
            self._initial_message = None

    async def _write(self, message: EventMessage) -> None:
        if self._signing_config is not None:
            identity = await self._signing_config.identity_resolver.get_identity(
                properties=self._signing_config.identity_properties
            )
            message = self._signing_config.signer.sign(
                event=message,
                identity=identity,
                properties=self._signing_config.signing_properties,
            )
        try:
            logger.debug("Publishing serialized event: %s", message)
            await self._writer.write(message.encode())
        except Exception as e:
            # The stream is broken. Abort the underlying writer directly rather than
            # routing through close(), which re-flushes the pending initial frame onto
            # the dead writer and tries to send a signed terminator that would also fail.
            self._closed = True
            self._initial_message = None
            with contextlib.suppress(Exception):
                await close_async(self._writer)
            raise OSError("Failed to write to stream.") from e


class AsyncAWSEventReceiver[E: DeserializeableShape](AsyncEventReceiver[E]):
    """Receives events from an AWS event stream."""

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
        self._closed = False

    async def receive(self) -> E | None:
        if self._closed:
            return None

        try:
            event = await decode_event_async(self._source)
        except Exception as e:
            await self.close()
            if not isinstance(e, EventError):
                raise OSError("Failed to read from stream.") from e
            raise

        if event is None:
            logger.debug("No event received from the source.")
            return None
        logger.debug("Received raw event: %s", event)

        deserializer = _EventDeserializer(
            event=event,
            payload_codec=self._payload_codec,
            is_client_mode=self._is_client_mode,
        )
        result = self._deserializer(deserializer)
        logger.debug("Successfully deserialized event: %s", result)
        value = getattr(result, "value", None)
        if isinstance(value, Exception):
            raise value
        return result

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await close_async(self._source)

    @property
    def closed(self) -> bool:
        """Whether the receiver has been closed."""
        return self._closed


type _AsyncSigningConfig[I: Identity, IP: Mapping[str, Any], SP: Mapping[str, Any]] = (
    SigningConfig[I, IP, SP, AsyncIdentityResolver[I, IP]]
)
