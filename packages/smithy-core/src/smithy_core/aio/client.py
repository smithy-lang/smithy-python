#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
from asyncio import sleep
from dataclasses import dataclass, replace
from typing import Any

from .interfaces import ClientProtocol, Request, Response, ClientTransport
from .. import URI
from ..interfaces import TypedProperties, Endpoint
from ..interfaces.retries import RetryStrategy, RetryErrorInfo, RetryErrorType
from ..interceptors import (
    Interceptor,
    InputContext,
    RequestContext,
    OutputContext,
    ResponseContext,
)
from ..schemas import APIOperation
from ..shapes import ShapeID
from ..serializers import SerializeableShape
from ..deserializers import DeserializeableShape
from ..exceptions import SmithyRetryException, SmithyException
from ..types import PropertyKey


RETRY_ATTEMPTS = PropertyKey(key="retry_attempts", value_type=int)


_UNRESOLVED = URI(host="", path="/")
_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True, frozen=True)
class ClientCall[I: SerializeableShape, O: DeserializeableShape]:
    input: I
    operation: APIOperation[I, O]
    context: TypedProperties
    interceptor: Interceptor[I, O, Any, Any]
    retry_strategy: RetryStrategy
    retry_scope: str | None = None

    # TODO: fix up auth
    auth_scheme_resolver: Any
    supported_auth_schemes: dict[ShapeID, Any]

    # TODO: fix up endpoints
    endpoint_resolver: Any


# Auth params need to be standardized. It's a bit too crazy to have unique
# Types for each auth scheme. It's impossible to generate those without
# code gen, and even with code gen it's annoying. Instead, the context
# properties can carry anything the auth resolver needs beyond the basics,
# and auth schemes can come with interceptors or plugins that set those
# properties.
@dataclass(kw_only=True, frozen=True)
class AuthParams:
    protocol_id: ShapeID
    operation: APIOperation[Any, Any]
    context: TypedProperties


# Similarly to auth params, endpoint params need to be standardized and
# de-http-ified
@dataclass(kw_only=True, frozen=True)
class EndpointResolverParams[I: SerializeableShape]:
    operation: APIOperation[I, Any]
    input: I
    context: TypedProperties


