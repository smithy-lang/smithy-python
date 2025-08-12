#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import asyncio
import logging
from asyncio import Future, sleep
from collections.abc import Awaitable, Callable, Sequence
from copy import copy
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

from .. import URI
from ..auth import AuthParams
from ..deserializers import DeserializeableShape, ShapeDeserializer
from ..endpoints import EndpointResolverParams
from ..exceptions import RetryError, SmithyError
from ..interceptors import (
    InputContext,
    Interceptor,
    OutputContext,
    RequestContext,
    ResponseContext,
)
from ..interfaces import Endpoint, TypedProperties
from ..interfaces.auth import AuthOption, AuthSchemeResolver
from ..interfaces.retries import RetryStrategy
from ..schemas import APIOperation
from ..serializers import SerializeableShape
from ..shapes import ShapeID
from ..types import PropertyKey
from .eventstream import DuplexEventStream, InputEventStream, OutputEventStream
from .interfaces import (
    ClientProtocol,
    ClientTransport,
    EndpointResolver,
    Request,
    Response,
)
from .interfaces.auth import AuthScheme
from .interfaces.eventstream import EventReceiver
from .utils import seek

if TYPE_CHECKING:
    from typing_extensions import TypeForm

AUTH_SCHEME = PropertyKey(key="auth_scheme", value_type=AuthScheme[Any, Any, Any, Any])

_UNRESOLVED = URI(host="", path="/")
_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True, frozen=True)
class ClientCall[I: SerializeableShape, O: DeserializeableShape]:
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

    supported_auth_schemes: dict[ShapeID, AuthScheme[Any, Any, Any, Any]]
    """The supported auth schemes for the operation."""

    endpoint_resolver: EndpointResolver
    """The endpoint resolver for the operation."""

    retry_strategy: RetryStrategy
    """The retry strategy to use for the operation."""

    retry_scope: str | None = None
    """The retry scope for the operation."""

    def retryable(self) -> bool:
        # TODO: check to see if the stream is seekable
        return self.operation.input_stream_member is None


