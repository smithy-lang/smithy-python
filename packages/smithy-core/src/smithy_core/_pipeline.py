#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""The request pipeline shared by the sync and async clients.

Every step is a :py:data:`~smithy_core._program.Program`, so the sync pipeline and the
async pipeline run identical logic and differ only in how effects are driven and in
the few hooks below.
"""

import logging
from collections.abc import Mapping, Sequence
from copy import copy
from dataclasses import replace
from typing import Any, Protocol

from . import URI
from ._program import Program
from .auth import AuthParams
from .deserializers import DeserializeableShape
from .endpoints import EndpointResolverParams
from .exceptions import ClientTimeoutError, RetryError, SmithyError
from .interceptors import (
    InputContext,
    Interceptor,
    OutputContext,
    RequestContext,
    ResponseContext,
)
from .interfaces import Endpoint, TypedProperties
from .interfaces.auth import AuthOption, AuthSchemeResolver
from .schemas import APIOperation
from .serializers import SerializeableShape
from .shapes import ShapeID, ShapeType
from .types import PropertyKey

__all__ = ["AUTH_SCHEME", "CallLike", "RequestPipelineBase", "is_retryable"]

AUTH_SCHEME = PropertyKey(key="auth_scheme", value_type=object)
"""The auth scheme selected for a call. Exposed with a mode-specific type by each
client module."""

_UNRESOLVED = URI(host="", path="/")
_LOGGER = logging.getLogger("smithy_core.aio.client")


class CallLike[I: SerializeableShape, O: DeserializeableShape](Protocol):
    """The fields of a client call that the shared pipeline reads."""

    @property
    def input(self) -> I: ...
    @property
    def operation(self) -> APIOperation[I, O]: ...
    @property
    def context(self) -> TypedProperties: ...
    @property
    def interceptor(self) -> Interceptor[I, O, Any, Any]: ...
    @property
    def auth_scheme_resolver(self) -> AuthSchemeResolver: ...
    @property
    def supported_auth_schemes(self) -> Mapping[ShapeID, Any]: ...
    @property
    def endpoint_resolver(self) -> Any: ...
    @property
    def retry_strategy(self) -> Any: ...
    @property
    def retry_scope(self) -> str | None: ...
    def retryable(self) -> bool: ...


def is_retryable(operation: APIOperation[Any, Any]) -> bool:
    """Whether an operation can be retried.

    Operations with an input event stream are never retried. A request for any other
    operation is retried only if its body can be rewound to where it started.
    """
    member = operation.input_stream_member
    return member is None or member.shape_type is not ShapeType.UNION


def _seek(stream: Any, offset: int, whence: int = 0) -> Any:
    """Seek a stream, returning the stream's own (possibly awaitable) result."""
    if (seekable := getattr(stream, "seekable", None)) is not None and not seekable():
        return None
    if (seek := getattr(stream, "seek", None)) is not None:
        return seek(offset, whence)
    return None


def _rewind_position(body: Any) -> Program[int | None]:
    """Find where a request body is rewound to before it's resent.

    :returns: The body's current position, or None if it can't be rewound.
    """
    if body is None or isinstance(body, bytes | bytearray):
        return 0
    try:
        return (yield lambda: _seek(body, 0, 1))
    except (OSError, ValueError, NotImplementedError):
        return None


