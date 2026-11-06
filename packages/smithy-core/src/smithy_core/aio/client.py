#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import contextlib
import logging
from asyncio import Future, sleep
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, ClassVar, Self

from smithy_core.interfaces import ClientProtocol, Request, Response

from .._client import ClientBase as _ClientBase
from .._pipeline import RequestPipelineBase
from ..client import ClientCall
from ..deserializers import DeserializeableShape, ShapeDeserializer
from ..exceptions import UnsupportedStreamError, UnsupportedTransportError
from ..interceptors import (
    OutputContext,
    RequestContext,
)
from ..schemas import APIOperation
from ..serializers import SerializeableShape
from ..types import PropertyKey
from .eventstream import (
    AsyncDuplexEventStream,
    AsyncInputEventStream,
    AsyncOutputEventStream,
)
from .interfaces import AsyncClientProtocol, AsyncClientTransport
from .interfaces.auth import AsyncAuthScheme
from .interfaces.eventstream import AsyncEventReceiver
from .program import run_program_async
from .utils import read_streaming_blob_async

if TYPE_CHECKING:
    from typing_extensions import TypeForm

    from .interfaces.eventstream import AsyncEventPublisher

AUTH_SCHEME = PropertyKey(
    key="auth_scheme", value_type=AsyncAuthScheme[Any, Any, Any, Any]
)


