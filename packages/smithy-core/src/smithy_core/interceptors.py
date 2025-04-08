#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from .deserializers import DeserializeableShape
from .interfaces import TypedProperties
from .serializers import SerializeableShape


@dataclass(kw_only=True, frozen=True, slots=True)
class InputContext[Request: SerializeableShape]:
    request: Request
    """The modeled request for the operation being invoked."""

    properties: TypedProperties
    """A typed context property bag."""


@dataclass(kw_only=True, frozen=True, slots=True)
class RequestContext[Request: SerializeableShape, TransportRequest](
    InputContext[Request]
):
    transport_request: TransportRequest
    """The transmittable request for the operation being invoked."""


@dataclass(kw_only=True, frozen=True, slots=True)
class ResponseContext[Request: SerializeableShape, TransportRequest, TransportResponse](
    RequestContext[Request, TransportRequest]
):
    transport_response: TransportResponse
    """The transmitted response for the operation being invoked."""


@dataclass(kw_only=True, frozen=True, slots=True)
class OutputContext[
    Request: SerializeableShape,
    Response: DeserializeableShape,
    TransportRequest,
    TransportResponse,
](ResponseContext[Request, TransportRequest, TransportResponse]):
    response: Response | Exception
    """The modeled response for the operation being invoked."""


