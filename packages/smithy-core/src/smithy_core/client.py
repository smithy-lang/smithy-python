#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
from collections.abc import Sequence
from copy import copy
from dataclasses import replace
from time import sleep
from typing import Any, cast

from . import URI
from .aio.client import AUTH_SCHEME, ClientCall
from .auth import AuthParams
from .deserializers import DeserializeableShape
from .endpoints import EndpointResolverParams
from .exceptions import (
    ClientTimeoutError,
    RetryError,
    SmithyError,
)
from .interceptors import (
    InputContext,
    OutputContext,
    RequestContext,
    ResponseContext,
)
from .interfaces import ClientProtocol, ClientTransport, Endpoint, Request, Response
from .interfaces.auth import AuthOption, AuthScheme
from .interfaces.retries import RetryStrategy
from .serializers import SerializeableShape
from .utils import seek

_UNRESOLVED = URI(host="", path="/")
_LOGGER = logging.getLogger(__name__)


class RequestPipeline[TRequest: Request, TResponse: Response]:
    """Invokes client operations synchronously."""

    protocol: ClientProtocol[TRequest, TResponse]
    transport: ClientTransport[TRequest, TResponse]

    def __init__(
        self,
        protocol: ClientProtocol[TRequest, TResponse],
        transport: ClientTransport[TRequest, TResponse],
    ) -> None:
        self.protocol = protocol
        self.transport = transport

    def __call__[I: SerializeableShape, O: DeserializeableShape](
        self, call: ClientCall[I, O], /
    ) -> O:
        """Invoke an operation synchronously.

        :param call: The operation to invoke and associated context.
        """
        output_context = self._handle_execution(call)
        output_context = self._finalize_execution(call, output_context)

        if isinstance(output_context.response, Exception):
            e = output_context.response
            if not isinstance(e, SmithyError):
                raise SmithyError(e) from e
            raise e

        return output_context.response  # type: ignore

    def _handle_execution[I: SerializeableShape, O: DeserializeableShape](
        self, call: ClientCall[I, O]
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

            return self._retry(call, request_context)
        except Exception as e:
            return OutputContext(
                request=request_context.request,
                response=e,
                transport_request=request_context.transport_request,
                transport_response=None,
                properties=request_context.properties,
            )

    def _retry[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: ClientCall[I, O],
        request_context: RequestContext[I, TRequest],
    ) -> OutputContext[I, O, TRequest | None, TResponse | None]:
        if not call.retryable():
            return self._handle_attempt(call, request_context)

        retry_strategy = cast(RetryStrategy, call.retry_strategy)
        retry_token = retry_strategy.acquire_initial_retry_token(
            token_scope=call.retry_scope
        )

        while True:
            if retry_token.retry_delay:
                sleep(retry_token.retry_delay)

            output_context = self._handle_attempt(
                call,
                replace(
                    request_context,
                    transport_request=copy(request_context.transport_request),
                ),
            )

            if isinstance(output_context.response, Exception):
                try:
                    retry_token = retry_strategy.refresh_retry_token_for_retry(
                        token_to_renew=retry_token,
                        error=output_context.response,
                    )
                except RetryError as retry_error:
                    # Long-polling operations back off even when the retry quota is
                    # exhausted; the strategy surfaces that delay here.
                    if (
                        call.operation.long_polling
                        and retry_error.retry_after is not None
                    ):
                        sleep(retry_error.retry_after)
                    raise output_context.response

                seek(request_context.transport_request.body, 0)
            else:
                retry_strategy.record_success(token=retry_token)
                return output_context

    def _handle_attempt[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: ClientCall[I, O],
        request_context: RequestContext[I, TRequest],
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
            endpoint: Endpoint = call.endpoint_resolver.resolve_endpoint(
                endpoint_params
            )

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
                request_context.properties[AUTH_SCHEME] = cast("Any", scheme)
                identity_resolver = scheme.identity_resolver(context=call.context)

                identity_properties = scheme.identity_properties(
                    context=request_context.properties
                )
                identity_properties.update(option.identity_properties)

                identity = identity_resolver.get_identity(
                    properties=identity_properties
                )

                signer_properties = scheme.signer_properties(
                    context=request_context.properties
                )
                signer_properties.update(option.identity_properties)

                signer = scheme.signer()
                request_context = replace(
                    request_context,
                    transport_request=signer.sign(
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

            try:
                transport_response = self.transport.send(
                    request_context.transport_request
                )
            except Exception as e:
                if isinstance(e, self.transport.TIMEOUT_EXCEPTIONS):
                    raise ClientTimeoutError(message="A timeout error occurred.") from e
                raise

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

            output = self.protocol.deserialize_response(
                operation=call.operation,
                request=response_context.transport_request,
                response=response_context.transport_response,
                error_registry=call.operation.error_registry,
                context=response_context.properties,
            )

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
                # ClientCall pins the async AuthScheme statically; a sync client
                # populates it with sync schemes, so narrow at the boundary.
                return option, cast("AuthScheme[TRequest, Any, Any, Any]", scheme)

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
        except Exception as e:
            output_context = replace(output_context, response=e)

        try:
            interceptor.read_after_execution(output_context)
        except Exception as e:
            output_context = replace(output_context, response=e)

        return output_context