class RequestPipeline[TRequest: Request, TResponse: Response]:
    """Invokes client operations asynchronously."""

    protocol: ClientProtocol[TRequest, TResponse]
    """The protocol to use to serialize the request and deserialize the response."""

    transport: ClientTransport[TRequest, TResponse]
    """The transport to use to send the request and receive the response (e.g. an HTTP
    Client)."""

    def __init__(
        self,
        protocol: ClientProtocol[TRequest, TResponse],
        transport: ClientTransport[TRequest, TResponse],
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
    ) -> InputEventStream[E, O]:
        """Invoke an input stream operation asynchronously.

        :param call: The operation to invoke and associated context.
        :param event_type: The event type to send in the input stream.
        """
        request_future = Future[RequestContext[I, TRequest]]()
        output_future = asyncio.create_task(
            self._await_output(self._execute_request(call, request_future))
        )
        request_context = await request_future
        input_stream = self.protocol.create_event_publisher(
            operation=call.operation,
            request=request_context.transport_request,
            event_type=event_type,
            context=request_context.properties,
            auth_scheme=request_context.properties.get(AUTH_SCHEME),
        )
        return InputEventStream(input_stream=input_stream, output_future=output_future)

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
        call: ClientCall[I, O],
        event_type: "TypeForm[E]",
        event_deserializer: Callable[[ShapeDeserializer], E],
        /,
    ) -> OutputEventStream[E, O]:
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
        return OutputEventStream(output_stream=output_stream, output=output)

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
    ) -> DuplexEventStream[IE, OE, O]:
        """Invoke an input stream operation asynchronously.

        :param call: The operation to invoke and associated context.
        :param input_event_type: The event type to send in the input stream.
        :param output_event_type: The event type to receive in the output stream.
        :param event_deserializer: The method used to deserialize events.
        """
        request_future = Future[RequestContext[I, TRequest]]()
        execute_task = asyncio.create_task(self._execute_request(call, request_future))
        request_context = await request_future
        input_stream = self.protocol.create_event_publisher(
            operation=call.operation,
            request=request_context.transport_request,
            event_type=input_event_type,
            context=request_context.properties,
            auth_scheme=request_context.properties.get(AUTH_SCHEME),
        )
        output_future = asyncio.create_task(
            self._await_output_stream(
                call=call,
                execute_task=execute_task,
                output_event_type=output_event_type,
                event_deserializer=event_deserializer,
            )
        )
        return DuplexEventStream(input_stream=input_stream, output_future=output_future)

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
    ) -> tuple[O, EventReceiver[OE]]:
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
        call: ClientCall[I, O],
        request_future: Future[RequestContext[I, TRequest]] | None,
    ) -> tuple[O, OutputContext[I, O, TRequest, TResponse]]:
        _LOGGER.debug(
            'Making request for operation "%s" with parameters: %s',
            call.operation.schema.id.name,
            call.input,
        )
        output_context = await self._handle_execution(call, request_future)
        output_context = self._finalize_execution(call, output_context)

        if isinstance(output_context.response, Exception):
            e = output_context.response
            if not isinstance(e, SmithyError):
                raise SmithyError(e) from e
            raise e

        return output_context.response, output_context  # type: ignore

    async def _handle_execution[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: ClientCall[I, O],
        request_future: Future[RequestContext[I, TRequest]] | None,
    ) -> OutputContext[I, O, TRequest | None, TResponse | None]:
        try:
            interceptor = call.interceptor

            input_context = InputContext(request=call.input, properties=call.context)
            interceptor.read_before_execution(input_context)

            input_context = replace(
                input_context,
                request=interceptor.modify_before_serialization(input_context),
            )

            interceptor.read_before_serialization(input_context)
            _LOGGER.debug("Serializing request for: %s", input_context.request)

            transport_request = self.protocol.serialize_request(
                operation=call.operation,
                input=call.input,
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
                request=call.input,
                response=e,
                transport_request=None,
                transport_response=None,
                properties=call.context,
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
        call: ClientCall[I, O],
        request_context: RequestContext[I, TRequest],
        request_future: Future[RequestContext[I, TRequest]] | None,
    ) -> OutputContext[I, O, TRequest | None, TResponse | None]:
        if not call.retryable():
            return await self._handle_attempt(call, request_context, request_future)

        retry_strategy = call.retry_strategy
        retry_token = retry_strategy.acquire_initial_retry_token(
            token_scope=call.retry_scope
        )

        while True:
            if retry_token.retry_delay:
                await sleep(retry_token.retry_delay)

            output_context = await self._handle_attempt(
                call,
                replace(
                    request_context,
                    transport_request=copy(request_context.transport_request),
                ),
                request_future,
            )

            if isinstance(output_context.response, Exception):
                try:
                    retry_strategy.refresh_retry_token_for_retry(
                        token_to_renew=retry_token,
                        error=output_context.response,
                    )
                except RetryError:
                    raise output_context.response

                _LOGGER.debug(
                    "Retry needed. Attempting request #%s in %.4f seconds.",
                    retry_token.retry_count + 1,
                    retry_token.retry_delay,
                )

                await seek(request_context.transport_request.body, 0)
            else:
                retry_strategy.record_success(token=retry_token)
                return output_context

    async def _handle_attempt[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: ClientCall[I, O],
        request_context: RequestContext[I, TRequest],
        request_future: Future[RequestContext[I, TRequest]] | None,
    ) -> OutputContext[I, O, TRequest, TResponse | None]:
        output_context: OutputContext[I, O, TRequest, TResponse | None]
        try:
            interceptor = call.interceptor
            interceptor.read_before_attempt(request_context)

            endpoint_params = EndpointResolverParams(
                operation=call.operation,
                input=call.input,
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
                signer_properties.update(option.identity_properties)
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
                transport_response=None,
                properties=request_context.properties,
            )

        return self._finalize_attempt(call, output_context)

    def _resolve_auth[I: SerializeableShape, O: DeserializeableShape](
        self, call: ClientCall[Any, Any], params: AuthParams[I, O]
    ) -> tuple[AuthOption, AuthScheme[TRequest, Any, Any, Any]] | None:
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
        call: ClientCall[I, O],
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
        call: ClientCall[I, O],
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
