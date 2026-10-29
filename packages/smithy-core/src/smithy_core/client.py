#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Self

from ._pipeline import RequestPipelineBase, is_retryable
from ._program import run_program
from .deserializers import DeserializeableShape
from .interceptors import Interceptor, InterceptorChain, RequestContext
from .interfaces import (
    ClientProtocol,
    ClientTransport,
    EndpointResolver,
    TypedProperties,
)
from .interfaces.auth import AuthScheme, AuthSchemeResolver
from .interfaces.retries import RetryStrategy
from .retries import AdaptiveRetryStrategy, RetryStrategyResolver
from .schemas import APIOperation
from .serializers import SerializeableShape
from .shapes import ShapeID
from .types import PropertyKey
from .types import TypedProperties as _TypedProperties

__all__ = ["AUTH_SCHEME", "Client", "ClientCall", "RequestPipeline"]

AUTH_SCHEME = PropertyKey(key="auth_scheme", value_type=AuthScheme[Any, Any, Any, Any])


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
        """Whether the operation can be retried."""
        return is_retryable(self.operation)


class RequestPipeline[TRequest, TResponse](RequestPipelineBase[TRequest, TResponse]):
    """Invokes client operations synchronously."""

    protocol: ClientProtocol[TRequest, TResponse]
    """The protocol to use to serialize the request and deserialize the response."""

    transport: ClientTransport[TRequest, TResponse]
    """The transport to use to send the request and receive the response."""

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
        output, _ = run_program(self._execute(call, None))
        return output

    def _sleep(self, delay: float) -> None:
        time.sleep(delay)

    def _transmit(
        self, request_context: RequestContext[Any, TRequest], request_future: None
    ) -> TResponse:
        return self.transport.send(request_context.transport_request)

    def _adaptive_strategy(
        self, retry_strategy: RetryStrategy
    ) -> AdaptiveRetryStrategy | None:
        if isinstance(retry_strategy, AdaptiveRetryStrategy):
            return retry_strategy
        return None


class Client:
    """Shared sync client machinery: lifecycle, setup gating, and call dispatch."""

    def __init__(self) -> None:
        self._derive_lock = threading.Lock()
        self._setup_done = False
        self._closed = False
        self._transport: ClientTransport[Any, Any] | None = None
        self._retry_strategy_resolver = RetryStrategyResolver()

    def _build_call[I: SerializeableShape, O: DeserializeableShape](
        self,
        input: I,
        operation: APIOperation[I, O],
        *,
        config: Any,
        retry_strategy: RetryStrategy,
    ) -> tuple[RequestPipeline[Any, Any], ClientCall[I, O]]:
        """Build the pipeline and call from a resolved config and retry strategy."""
        pipeline = RequestPipeline(protocol=config.protocol, transport=config.transport)
        call = ClientCall(
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

    def close(self) -> None:
        """Close this client and any resources held by its transport."""
        if self._closed:
            return
        with self._derive_lock:
            if self._closed:
                return
            self._closed = True
            if self._setup_done and self._transport is not None:
                if (close := getattr(self._transport, "close", None)) is not None:
                    close()

    def __enter__(self) -> Self:
        if self._closed:
            raise RuntimeError("Cannot enter a client that has been closed.")
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()