class RequestPipeline[TRequest: Request, TResponse: Response]:
    protocol: ClientProtocol[TRequest, TResponse]
    transport: ClientTransport[TRequest, TResponse]

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
        _LOGGER.debug(
            'Making request for operation "%s" with parameters: %s',
            call.operation.schema.id.name,
            call.input,
        )
        output_context = await self._handle_execution(call)
        output_context = self._finalize_execution(call, output_context)

        if isinstance(output_context.response, Exception):
            e = output_context.response
            if not isinstance(e, SmithyException):
                raise SmithyException(e) from e
            raise e

        # TODO: wrap event streams
        # This needs to go on the protocols

        return output_context.response

    async def _handle_execution[I: SerializeableShape, O: DeserializeableShape](
        self, call: ClientCall[I, O]
    ) -> OutputContext[I, O, TRequest | None, TResponse | None]:
        try:
            interceptor = call.interceptor

            call.context[RETRY_ATTEMPTS] = 1

            input_context = InputContext(request=call.input, properties=call.context)

            # 2. Invoke ReadBeforeExecution
            interceptor.read_before_execution(input_context)

            # 3. Invoke ModifyBeforeSeraialization
            input_context = replace(
                input_context,
                request=interceptor.modify_before_serialization(input_context),
            )

            # 4. Invoke ReadBeforeSerialization
            interceptor.read_before_serialization(input_context)

            _LOGGER.debug("Serializing request for: %s", input_context.request)

            # 5. Serialize the input message into a transport request
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
            # 6. Invoke ReadAfterSerialization
            interceptor.read_after_serialization(request_context)

            # 7. Invoke ModifyBeforeRetryLoop
            request_context = replace(
                request_context,
                transport_request=interceptor.modify_before_retry_loop(request_context),
            )

            return await self._retry(call, request_context)
        except Exception as e:
            return OutputContext(
                request=request_context.request,
                response=e,
                transport_request=request_context.transport_request,
                transport_response=None,
                properties=request_context.properties,
            )

    async def _retry[I: SerializeableShape, O: DeserializeableShape](
        self, call: ClientCall[I, O], request_context: RequestContext[I, TRequest]
    ) -> OutputContext[I, O, TRequest | None, TResponse | None]:
        # 8. Invoke AcquireInitialRetryToken
        retry_strategy = call.retry_strategy
        retry_token = retry_strategy.acquire_initial_retry_token(
            token_scope=call.retry_scope
        )

        while True:
            # Even the first token can have a delay, so wait at the start of the retry loop.
            if retry_token.retry_delay:
                await sleep(retry_token.retry_delay)

            output_context = await self._handle_attempt(call, request_context)

            if isinstance(output_context.response, Exception):
                try:
                    retry_strategy.refresh_retry_token_for_retry(
                        token_to_renew=retry_token,
                        # TODO: classify
                        # Transports should be responsible for this classification IMO
                        error_info=RetryErrorInfo(
                            error_type=RetryErrorType.CLIENT_ERROR,
                        ),
                    )
                except SmithyRetryException:
                    raise output_context.response

                _LOGGER.debug(
                    "Retry needed. Attempting request #%s in %.4f seconds.",
                    retry_token.retry_count + 1,
                    retry_token.retry_delay,
                )

                call.context[RETRY_ATTEMPTS] += 1
                # TODO: seek
                # The Request interface needs to be updated with a retryable
                # method and a reset method
            else:
                retry_strategy.record_success(token=retry_token)
                return output_context

    async def _handle_attempt[I: SerializeableShape, O: DeserializeableShape](
        self, call: ClientCall[I, O], request_context: RequestContext[I, TRequest]
    ) -> OutputContext[I, O, TRequest, TResponse | None]:
        output_context: OutputContext[I, O, TRequest, TResponse | None]
        try:
            interceptor = call.interceptor
            # 8a. Invoke ReadBeforeAttempt
            interceptor.read_before_attempt(request_context)

            # TODO: resolve endpoint
            # This should probably go *before* auth despite SRA guidcance because its
            # result can affect auth. Musch of below is sort of wishful thinking for
            # a de-http-ified endpoint resolver
            endpoint_params = EndpointResolverParams(
                operation=call.operation,
                input=call.input,
                context=request_context.properties,
            )
            _LOGGER.debug("Calling endpoint resolver.")
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

            # 8b. Invoke ModifyBeforeSigning
            request_context = replace(
                request_context,
                transport_request=interceptor.modify_before_signing(request_context),
            )

            # 8c. Invoke ReadBeforeSigning
            interceptor.read_before_signing(request_context)

            # 8d. Resolve auth scheme
            # TODO: Actually sign
            # Most of this is wishful thinking for a not-yet-implemented
            # protocol agnostic auth resolver
            auth_params = AuthParams(
                protocol_id=self.protocol.id,
                operation=call.operation,
                context=request_context.properties,
            )
            auth = self._resolve_auth(call, auth_params)
            if auth is not None:
                option, scheme = auth
                identity_resolver = scheme.identity_resolver(context=call.context)
                identity = await identity_resolver.get_identity(
                    identity_properties=option.identity_properties
                )

                _LOGGER.debug("Request to sign: %s", request_context.transport_request)
                _LOGGER.debug("Signer properties: %s", option.signer_properties)

                request_context = replace(
                    request_context,
                    transport_request=await scheme.signer.sign(
                        request=request_context.transport_request,
                        identity=identity,
                        signing_properties=option.signer_properties,
                    ),
                )

            interceptor.read_after_signing(request_context)
            request_context = replace(
                request_context,
                transport_request=interceptor.modify_before_transmit(request_context),
            )
            interceptor.read_before_transmit(request_context)

            _LOGGER.debug("Sending request %s", request_context.transport_request)

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
                error_registry="foo",
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

    def _resolve_auth(
        self, call: ClientCall[Any, Any], params: AuthParams
    ) -> tuple[Any, Any] | None:
        auth_options: list[Any] = call.auth_scheme_resolver.resolve_auth_scheme(params)

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
