#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar, Self

from ._client import OPERATION
from ._client import ClientBase as _ClientBase
from ._pipeline import RequestPipelineBase, is_retryable
from .deserializers import DeserializeableShape
from .exceptions import ResourceLifecycleError
from .interceptors import Interceptor, RequestContext
from .interfaces import (
    ClientProtocol,
    ClientTransport,
    EndpointResolver,
    TypedProperties,
)
from .interfaces.auth import AuthScheme, AuthSchemeResolver
from .interfaces.retries import RetryStrategy
from .program import run_program
from .schemas import APIOperation
from .serializers import SerializeableShape
from .shapes import ShapeID
from .types import PropertyKey
from .utils import read_streaming_blob

__all__ = ["AUTH_SCHEME", "OPERATION", "Client", "ClientCall", "RequestPipeline"]

AUTH_SCHEME = PropertyKey(key="auth_scheme", value_type=AuthScheme[Any, Any, Any, Any])
"""Property key for the auth scheme selected for the call."""


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

    supported_auth_schemes: dict[ShapeID, Any]
    """The supported auth schemes for the operation, sync or async to match the
    pipeline."""

    endpoint_resolver: EndpointResolver | Any
    """The endpoint resolver for the operation. Async clients also accept an
    ``AsyncEndpointResolver``."""

    retry_strategy: RetryStrategy
    """The retry strategy to use for the operation."""

    retry_scope: str | None = None
    """The retry scope for the operation."""

    def retryable(self) -> bool:
        """Whether the operation can be retried.

        Operations with an input event stream are never retried. A request for any
        other operation is retried only if its body can be rewound to where it started.
        """
        return is_retryable(self.operation)


class RequestPipeline[TRequest, TResponse](RequestPipelineBase[TRequest, TResponse]):
    """Invokes client operations synchronously."""

    protocol: ClientProtocol[TRequest, TResponse]
    """The protocol to use to serialize the request and deserialize the response."""

    transport: ClientTransport[TRequest, TResponse]
    """The transport to use to send the request and receive the response."""

    _logger: ClassVar[logging.Logger] = logging.getLogger("smithy_core.client")

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

    def _read_body(self, body: Any) -> bytes:
        return read_streaming_blob(body)

    def _sleep(self, delay: float) -> None:
        time.sleep(delay)

    def _transmit(
        self, request_context: RequestContext[Any, TRequest], request_future: None
    ) -> TResponse:
        return self.transport.send(request_context.transport_request)


class Client[C](_ClientBase[C]):
    """Shared sync client machinery: lifecycle, setup gating, and call dispatch.

    Generated clients subclass this with their config type and supply
    ``_new_config``, plus ``_post_setup`` when setup needs more than plugins.
    """

    _pipeline_type = RequestPipeline
    _call_type = ClientCall

    def __init__(
        self,
        config: C | None = None,
        plugins: list[Callable[[C], None]] | None = None,
    ) -> None:
        super().__init__(config, plugins)
        self._derive_lock = threading.Lock()

    def __enter__(self) -> Self:
        if self._closed:
            raise ResourceLifecycleError("Cannot enter a client that has been closed.")
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close this client and any resources held by its transport."""
        if self._closed:
            return
        with self._derive_lock:
            run_program(self._close())

    def _ensure_setup(self) -> C:
        if not self._setup_done:
            with self._derive_lock:
                return run_program(self._setup())
        return self._config

    def _invoke[I: SerializeableShape, O: DeserializeableShape](
        self,
        input: I | None,
        operation: APIOperation[I, O],
        default_plugins: list[Callable[[C], None]],
        plugins: list[Callable[[C], None]] | None,
    ) -> O:
        pipeline, call = self._prepare_call(input, operation, default_plugins, plugins)
        return pipeline(call)

    def _prepare_call[I: SerializeableShape, O: DeserializeableShape](
        self,
        input: I | None,
        operation: APIOperation[I, O],
        default_plugins: list[Callable[[C], None]],
        plugins: list[Callable[[C], None]] | None,
    ) -> tuple[RequestPipeline[Any, Any], ClientCall[I, O]]:
        self._raise_if_closed()
        config = self._ensure_setup()
        return run_program(
            self._prepare(config, input, operation, default_plugins, plugins)
        )