class AsyncRequestPipeline[TRequest: Request, TResponse: Response](
    RequestPipelineBase[TRequest, TResponse]
):
    """Invokes client operations asynchronously."""

    protocol: ClientProtocol[TRequest, TResponse]
    """The protocol to use to serialize the request and deserialize the response.

    Event stream operations need an :py:class:`AsyncClientProtocol`.
    """

    transport: AsyncClientTransport[TRequest, TResponse]
    """The transport to use to send the request and receive the response (e.g. an HTTP
    Client)."""

    _logger: ClassVar[logging.Logger] = logging.getLogger("smithy_core.aio.client")

    def __init__(
        self,
        protocol: ClientProtocol[TRequest, TResponse],
        transport: AsyncClientTransport[TRequest, TResponse],
    ) -> None:
        self.protocol = protocol
        self.transport = transport

    async def __call__[I: SerializeableShape, O: DeserializeableShape](
        self, call: ClientCall[I, O], /
    ) -> O:
        """Invoke an operation asynchronously.

        :param call: The operation to invoke and associated context.
        """
        output, _ = await self._execute_request(call, None)
        return output

    async def input_stream[
        I: SerializeableShape,
        O: DeserializeableShape,
        E: SerializeableShape,
    ](
        self, call: ClientCall[I, O], event_type: "TypeForm[E]", /
    ) -> AsyncInputEventStream[E, O]:
        """Invoke an input stream operation asynchronously.

        :param call: The operation to invoke and associated context.
        :param event_type: The event type to send in the input stream.
        """
        request_future = Future[RequestContext[I, TRequest]]()
        output_future = asyncio.create_task(
            self._await_output(self._execute_request(call, request_future))
        )
        input_stream = await self._start_publisher(
            call, event_type, request_future, output_future
        )
        return AsyncInputEventStream(
            input_stream=input_stream, output_future=output_future
        )

    async def output_stream[
        I: SerializeableShape,
        O: DeserializeableShape,
        E: DeserializeableShape,
    ](
        self,
        call: ClientCall[I, O],
        event_type: "TypeForm[E]",
        event_deserializer: Callable[[ShapeDeserializer], E],
        /,
    ) -> AsyncOutputEventStream[E, O]:
        """Invoke an input stream operation asynchronously.

        :param call: The operation to invoke and associated context.
        :param event_type: The event type to receive in the output stream.
        :param event_deserializer: The method used to deserialize events.
        """
        output, output_context = await self._execute_request(call, None)
        output_stream = self._event_stream_protocol().create_event_receiver(
            operation=call.operation,
            request=output_context.transport_request,
            response=output_context.transport_response,
            event_type=event_type,
            event_deserializer=event_deserializer,
            context=output_context.properties,
        )
        return AsyncOutputEventStream(output_stream=output_stream, output=output)

    async def duplex_stream[
        I: SerializeableShape,
        O: DeserializeableShape,
        IE: SerializeableShape,
        OE: DeserializeableShape,
    ](
        self,
        call: ClientCall[I, O],
        input_event_type: "TypeForm[IE]",
        output_event_type: "TypeForm[OE]",
        event_deserializer: Callable[[ShapeDeserializer], OE],
        /,
    ) -> AsyncDuplexEventStream[IE, OE, O]:
        """Invoke an input stream operation asynchronously.

        :param call: The operation to invoke and associated context.
        :param input_event_type: The event type to send in the input stream.
        :param output_event_type: The event type to receive in the output stream.
        :param event_deserializer: The method used to deserialize events.
        """
        # The transport is assumed not to support duplex streaming unless it
        # explicitly declares otherwise.
        if getattr(self.transport, "SUPPORTS_DUPLEX_STREAMING", False) is not True:
            raise UnsupportedTransportError(
                f"The configured transport ({type(self.transport).__name__}) does "
                f"not support duplex (bidirectional) event streaming, which is "
                f"required by the {call.operation.schema.id} operation. Use a "
                f"transport that does, such as "
                f"smithy_http.aio.crt.AWSCRTHTTPClient. Custom transports that "
                f"support duplex streaming can implement AsyncDuplexClientTransport "
                f"by setting SUPPORTS_DUPLEX_STREAMING to True."
            )
        request_future = Future[RequestContext[I, TRequest]]()
        execute_task = asyncio.create_task(self._execute_request(call, request_future))
        input_stream = await self._start_publisher(
            call, input_event_type, request_future, execute_task
        )
        output_future = asyncio.create_task(
            self._await_output_stream(
                call=call,
                execute_task=execute_task,
                output_event_type=output_event_type,
                event_deserializer=event_deserializer,
            )
        )
        return AsyncDuplexEventStream(
            input_stream=input_stream, output_future=output_future
        )

    async def _start_publisher[I: SerializeableShape, E: SerializeableShape](
        self,
        call: ClientCall[I, Any],
        event_type: "TypeForm[E]",
        request_future: Future[RequestContext[I, TRequest]],
        execute_task: "asyncio.Task[Any]",
    ) -> "AsyncEventPublisher[E]":
        request_context = await request_future
        try:
            return await self._event_stream_protocol().create_event_publisher(
                operation=call.operation,
                request=request_context.transport_request,
                event_type=event_type,
                context=request_context.properties,
                auth_scheme=request_context.properties.get(AUTH_SCHEME),
            )
        except BaseException:
            # Publisher creation failed; the request task is still running, so cancel
            # and drain it rather than leaking a pending task.
            execute_task.cancel()
            with contextlib.suppress(BaseException):
                await execute_task
            raise

    async def _await_output[I: SerializeableShape, O: DeserializeableShape](
        self,
        execute_task: Awaitable[tuple[O, OutputContext[I, O, TRequest, TResponse]]],
    ) -> O:
        output, _ = await execute_task
        return output

    async def _await_output_stream[
        I: SerializeableShape,
        O: DeserializeableShape,
        OE: DeserializeableShape,
    ](
        self,
        call: ClientCall[I, O],
        execute_task: Awaitable[tuple[O, OutputContext[I, O, TRequest, TResponse]]],
        output_event_type: "TypeForm[OE]",
        event_deserializer: Callable[[ShapeDeserializer], OE],
    ) -> tuple[O, AsyncEventReceiver[OE]]:
        output, output_context = await execute_task
        output_stream = self._event_stream_protocol().create_event_receiver(
            operation=call.operation,
            request=output_context.transport_request,
            response=output_context.transport_response,
            event_type=output_event_type,
            event_deserializer=event_deserializer,
            context=output_context.properties,
        )
        return output, output_stream

    async def _execute_request[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: ClientCall[I, O],
        request_future: Future[RequestContext[I, TRequest]] | None,
    ) -> tuple[O, OutputContext[I, O, TRequest, TResponse]]:
        return await run_program_async(self._execute(call, request_future))

    def _event_stream_protocol(self) -> AsyncClientProtocol[TRequest, TResponse]:
        if not isinstance(self.protocol, AsyncClientProtocol):
            raise UnsupportedStreamError(
                f"The configured protocol ({type(self.protocol).__name__}) does not "
                "support event streams."
            )
        return self.protocol  # type: ignore[reportUnknownVariableType]

    async def _read_body(self, body: Any) -> bytes:
        return await read_streaming_blob_async(body)

    async def _sleep(self, delay: float) -> None:
        await sleep(delay)

    async def _transmit(
        self,
        request_context: RequestContext[Any, TRequest],
        request_future: Future[RequestContext[Any, TRequest]] | None,
    ) -> TResponse:
        if request_future is None:
            # If we don't have an input stream, there's no point in creating a
            # task, so we just immediately await the coroutine.
            return await self.transport.send(request=request_context.transport_request)
        # If we have an input event stream (or duplex event stream) then we need to
        # let the client return ASAP so that it can start sending events. So here we
        # start the transport send in a background task then set the result of the
        # request future. It's important to sequence it just like that so that the
        # client gets a stream that's ready to send.
        transport_task = asyncio.create_task(
            self.transport.send(request=request_context.transport_request)
        )
        request_future.set_result(request_context)
        return await transport_task

    def _fail_request_future(
        self,
        request_future: Future[RequestContext[Any, TRequest]] | None,
        error: Exception,
    ) -> None:
        if request_future is not None and not request_future.done():
            request_future.set_exception(error)