class Interceptor[
    Request: SerializeableShape,
    Response: DeserializeableShape,
    TransportRequest,
    TransportResponse,
]:
    """Allows injecting code into the SDK's request execution pipeline.

    Terminology:

    * execution - An execution is one end-to-end invocation against a client.
    * attempt - An attempt is an attempt at performing an execution. By default,
        executions are retried multiple times based on the client's retry strategy.
    * hook - A hook is a single method on the interceptor, allowing injection of code
        into a specific part of the SDK's request execution pipeline. Hooks are either
        "read" hooks, which make it possible to read in-flight request or response
        messages, or "read/write" hooks, which make it possible to modify in-flight
        requests or responses.
    """

    def read_before_execution(self, context: InputContext[Request]) -> None:
        """A hook called at the start of an execution, before the SDK does anything
        else.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will always be called once per execution. The duration between invocation
        of this hook and `read_after_execution` is very close to full duration of the
        execution.

        The `request` of the context will always be available. Other static properties
        will be None.

        Exceptions thrown by this hook will be stored until all interceptors have had
        their `read_before_execution` invoked. Other hooks will then be skipped and
        execution will jump to `modify_before_completion` with the thrown exception as
        the `response`. If multiple `read_before_execution` methods throw exceptions,
        the latest will be used and earlier ones will be logged and dropped.
        """

    def modify_before_serialization(self, context: InputContext[Request]) -> Request:
        """A hook called before the request is serialized into a transport request.

        This method has the ability to modify and return a new request of the same
        type.

        This will ALWAYS be called once per execution, except when a failure occurs
        earlier in the request pipeline.

        The `request` of the context will always be available. This `request` may have
        been modified by earlier `modify_before_serialization` hooks, and may be
        modified further by later hooks. Other static properites will be None.

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_completion` with the thrown exception as the `response`.

        The request returned by this hook MUST be the same type of request
        message passed into this hook. If not, an exception will immediately occur.
        """
        return context.request

    def read_before_serialization(self, context: InputContext[Request]) -> None:
        """A hook called before the input message is serialized into a transport
        request.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will always be called once per execution, except when a failure occurs
        earlier in the request pipeline. The duration between invocation of this hook
        and `read_after_serialization` is very close to the amount of time spent
        marshalling the request.

        The `request` of the context will always be available. Other static properties
        will be None.

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_completion` with the thrown exception as the `response`.
        """

    def read_after_serialization(
        self, context: RequestContext[Request, TransportRequest]
    ) -> None:
        """A hook called after the input message is serialized into a transport request.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will always be called once per execution, except when a failure occurs
        earlier in the request pipeline. The duration between
        `read_before_serialization` and the invocation of this hook is very close to
        the amount of time spent serializing the request.

        The `request` and `transport_request` of the context will always be available.
        Other static properties will be None.

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_completion` with the thrown exception as the `response`.
        """

    def modify_before_retry_loop(
        self, context: RequestContext[Request, TransportRequest]
    ) -> TransportRequest:
        """A hook called before the retry loop is entered.

        This method has the ability to modify and return a new transport request of the
        same type.

        This will always be called once per execution, except when a failure occurs
        earlier in the request pipeline.

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_completion` with the thrown exception as the `response`.

        The transport request returned by this hook MUST be the same type of request
        passed into this hook. If not, an exception will immediately occur.
        """
        return context.transport_request

    def read_before_attempt(
        self, context: RequestContext[Request, TransportRequest]
    ) -> None:
        """A hook called before each attempt at sending the transport request to the
        service.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will always be called once per attempt, except when a failure occurs
        earlier in the request pipeline. This method will be called multiple times in
        the event of retries.

        The `request` and `transport_request` of the context will always be available.
        Other static properties will be None. In the event of retries, the context will
        not include changes made in previous attempts (e.g. by request signers or other
        interceptors).

        Exceptions thrown by this hook will be stored until all interceptors have had
        their `read_before_attempt` invoked. Other hooks will then be skipped and
        execution will jump to `modify_before_attempt_completion` with the thrown
        exception as the `response` If multiple `read_before_attempt` methods throw
        exceptions, the latest will be used and earlier ones will be logged and dropped.
        """

    def modify_before_signing(
        self, context: RequestContext[Request, TransportRequest]
    ) -> TransportRequest:
        """A hook called before the transport request is signed.

        This method has the ability to modify and return a new transport request of the
        same type.

        This will always be called once per attempt, except when a failure occurs
        earlier in the request pipeline. This method will be called multiple times in
        the event of retries.

        The `request` and `transport_request` of the context will always be available.
        Other static properties will be None. The `transport_request` may have been
        modified by earlier `modify_before_signing` hooks, and may be modified further
        by later hooks. In the event of retries, the context will not include changes
        made in previous attempts (e.g. by request signers or other interceptors).

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_attempt_completion` with the thrown exception as the `response`.

        The transport request returned by this hook MUST be the same type of request
        passed into this hook. If not, an exception will immediately occur.
        """
        return context.transport_request

    def read_before_signing(
        self, context: RequestContext[Request, TransportRequest]
    ) -> None:
        """A hook called before the transport request is signed.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will always be called once per attempt, except when a failure occurs
        earlier in the request pipeline. This method may be called multiple times in
        the event of retries. The duration between invocation of this hook and
        `read_after_signing` is very close to the amount of time spent signing the
        request.

        The `request` and `transport_request` of the context will always be available.
        Other static properties will be None. In the event of retries, the context will
        not include changes made in previous attempts (e.g. by request signers or other
        interceptors).

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_attempt_completion` with the thrown exception as the `response`.
        """

    def read_after_signing(
        self, context: RequestContext[Request, TransportRequest]
    ) -> None:
        """A hook called after the transport request is signed.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will always be called once per attempt, except when a failure occurs
        earlier in the request pipeline. This method may be called multiple times in
        the event of retries. The duration between `read_before_signing` and the
        invocation of this hook is very close to the amount of time spent signing the
        request.

        The `request` and `transport_request` of the context will always be available.
        Other static properties will be None. In the event of retries, the context will
        not include changes made in previous attempts (e.g. by request signers or other
        interceptors).

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_attempt_completion` with the thrown exception as the `response`.
        """

    def modify_before_transmit(
        self, context: RequestContext[Request, TransportRequest]
    ) -> TransportRequest:
        """A hook called before the transport request is sent to the service.

        This method has the ability to modify and return a new transport request of the
        same type.

        This will always be called once per attempt, except when a failure occurs
        earlier in the request pipeline. This method may be called multiple times in
        the event of retries.

        The `request` and `transport_request` of the context will always be available.
        Other static properties will be None. The `transport_request` may have been
        modified by earlier `modify_before_signing` hooks, and may be modified further
        by later hooks. In the event of retries, the context will not include changes
        made in previous attempts (e.g. by request signers or other interceptors).

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_attempt_completion` with the thrown exception as the `response`.

        The transport request returned by this hook MUST be the same type of request
        passed into this hook. If not, an exception will immediately occur.
        """
        return context.transport_request

    def read_before_transmit(
        self, context: RequestContext[Request, TransportRequest]
    ) -> None:
        """A hook called before the transport request is sent to the service.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will always be called once per attempt, except when a failure occurs
        earlier in the request pipeline. This method may be called multiple times in
        the event of retries. The duration between invocation of this hook and
        `read_after_transmit` is very close to the amount of time spent communicating
        with the service. Depending on the protocol, the duration may not include the
        time spent reading the response data.

        The `request` and `transport_request` of the context will always be available.
        Other static properties will be None. In the event of retries, the context will
        not include changes made in previous attempts (e.g. by request signers or other
        interceptors).

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_attempt_completion` with the thrown exception as the `response`.
        """

    def read_after_transmit(
        self,
        context: ResponseContext[Request, TransportRequest, TransportResponse],
    ) -> None:
        """A hook called after the transport request is sent to the service and a
        transport response is received.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will always be called once per attempt, except when a failure occurs
        earlier in the request pipeline. This method may be called multiple times in
        the event of retries. The duration between `read_before_transmit` and the
        invocation of this hook is very close to the amount of time spent communicating
        with the service. Depending on the protocol, the duration may not include the
        time spent reading the response data.

        The `request`, `transport_request`, and `transport_response` of the context
        will always be available. Other static properties will be None. In the event of
        retries, the context will not include changes made in previous attempts (e.g.
        by request signers or other interceptors).

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_attempt_completion` with the thrown exception as the `response`.
        """

    def modify_before_deserialization(
        self,
        context: ResponseContext[Request, TransportRequest, TransportResponse],
    ) -> TransportResponse:
        """A hook called before the transport response is deserialized.

        This method has the ability to modify and return a new transport response of the
        same type.

        This will always be called once per attempt, except when a failure occurs
        earlier in the request pipeline. This method may be called multiple times in
        the event of retries.

        The `request`, `transport_request`, and `transport_response` of the context
        will always be available. Other static properties will be None. In the event of
        retries, the context will not include changes made in previous attempts (e.g.
        by request signers or other interceptors). The `transport_response` may have
        been modified by earlier `modify_before_deserialization` hooks, and may be
        modified further by later hooks. In the event of retries, the context will not
        include changes made in previous attempts (e.g. by request signers or other
        interceptors).

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_attempt_completion` with the thrown exception as the `response`.

        The transport response returned by this hook MUST be the same type of
        response passed into this hook. If not, an exception will immediately occur.
        """
        return context.transport_response

    def read_before_deserialization(
        self,
        context: ResponseContext[Request, TransportRequest, TransportResponse],
    ) -> None:
        """A hook called before the transport response is deserialized.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will always be called once per attempt, except when a failure occurs
        earlier in the request pipeline. This method may be called multiple times in
        the event of retries. The duration between invocation of this hook and
        `read_after_deserialization` is very close to the amount of time spent
        deserializing the service response. Depending on the protocol and operation,
        the duration may include the time spent downloading the response data.

        The `request`, `transport_request`, and `transport_response` of the context
        will always be available. Other static properties will be None. In the event of
        retries, the context will not include changes made in previous attempts (e.g.
        by request signers or other interceptors).

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_attempt_completion` with the thrown exception as the `response`.
        """

    def read_after_deserialization(
        self,
        context: OutputContext[Request, Response, TransportRequest, TransportResponse],
    ) -> None:
        """A hook called after the transport response is deserialized.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will always be called once per attempt, except when a failure occurs
        earlier in the request pipeline. This method may be called multiple times in
        the event of retries. The duration between `read_before_deserialization`
        and the invocation of this hook is very close to the amount of time spent
        deserializing the service response. Depending on the protocol and operation,
        the duration may include the time spent downloading the response data.

        The `request`, `response`, `transport_request`, and `transport_response` of the
        context will always be available. In the event of retries, the context will not
        include changes made in previous attempts (e.g. by request signers or other
        interceptors).

        If exceptions are thrown by this hook, execution will jump to
        `modify_before_attempt_completion` with the thrown exception as the `response`.
        """

    def modify_before_attempt_completion(
        self,
        context: OutputContext[
            Request, Response, TransportRequest, TransportResponse | None
        ],
    ) -> Response | Exception:
        """A hook called when an attempt is completed.

        This method has the ability to modify and return a new output message or
        exception matching the currently-executing operation.

        This will ALWAYS be called once per attempt, except when a failure occurs
        before `read_before_attempt`. This method may be called multiple times in the
        event of retries.

        The `request`, `response`, and `transport_request` of the context will always
        be available. The `transport_response` will be available if a response was
        received by the service for this attempt. In the event of retries, the context
        will not include changes made in previous attempts (e.g. by request signers or
        other interceptors).

        If exceptions are thrown by this hook, execution will jump to
        `read_after_attempt` with  the thrown exception as the `response`.

        Any output returned by this hook MUST match the operation being invoked. Any
        exception type can be returned, replacing the `response` currently in the
        context.
        """
        return context.response

    def read_after_attempt(
        self,
        context: OutputContext[
            Request, Response, TransportRequest, TransportResponse | None
        ],
    ) -> None:
        """A hook called when an attempt is completed.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will ALWAYS be called once per attempt, as long as `read_before_attempt`
        has been executed.

        The `request`, `response`, and `transport_request` of the context will always
        be available. The `transport_response` will be available if a response was
        received by the service for this attempt. In the event of retries, the context
        will not include changes made in previous attempts (e.g. by request signers or
        other interceptors).

        Exceptions thrown by this hook will be stored until all interceptors have had
        their `read_after_attempt` invoked. If multiple `read_after_attempt` methods
        throw exceptions, the latest will be used and earlier ones will be logged and
        dropped. If the retry strategy determines that the execution is retryable,
        execution will then jump to `read_before_attempt`. Otherwise, execution will
        jump to `modify_before_completion` with the thrown exception as the `response`.
        """

    def modify_before_completion(
        self,
        context: OutputContext[
            Request, Response, TransportRequest | None, TransportResponse | None
        ],
    ) -> Response | Exception:
        """A hook called when an execution is completed.

        This method has the ability to modify and return a new output message or
        exception matching the currently-executing operation.

        This will always be called once per execution.

        The `request` and `response` of the context will always be available. The
        `transport_request` and `transport_response` will be available if the execution
        proceeded far enough for them to be generated.

        If exceptions are thrown by this hook, execution will jump to
        `read_after_execution` with the thrown exception as the `response`.

        Any output returned by this hook MUST match the operation being invoked. Any
        exception type can be returned, replacing the `response` currently in the context.
        """
        return context.response

    def read_after_execution(
        self,
        context: OutputContext[
            Request, Response, TransportRequest | None, TransportResponse | None
        ],
    ) -> None:
        """A hook called when an execution is completed.

        Implementations MUST NOT modify the `request`, `response`, `transport_request`,
        or `transport_response` in this hook.

        This will always be called once per execution. The duration between
        `read_before_execution` and the invocation of this hook is very close to the
        full duration of the execution.

        The `request` and `response` of the context will always be available. The
        `transport_request` and `transport_response` will be available if the execution
        proceeded far enough for them to be generated.

        Exceptions thrown by this hook will be stored until all interceptors have had
        their `read_after_execution` invoked. The exception will then be treated as the
        final response. If multiple `read_after_execution` methods throw exceptions,
        the latest will be used and earlier ones will be logged and dropped.
        """


