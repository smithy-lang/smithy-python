#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import contextlib
import logging
from asyncio import Future, sleep
from collections.abc import Awaitable, Callable, Sequence
from copy import copy
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Self

from .. import URI
from ..auth import AuthParams
from ..deserializers import DeserializeableShape, ShapeDeserializer
from ..endpoints import EndpointResolverParams
from ..exceptions import (
    ClientTimeoutError,
    RetryError,
    SmithyError,
    UnsupportedTransportError,
)
from ..interceptors import (
    InputContext,
    Interceptor,
    InterceptorChain,
    OutputContext,
    RequestContext,
    ResponseContext,
)
from ..interfaces import Endpoint, TypedProperties
from ..interfaces.auth import AuthOption, AuthSchemeResolver
from ..schemas import APIOperation
from ..serializers import SerializeableShape
from ..shapes import ShapeID, ShapeType
from ..types import PropertyKey
from ..types import TypedProperties as _TypedProperties
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
from .retries import (
    RETRY_STRATEGY,
    AsyncAdaptiveRetryStrategy,
    AsyncRetryStrategyResolver,
)
from .utils import close, seek

if TYPE_CHECKING:
    from typing_extensions import TypeForm

AUTH_SCHEME = PropertyKey(
    key="auth_scheme", value_type=AsyncAuthScheme[Any, Any, Any, Any]
)

_UNRESOLVED = URI(host="", path="/")
_LOGGER = logging.getLogger(__name__)


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
        member = self.operation.input_stream_member
        return member is None or member.shape_type is not ShapeType.UNION


async def _rewind_position(body: Any) -> int | None:
    """Find where a request body is rewound to before it's resent.

    :returns: The body's current position, or None if it can't be rewound.
    """
    if body is None or isinstance(body, bytes | bytearray):
        return 0
    try:
        return await seek(body, 0, 1)
    except (OSError, ValueError, NotImplementedError):
        return None