class AsyncClient[C](_ClientBase[C]):
    """Shared async client machinery: lifecycle, setup gating, and call dispatch.

    Generated clients subclass this with their config type and supply
    ``_new_config``, plus ``_post_setup`` when setup needs more than plugins.
    """

    _pipeline_type = AsyncRequestPipeline
    _call_type = ClientCall

    def __init__(
        self,
        config: C | None = None,
        plugins: list[Callable[[C], None]] | None = None,
    ) -> None:
        super().__init__(config, plugins)
        self._derive_lock = asyncio.Lock()

    async def __aenter__(self) -> Self:
        if self._closed:
            raise RuntimeError("Cannot enter a client that has been closed.")
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close this client and any resources held by its transport."""
        if self._closed:
            return
        async with self._derive_lock:
            await run_program_async(self._close())

    async def _ensure_setup(self) -> C:
        if not self._setup_done:
            async with self._derive_lock:
                return await run_program_async(self._setup())
        return self._config

    async def _invoke[I: SerializeableShape, O: DeserializeableShape](
        self,
        input: I | None,
        operation: APIOperation[I, O],
        default_plugins: list[Callable[[C], None]],
        plugins: list[Callable[[C], None]] | None,
    ) -> O:
        pipeline, call = await self._prepare_call(
            input, operation, default_plugins, plugins
        )
        return await pipeline(call)

    async def _prepare_call[I: SerializeableShape, O: DeserializeableShape](
        self,
        input: I | None,
        operation: APIOperation[I, O],
        default_plugins: list[Callable[[C], None]],
        plugins: list[Callable[[C], None]] | None,
    ) -> tuple[AsyncRequestPipeline[Any, Any], ClientCall[I, O]]:
        self._raise_if_closed()
        config = await self._ensure_setup()
        return await run_program_async(
            self._prepare(config, input, operation, default_plugins, plugins)
        )
