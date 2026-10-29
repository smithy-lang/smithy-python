#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import contextlib
from asyncio import Future, sleep
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Self

from .._pipeline import RequestPipelineBase, is_retryable
from ..deserializers import DeserializeableShape, ShapeDeserializer
from ..exceptions import UnsupportedTransportError
from ..interceptors import (
    Interceptor,
    InterceptorChain,
    OutputContext,
    RequestContext,
)
from ..interfaces import TypedProperties
from ..interfaces.auth import AuthSchemeResolver
from ..schemas import APIOperation
from ..serializers import SerializeableShape
from ..shapes import ShapeID
from ..types import PropertyKey
from ..types import TypedProperties as _TypedProperties
from ._program import run_program_async
from .eventstream import (
    AsyncDuplexEventStream,
    AsyncInputEventStream,
    AsyncOutputEventStream,
)
from .interfaces import (
    AsyncClientProtocol,
    AsyncClientTransport,
    AsyncEndpointResolver,
    Request,
    Response,
)
from .interfaces.auth import AsyncAuthScheme
from .interfaces.eventstream import AsyncEventReceiver
from .interfaces.retries import AsyncRetryStrategy
from .retries import AsyncAdaptiveRetryStrategy, AsyncRetryStrategyResolver
from .utils import close

if TYPE_CHECKING:
    from typing_extensions import TypeForm

AUTH_SCHEME = PropertyKey(
    key="auth_scheme", value_type=AsyncAuthScheme[Any, Any, Any, Any]
)


@dataclass(kw_only=True, frozen=True)
class AsyncClientCall[I: SerializeableShape, O: DeserializeableShape]:
    """A data class containing all the initial information about an operation
    invocation."""

    input: I
    """The input of the operation."""

    operation: APIOperation[I, O] = field(repr=False)
    """The schema of the operation."""

    context: TypedProperties
    """The initial context of the operation."""

    interceptor: Interceptor[I, O, Any, Any]
    """The interceptor to use in the course of the operation invocation.

    This SHOULD be an InterceptorChain.
    """

    auth_scheme_resolver: AuthSchemeResolver
    """The auth scheme resolver for the operation."""

    supported_auth_schemes: dict[ShapeID, AsyncAuthScheme[Any, Any, Any, Any]]
    """The supported auth schemes for the operation."""

    endpoint_resolver: AsyncEndpointResolver
    """The endpoint resolver for the operation."""

    retry_strategy: AsyncRetryStrategy
    """The retry strategy to use for the operation."""

    retry_scope: str | None = None
    """The retry scope for the operation."""

    def retryable(self) -> bool:
        """Whether the operation can be retried.

        Operations with an input event stream are never retried. A request for any
        other operation is retried only if its body can be rewound to where it started.
        """
        return is_retryable(self.operation)