class RequestPipelineBase[TRequest, TResponse]:
    """Mode-neutral request pipeline.

    Subclasses supply the protocol and transport and implement the hooks that
    differ between sync and async execution.
    """

    protocol: Any
    transport: Any

    def _sleep(self, delay: float) -> Any:
        """Effect: wait ``delay`` seconds."""
        raise NotImplementedError

    def _transmit(
        self, request_context: RequestContext[Any, TRequest], request_future: Any
    ) -> Any:
        """Effect: send a request over the transport."""
        raise NotImplementedError

    def _adaptive_strategy(self, retry_strategy: Any) -> Any:
        """Return the retry strategy if it rate limits requests, else None."""
        raise NotImplementedError

    def _fail_request_future(self, request_future: Any, error: Exception) -> None:
        """Report a failure that happened before the request was sent."""

    def _execute[I: SerializeableShape, O: DeserializeableShape](
        self, call: CallLike[I, O], request_future: Any
    ) -> Program[tuple[O, OutputContext[I, O, TRequest, TResponse]]]:
        _LOGGER.debug(
            'Making request for operation "%s" with parameters: %s',
            call.operation.schema.id.name,
            call.input,
        )
        output_context = yield from self._handle_execution(call, request_future)
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

    def _handle_execution[I: SerializeableShape, O: DeserializeableShape](
        self, call: CallLike[I, O], request_future: Any
    ) -> Program[OutputContext[I, O, TRequest | None, TResponse | None]]:
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

            transport_request: TRequest = self.protocol.serialize_request(
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

            return (yield from self._retry(call, request_context, request_future))
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
        call: CallLike[I, O],
        request_context: RequestContext[I, TRequest],
        request_future: Any,
    ) -> Program[OutputContext[I, O, TRequest | None, TResponse | None]]:
        body = getattr(request_context.transport_request, "body", None)
        if (
            not call.retryable()
            or (start := (yield from _rewind_position(body))) is None
        ):
            return (
                yield from self._send_with_rate_limiting(
                    call, request_context, request_future
                )
            )

        retry_strategy = call.retry_strategy
        retry_token = yield lambda: retry_strategy.acquire_initial_retry_token(
            token_scope=call.retry_scope
        )

        last_output_context: OutputContext[I, O, TRequest, TResponse | None] | None = (
            None
        )
        while True:
            if retry_token.retry_delay:
                delay = retry_token.retry_delay
                yield lambda: self._sleep(delay)

            try:
                output_context = yield from self._send_with_rate_limiting(
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
                error = output_context.response
                token = retry_token
                try:
                    retry_token = (
                        yield lambda: retry_strategy.refresh_retry_token_for_retry(
                            token_to_renew=token, error=error
                        )
                    )
                except RetryError as retry_error:
                    # Long-polling operations back off even when the retry quota
                    # is exhausted; the strategy surfaces that delay here.
                    if (
                        call.operation.long_polling
                        and (retry_after := retry_error.retry_after) is not None
                    ):
                        yield lambda: self._sleep(retry_after)
                    # Keeps the final attempt's response, so throttling and 5xx
                    # failures still carry a request ID when _execute raises.
                    return output_context

                _LOGGER.debug(
                    "Retry needed. Attempting request #%s in %.4f seconds.",
                    retry_token.retry_count + 1,
                    retry_token.retry_delay,
                )

                try:
                    yield lambda: _seek(body, start)
                except (OSError, ValueError, NotImplementedError) as e:
                    error.add_note(f"Retry not attempted: {e}")
                    return output_context
            else:
                token = retry_token
                yield lambda: retry_strategy.record_success(token=token)
                return output_context

    def _send_with_rate_limiting[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: CallLike[I, O],
        request_context: RequestContext[I, TRequest],
        request_future: Any,
    ) -> Program[OutputContext[I, O, TRequest, TResponse | None]]:
        """Send a single attempt, applying client-side rate limiting (adaptive only).

        Every attempt, retryable or not, acquires a send token before it is sent. Once a
        response comes back from the service, the rate limiter is updated with it.
        """
        adaptive = self._adaptive_strategy(call.retry_strategy)
        if adaptive is not None:
            try:
                yield adaptive.acquire_from_token_bucket
            except Exception as e:
                self._fail_request_future(request_future, e)
                raise

        output_context = yield from self._handle_attempt(
            call, request_context, request_future
        )

        if output_context.transport_response is None or adaptive is None:
            # Failed before sending, or the connection failed: not a service response
            return output_context

        if isinstance(output_context.response, Exception):
            is_throttling = adaptive.is_throttling_error(output_context.response)
            yield lambda: adaptive.rate_limiter.after_receiving_response(is_throttling)
        else:
            yield lambda: adaptive.rate_limiter.after_receiving_response(
                throttling_error=False
            )
        return output_context

    def _handle_attempt[I: SerializeableShape, O: DeserializeableShape](
        self,
        call: CallLike[I, O],
        request_context: RequestContext[I, TRequest],
        request_future: Any,
    ) -> Program[OutputContext[I, O, TRequest, TResponse | None]]:
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
            endpoint: Endpoint = yield lambda: call.endpoint_resolver.resolve_endpoint(
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

                identity = yield lambda: identity_resolver.get_identity(
                    properties=identity_properties
                )

                signer_properties = scheme.signer_properties(
                    context=request_context.properties
                )
                signer_properties.update(option.signer_properties)
                _LOGGER.debug("Request to sign: %s", request_context.transport_request)
                _LOGGER.debug("Signer properties: %s", signer_properties)

                signer = scheme.signer()
                unsigned = request_context.transport_request
                signed: TRequest = yield lambda: signer.sign(
                    request=unsigned,
                    identity=identity,
                    properties=signer_properties,
                )
                request_context = replace(request_context, transport_request=signed)

            interceptor.read_after_signing(request_context)
            request_context = replace(
                request_context,
                transport_request=interceptor.modify_before_transmit(request_context),
            )
            interceptor.read_before_transmit(request_context)

            _LOGGER.debug("Sending request %s", request_context.transport_request)

            to_send = request_context
            try:
                transport_response = yield lambda: self._transmit(
                    to_send, request_future
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

            received = response_context
            output = yield lambda: self.protocol.deserialize_response(
                operation=call.operation,
                request=received.transport_request,
                response=received.transport_response,
                error_registry=call.operation.error_registry,
                context=received.properties,
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
        self, call: CallLike[Any, Any], params: AuthParams[I, O]
    ) -> tuple[AuthOption, Any] | None:
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
        call: CallLike[I, O],
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
        call: CallLike[I, O],
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