class AsyncRequestPipeline[TRequest: Request, TResponse: Response]:
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
        _LOGGER.debug(
            'Making request for operation "%s" with parameters: %s',
            call.operation.schema.id.name,
            call.input,
        )
        output_context = await self._handle_execution(call, request_future)
        output_context = self._finalize_execution(call, output_context)

        self._attach_response_metadata(output_context)

        if isinstance(output_context.response, Exception):
            e = output_context.response
            if not isinstance(e, SmithyError):
                raise SmithyError(e) from e
            raise e

        return output_context.response, output_context  # type: ignore

    def _attach_response_metadata[I: SerializeableShape, O: DeserializeableShape](
        self,
        output_context: OutputContext[I, O, TRequest | None, TResponse | None],
    ) -> None:
        """Attach metadata about the transport response to the result or error.

        This runs for successes and failures alike, so that request identifiers
        stay available to callers for debugging. Results that do not carry the
        attribute are left untouched, as are cases where no response was received
        at all.
        """
        result = output_context.response
        transport_response = output_context.transport_response

        # Only reachable for errors raised before a response arrived, such as a
        # connection timeout. The default empty metadata is left in place, where
        # a null status code records that nothing came back.
        if transport_response is None:
            return

        if not hasattr(result, "response_metadata"):
            return

        try:
            metadata = self.protocol.extract_response_metadata(
                response=transport_response,
                context=output_context.properties,
            )
            setattr(result, "response_metadata", metadata)
        except Exception as e:
            # Metadata is diagnostic and must never fail a call. Both statements
            # above can raise: a broken protocol, or the assignment itself if the
            # output shape is frozen.
            _LOGGER.debug("Unable to attach response metadata: %s", e)

    async def _handle_execution[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: AsyncClientCall[I, O],
        request_future: Future[RequestContext[I, TRequest]] | None,
    ) -> OutputContext[I, O, TRequest | None, TResponse | None]:
        interceptor = call.interceptor
        input_context = InputContext(request=call.input, properties=call.context)
        try:
            interceptor.read_before_execution(input_context)

            input_context = replace(
                input_context,
                request=interceptor.modify_before_serialization(input_context),
            )

            interceptor.read_before_serialization(input_context)
            _LOGGER.debug("Serializing request for: %s", input_context.request)

            transport_request = self.protocol.serialize_request(
                operation=call.operation,
                input=input_context.request,
                endpoint=_UNRESOLVED,
                context=input_context.properties,
            )
            request_context = RequestContext(
                request=input_context.request,
                transport_request=transport_request,
                properties=input_context.properties,
            )

            _LOGGER.debug(
                "Serialization complete. Transport request: %s", transport_request
            )
        except Exception as e:
            return OutputContext(
                request=input_context.request,
                response=e,
                transport_request=None,
                transport_response=None,
                properties=input_context.properties,
            )

        try:
            interceptor.read_after_serialization(request_context)
            request_context = replace(
                request_context,
                transport_request=interceptor.modify_before_retry_loop(request_context),
            )

            return await self._retry(call, request_context, request_future)
        except Exception as e:
            return OutputContext(
                request=request_context.request,
                response=e,
                transport_request=request_context.transport_request,
                transport_response=None,
                properties=request_context.properties,
            )

    async def _retry[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: AsyncClientCall[I, O],
        request_context: RequestContext[I, TRequest],
        request_future: Future[RequestContext[I, TRequest]] | None,
    ) -> OutputContext[I, O, TRequest | None, TResponse | None]:
        body = request_context.transport_request.body
        if not call.retryable() or (start := await _rewind_position(body)) is None:
            return await self._send_with_rate_limiting(
                call, request_context, request_future
            )

        retry_strategy = call.retry_strategy
        retry_token = await retry_strategy.acquire_initial_retry_token(
            token_scope=call.retry_scope
        )

        last_output_context: OutputContext[I, O, TRequest, TResponse | None] | None = (
            None
        )
        while True:
            if retry_token.retry_delay:
                await sleep(retry_token.retry_delay)

            try:
                output_context = await self._send_with_rate_limiting(
                    call,
                    replace(
                        request_context,
                        transport_request=copy(request_context.transport_request),
                    ),
                    request_future,
                )
            except TimeoutError as e:
                # Only the adaptive send-token wait raises this. If it happens on a
                # retry, return the previous failed attempt (as when attempts run out)
                # so the caller's error still includes that response's request ID.
                if last_output_context is None:
                    raise
                last_error = last_output_context.response
                if isinstance(last_error, Exception):
                    last_error.add_note(f"Retry not attempted: {e}")
                return last_output_context

            if isinstance(output_context.response, Exception):
                last_output_context = output_context
                try:
                    retry_token = await retry_strategy.refresh_retry_token_for_retry(
                        token_to_renew=retry_token,
                        error=output_context.response,
                    )
                except RetryError as retry_error:
                    # Long-polling operations back off even when the retry quota
                    # is exhausted; the strategy surfaces that delay here.
                    if (
                        call.operation.long_polling
                        and retry_error.retry_after is not None
                    ):
                        await sleep(retry_error.retry_after)
                    # Keeps the final attempt's response, so throttling and 5xx
                    # failures still carry a request ID when _execute_request raises.
                    return output_context

                _LOGGER.debug(
                    "Retry needed. Attempting request #%s in %.4f seconds.",
                    retry_token.retry_count + 1,
                    retry_token.retry_delay,
                )

                try:
                    await seek(body, start)
                except (OSError, ValueError, NotImplementedError) as e:
                    output_context.response.add_note(f"Retry not attempted: {e}")
                    return output_context
            else:
                await retry_strategy.record_success(token=retry_token)
                return output_context

    async def _send_with_rate_limiting[
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        call: AsyncClientCall[I, O],
        request_context: RequestContext[I, TRequest],
        request_future: Future[RequestContext[I, TRequest]] | None,
    ) -> OutputContext[I, O, TRequest, TResponse | None]:
        """Send a single attempt, applying client-side rate limiting (adaptive only).

        Every attempt, retryable or not, acquires a send token before it is sent. Once a
        response comes back from the service, the rate limiter is updated with it.
        """
        retry_strategy = call.retry_strategy
        try:
            await self._handle_pre_request_rate_limiting(retry_strategy)
        except Exception as e:
            if request_future is not None and not request_future.done():
                request_future.set_exception(e)
            raise

        output_context = await self._handle_attempt(
            call, request_context, request_future
        )

        if output_context.transport_response is None:
            # Failed before sending, or the connection failed: not a service response
            return output_context

        if isinstance(output_context.response, Exception):
            await self._handle_post_error_response_rate_limiting(
                retry_strategy, output_context.response
            )
        else:
            await self._handle_success_rate_limiting(retry_strategy)
        return output_context

    async def _handle_pre_request_rate_limiting(
        self, retry_strategy: AsyncRetryStrategy
    ) -> None:
        """Handle rate limiting before sending request."""
        if isinstance(retry_strategy, AsyncAdaptiveRetryStrategy):
            await retry_strategy.acquire_from_token_bucket()

    async def _handle_post_error_response_rate_limiting(
        self, retry_strategy: AsyncRetryStrategy, error: Exception
    ) -> None:
        """Handle rate limiting after failed response."""
        if isinstance(retry_strategy, AsyncAdaptiveRetryStrategy):
            is_throttling = retry_strategy.is_throttling_error(error)
            await retry_strategy.rate_limiter.after_receiving_response(is_throttling)

    async def _handle_success_rate_limiting(
        self, retry_strategy: AsyncRetryStrategy
    ) -> None:
        """Handle rate limiting after successful response."""
        if isinstance(retry_strategy, AsyncAdaptiveRetryStrategy):
            await retry_strategy.rate_limiter.after_receiving_response(
                throttling_error=False
            )

    async def _handle_attempt[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: AsyncClientCall[I, O],
        request_context: RequestContext[I, TRequest],
        request_future: Future[RequestContext[I, TRequest]] | None,
    ) -> OutputContext[I, O, TRequest, TResponse | None]:
        output_context: OutputContext[I, O, TRequest, TResponse | None]
        # A modeled error arrives after the response does, so the response is kept
        # here to report alongside it. Stays None if nothing came back.
        transport_response: TResponse | None = None
        try:
            interceptor = call.interceptor
            interceptor.read_before_attempt(request_context)

            endpoint_params = EndpointResolverParams(
                operation=call.operation,
                input=request_context.request,
                context=request_context.properties,
            )
            _LOGGER.debug("Calling endpoint resolver with params: %s", endpoint_params)
            endpoint: Endpoint = await call.endpoint_resolver.resolve_endpoint(
                endpoint_params
            )
            _LOGGER.debug("Endpoint resolver result: %s", endpoint)

            request_context = replace(
                request_context,
                transport_request=self.protocol.set_service_endpoint(
                    request=request_context.transport_request, endpoint=endpoint
                ),
            )

            request_context = replace(
                request_context,
                transport_request=interceptor.modify_before_signing(request_context),
            )
            interceptor.read_before_signing(request_context)

            auth_params = AuthParams[I, O](
                protocol_id=self.protocol.id,
                operation=call.operation,
                context=request_context.properties,
            )
            auth = self._resolve_auth(call, auth_params)
            if auth is not None:
                option, scheme = auth
                request_context.properties[AUTH_SCHEME] = scheme
                identity_resolver = scheme.identity_resolver(context=call.context)

                identity_properties = scheme.identity_properties(
                    context=request_context.properties
                )
                identity_properties.update(option.identity_properties)

                identity = await identity_resolver.get_identity(
                    properties=identity_properties
                )

                signer_properties = scheme.signer_properties(
                    context=request_context.properties
                )
                signer_properties.update(option.signer_properties)
                _LOGGER.debug("Request to sign: %s", request_context.transport_request)
                _LOGGER.debug("Signer properties: %s", signer_properties)

                signer = scheme.signer()
                request_context = replace(
                    request_context,
                    transport_request=await signer.sign(
                        request=request_context.transport_request,
                        identity=identity,
                        properties=signer_properties,
                    ),
                )

            interceptor.read_after_signing(request_context)
            request_context = replace(
                request_context,
                transport_request=interceptor.modify_before_transmit(request_context),
            )
            interceptor.read_before_transmit(request_context)

            _LOGGER.debug("Sending request %s", request_context.transport_request)

            try:
                if request_future is not None:
                    # If we have an input event stream (or duplex event stream) then we
                    # need to let the client return ASAP so that it can start sending
                    # events. So here we start the transport send in a background task
                    # then set the result of the request future. It's important to sequence
                    # it just like that so that the client gets a stream that's ready
                    # to send.
                    transport_task = asyncio.create_task(
                        self.transport.send(request=request_context.transport_request)
                    )
                    request_future.set_result(request_context)
                    transport_response = await transport_task
                else:
                    # If we don't have an input stream, there's no point in creating a
                    # task, so we just immediately await the coroutine.
                    transport_response = await self.transport.send(
                        request=request_context.transport_request
                    )
            except Exception as e:
                if isinstance(e, self.transport.TIMEOUT_EXCEPTIONS):
                    raise ClientTimeoutError(message="A timeout error occurred.") from e
                raise

            _LOGGER.debug("Received response: %s", transport_response)

            response_context = ResponseContext(
                request=request_context.request,
                transport_request=request_context.transport_request,
                transport_response=transport_response,
                properties=request_context.properties,
            )

            interceptor.read_after_transmit(response_context)

            response_context = replace(
                response_context,
                transport_response=interceptor.modify_before_deserialization(
                    response_context
                ),
            )
            transport_response = response_context.transport_response

            interceptor.read_before_deserialization(response_context)

            _LOGGER.debug(
                "Deserializing response: %s", response_context.transport_response
            )

            output = await self.protocol.deserialize_response(
                operation=call.operation,
                request=response_context.transport_request,
                response=response_context.transport_response,
                error_registry=call.operation.error_registry,
                context=response_context.properties,
            )

            _LOGGER.debug("Deserialization complete. Output: %s", output)

            output_context = OutputContext(
                request=response_context.request,
                response=output,
                transport_request=response_context.transport_request,
                transport_response=response_context.transport_response,
                properties=response_context.properties,
            )

            interceptor.read_after_deserialization(output_context)
        except Exception as e:
            output_context = OutputContext(
                request=request_context.request,
                response=e,
                transport_request=request_context.transport_request,
                transport_response=transport_response,
                properties=request_context.properties,
            )

        return self._finalize_attempt(call, output_context)

    def _resolve_auth[I: SerializeableShape, O: DeserializeableShape](
        self, call: AsyncClientCall[Any, Any], params: AuthParams[I, O]
    ) -> tuple[AuthOption, AsyncAuthScheme[TRequest, Any, Any, Any]] | None:
        auth_options: Sequence[AuthOption] = (
            call.auth_scheme_resolver.resolve_auth_scheme(auth_parameters=params)
        )

        for option in auth_options:
            if (
                scheme := call.supported_auth_schemes.get(option.scheme_id)
            ) is not None:
                return option, scheme

        return None

    def _finalize_attempt[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: AsyncClientCall[I, O],
        output_context: OutputContext[I, O, TRequest, TResponse | None],
    ) -> OutputContext[I, O, TRequest, TResponse | None]:
        interceptor = call.interceptor
        try:
            output_context = replace(
                output_context,
                response=interceptor.modify_before_attempt_completion(output_context),
            )
        except Exception as e:
            output_context = replace(output_context, response=e)

        try:
            interceptor.read_after_attempt(output_context)
        except Exception as e:
            output_context = replace(output_context, response=e)

        return output_context

    def _finalize_execution[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: AsyncClientCall[I, O],
        output_context: OutputContext[I, O, TRequest | None, TResponse | None],
    ) -> OutputContext[I, O, TRequest | None, TResponse | None]:
        interceptor = call.interceptor
        try:
            output_context = replace(
                output_context,
                response=interceptor.modify_before_completion(output_context),
            )

            # TODO trace probe
        except Exception as e:
            output_context = replace(output_context, response=e)

        try:
            interceptor.read_after_execution(output_context)
        except Exception as e:
            output_context = replace(output_context, response=e)

        return output_context


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
        context = _TypedProperties({"config": config})
        context[RETRY_STRATEGY] = retry_strategy
        call = AsyncClientCall(
            input=input,
            operation=operation,
            context=context,
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