class AsyncRequestPipeline[TRequest: Request, TResponse: Response](
    RequestPipelineBase[TRequest, TResponse]
):
    """Invokes client operations asynchronously."""

    protocol: AsyncClientProtocol[TRequest, TResponse]
    """The protocol to use to serialize the request and deserialize the response."""

    transport: AsyncClientTransport[TRequest, TResponse]
    """The transport to use to send the request and receive the response (e.g. an HTTP
    Client)."""

    def __init__(
        self,
        protocol: AsyncClientProtocol[TRequest, TResponse],
        transport: AsyncClientTransport[TRequest, TResponse],
    ) -> None:
        self.protocol = protocol
        self.transport = transport

    async def __call__[I: SerializeableShape, O: DeserializeableShape](
        self, call: AsyncClientCall[I, O], /
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
        self, call: AsyncClientCall[I, O], event_type: "TypeForm[E]", /
    ) -> AsyncInputEventStream[E, O]:
        """Invoke an input stream operation asynchronously.

        :param call: The operation to invoke and associated context.
        :param event_type: The event type to send in the input stream.
        """
        request_future = Future[RequestContext[I, TRequest]]()
        output_future = asyncio.create_task(
            self._await_output(self._execute_request(call, request_future))
        )
        request_context = await request_future
        try:
            input_stream = await self.protocol.create_event_publisher(
                operation=call.operation,
                request=request_context.transport_request,
                event_type=event_type,
                context=request_context.properties,
                auth_scheme=request_context.properties.get(AUTH_SCHEME),
            )
        except BaseException:
            # Publisher creation failed; the request task is still running, so cancel
            # and drain it rather than leaking a pending task.
            output_future.cancel()
            with contextlib.suppress(BaseException):
                await output_future
            raise
        return AsyncInputEventStream(
            input_stream=input_stream, output_future=output_future
        )

    async def _await_output[I: SerializeableShape, O: DeserializeableShape](
        self,
        execute_task: Awaitable[tuple[O, OutputContext[I, O, TRequest, TResponse]]],
    ) -> O:
        output, _ = await execute_task
        return output

    async def output_stream[
        I: SerializeableShape,
        O: DeserializeableShape,
        E: DeserializeableShape,
    ](
        self,
        call: AsyncClientCall[I, O],
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
        output_stream = self.protocol.create_event_receiver(
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
        call: AsyncClientCall[I, O],
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
                f"support duplex streaming can implement DuplexClientTransport "
                f"by setting SUPPORTS_DUPLEX_STREAMING to True."
            )
        request_future = Future[RequestContext[I, TRequest]]()
        execute_task = asyncio.create_task(self._execute_request(call, request_future))
        request_context = await request_future
        try:
            input_stream = await self.protocol.create_event_publisher(
                operation=call.operation,
                request=request_context.transport_request,
                event_type=input_event_type,
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

    async def _await_output_stream[
        I: SerializeableShape,
        O: DeserializeableShape,
        OE: DeserializeableShape,
    ](
        self,
        call: AsyncClientCall[I, O],
        execute_task: Awaitable[tuple[O, OutputContext[I, O, TRequest, TResponse]]],
        output_event_type: "TypeForm[OE]",
        event_deserializer: Callable[[ShapeDeserializer], OE],
    ) -> tuple[O, AsyncEventReceiver[OE]]:
        output, output_context = await execute_task
        output_stream = self.protocol.create_event_receiver(
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
        call: AsyncClientCall[I, O],
        request_future: Future[RequestContext[I, TRequest]] | None,
    ) -> tuple[O, OutputContext[I, O, TRequest, TResponse]]:
        return await run_program_async(self._execute(call, request_future))

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

    def _adaptive_strategy(
        self, retry_strategy: AsyncRetryStrategy
    ) -> AsyncAdaptiveRetryStrategy | None:
        if isinstance(retry_strategy, AsyncAdaptiveRetryStrategy):
            return retry_strategy
        return None

    def _fail_request_future(
        self,
        request_future: Future[RequestContext[Any, TRequest]] | None,
        error: Exception,
    ) -> None:
        if request_future is not None and not request_future.done():
            request_future.set_exception(error)


class AsyncClient:
    """Shared async client machinery: lifecycle, setup gating, and call dispatch."""

    def __init__(self) -> None:
        self._derive_lock = asyncio.Lock()
        self._setup_done = False
        self._closed = False
        self._transport: AsyncClientTransport[Any, Any] | None = None
        self._retry_strategy_resolver = AsyncRetryStrategyResolver()

    def _build_call[I: SerializeableShape, O: DeserializeableShape](
        self,
        input: I,
        operation: APIOperation[I, O],
        *,
        config: Any,
        retry_strategy: AsyncRetryStrategy,
    ) -> tuple[AsyncRequestPipeline[Any, Any], AsyncClientCall[I, O]]:
        """Build the pipeline and call from a resolved config and retry strategy."""
        pipeline = AsyncRequestPipeline(
            protocol=config.protocol, transport=config.transport
        )
        call = AsyncClientCall(
            input=input,
            operation=operation,
            context=_TypedProperties({"config": config}),
            interceptor=InterceptorChain(config.interceptors),
            auth_scheme_resolver=config.auth_scheme_resolver,
            supported_auth_schemes=config.auth_schemes,
            endpoint_resolver=config.endpoint_resolver,
            retry_strategy=retry_strategy,
        )
        return pipeline, call

    async def close(self) -> None:
        """Close this client and any resources held by its transport."""
        if self._closed:
            return
        async with self._derive_lock:
            if self._closed:
                return
            self._closed = True
            if self._setup_done and self._transport is not None:
                await close(self._transport)

    async def __aenter__(self) -> Self:
        if self._closed:
            raise RuntimeError("Cannot enter a client that has been closed.")
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.close()
