# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from smithy_core.aio.interfaces import AsyncByteStream, AsyncWriter
from smithy_core.aio.interfaces.auth import EventSigner
from smithy_core.aio.interfaces.eventstream import EventPublisher, EventReceiver
from smithy_core.aio.interfaces.identity import IdentityResolver
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.exceptions import ExpectationNotMetError
from smithy_core.serializers import SerializeableShape

from .._private.deserializers import EventDeserializer as _EventDeserializer
from .._private.serializers import EventSerializer as _EventSerializer
from ..events import Event, EventMessage
from ..exceptions import EventError

__all__ = ["AWSEventPublisher", "AWSEventReceiver", "SigningConfig"]

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from aws_sdk_signers import SigV4SigningProperties
    from smithy_aws_core.identity import AWSCredentialsIdentity, AWSIdentityProperties


@dataclass
class SigningConfig:
    signer: "EventSigner[AWSCredentialsIdentity, SigV4SigningProperties]"
    signing_properties: "SigV4SigningProperties"
    identity_resolver: "IdentityResolver[AWSCredentialsIdentity, AWSIdentityProperties]"
    identity_properties: "AWSIdentityProperties"


class AWSEventPublisher[E: SerializeableShape](EventPublisher[E]):
    def __init__(
        self,
        payload_codec: Codec,
        async_writer: AsyncWriter,
        signing_config: SigningConfig | None = None,
        is_client_mode: bool = True,
        initial_message: EventMessage | None = None,
    ):
        self._writer = async_writer
        self._signing_config = signing_config
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
                end_frame = await self._signing_config.signer.sign_empty(
                    event=end_frame,
                    identity=identity,
                    properties=self._signing_config.signing_properties,
                )
                logger.debug(
                    "Sending signed empty message to terminate the event stream."
                )
                await self._writer.write(end_frame.encode())
        finally:
            if (close := getattr(self._writer, "close", None)) is not None:
                if asyncio.iscoroutine(result := close()):
                    await result

    @property
    def closed(self) -> bool:
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
            message = await self._signing_config.signer.sign(
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
            if (close := getattr(self._writer, "close", None)) is not None:
                with contextlib.suppress(Exception):
                    if asyncio.iscoroutine(result := close()):
                        await result
            raise OSError("Failed to write to stream.") from e


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
        self._closed = False

    async def receive(self) -> E | None:
        if self._closed:
            return None

        try:
            event = await Event.decode_async(self._source)
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

        if (close := getattr(self._source, "close", None)) is not None:
            if asyncio.iscoroutine(result := close()):
                await result

    @property
    def closed(self) -> bool:
        return self._closed