AnyInterceptor = Interceptor[Any, Any, Any, Any]


class InterceptorChain(AnyInterceptor):
    """An interceptor that contains an ordered list of delegate interceptors.

    This is primarily intended for use within the client itself.
    """

    def __init__(self, chain: Sequence[AnyInterceptor]) -> None:
        """Construct an InterceptorChain.

        :param chain: The ordered interceptors to chain together.
        """
        self._chain = tuple(chain)

    def __repr__(self) -> str:
        return f"InterceptorChain(chain={self._chain!r})"

    def read_before_execution(self, context: InputContext[Any]) -> None:
        for interceptor in self._chain:
            interceptor.read_before_execution(context)

    def modify_before_serialization(self, context: InputContext[Any]) -> Any:
        request = context.request
        for interceptor in self._chain:
            request = interceptor.modify_before_serialization(context)
        return request

    def read_before_serialization(self, context: InputContext[Any]) -> None:
        for interceptor in self._chain:
            interceptor.read_before_serialization(context)

    def read_after_serialization(self, context: RequestContext[Any, Any]) -> None:
        for interceptor in self._chain:
            interceptor.read_after_serialization(context)

    def modify_before_retry_loop(self, context: RequestContext[Any, Any]) -> Any:
        transport_request = context.transport_request
        for interceptor in self._chain:
            transport_request = interceptor.modify_before_retry_loop(context)
        return transport_request

    def read_before_attempt(self, context: RequestContext[Any, Any]) -> None:
        for interceptor in self._chain:
            interceptor.read_before_attempt(context)

    def modify_before_signing(self, context: RequestContext[Any, Any]) -> Any:
        transport_request = context.transport_request
        for interceptor in self._chain:
            transport_request = interceptor.modify_before_signing(context)
        return transport_request

    def read_before_signing(self, context: RequestContext[Any, Any]) -> None:
        for interceptor in self._chain:
            interceptor.read_before_signing(context)

    def read_after_signing(self, context: RequestContext[Any, Any]) -> None:
        for interceptor in self._chain:
            interceptor.read_after_signing(context)

    def modify_before_transmit(self, context: RequestContext[Any, Any]) -> Any:
        transport_request = context.transport_request
        for interceptor in self._chain:
            transport_request = interceptor.modify_before_transmit(context)
        return transport_request

    def read_before_transmit(self, context: RequestContext[Any, Any]) -> None:
        for interceptor in self._chain:
            interceptor.read_before_transmit(context)

    def read_after_transmit(self, context: ResponseContext[Any, Any, Any]) -> None:
        for interceptor in self._chain:
            interceptor.read_after_transmit(context)

    def modify_before_deserialization(
        self, context: ResponseContext[Any, Any, Any]
    ) -> Any:
        transport_response = context.transport_response
        for interceptor in self._chain:
            transport_response = interceptor.modify_before_deserialization(context)
        return transport_response

    def read_before_deserialization(
        self, context: ResponseContext[Any, Any, Any]
    ) -> None:
        for interceptor in self._chain:
            interceptor.read_before_deserialization(context)

    def read_after_deserialization(
        self, context: OutputContext[Any, Any, Any, Any]
    ) -> None:
        for interceptor in self._chain:
            interceptor.read_after_deserialization(context)

    def modify_before_attempt_completion(
        self, context: OutputContext[Any, Any, Any, Any | None]
    ) -> Any | Exception:
        response = context.response
        for interceptor in self._chain:
            response = interceptor.modify_before_attempt_completion(context)
        return response

    def read_after_attempt(
        self, context: OutputContext[Any, Any, Any, Any | None]
    ) -> None:
        for interceptor in self._chain:
            interceptor.read_after_attempt(context)

    def modify_before_completion(
        self, context: OutputContext[Any, Any, Any | None, Any | None]
    ) -> Any | Exception:
        response = context.response
        for interceptor in self._chain:
            response = interceptor.modify_before_attempt_completion(context)
        return response

    def read_after_execution(
        self, context: OutputContext[Any, Any, Any | None, Any | None]
    ) -> None:
        exception: Exception | None = None
        for interceptor in self._chain:
            # Every one of these is supposed to be guaranteed to be called.
            try:
                interceptor.read_after_execution(context)
            except Exception as e:
                context = replace(context, response=e)
                exception = e
        if exception is not None:
            raise exception
