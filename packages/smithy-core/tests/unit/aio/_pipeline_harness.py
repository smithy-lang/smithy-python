# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import Any, Self, cast

from smithy_core import URI
from smithy_core.aio.client import ClientCall, RequestPipeline
from smithy_core.aio.interfaces import ClientProtocol
from smithy_core.aio.interfaces.retries import RetryStrategy
from smithy_core.aio.retries import SimpleRetryStrategy
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.endpoints import EndpointResolverParams
from smithy_core.interceptors import InterceptorChain
from smithy_core.response import EMPTY_RESPONSE_METADATA, ResponseMetadata
from smithy_core.schemas import APIOperation, Schema
from smithy_core.serializers import ShapeSerializer
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import StreamingTrait
from smithy_core.types import TypedProperties

_STRING = Schema(id=ShapeID("smithy.api#String"), shape_type=ShapeType.STRING)

_EVENTS = Schema.collection(
    id=ShapeID("com.example#Events"),
    shape_type=ShapeType.UNION,
    members={"message": {"target": _STRING}},
)

_INPUT_SCHEMA = Schema.collection(
    id=ShapeID("com.example#StreamingInput"),
    members={"events": {"target": _EVENTS, "traits": [StreamingTrait()]}},
)

_OUTPUT_SCHEMA = Schema.collection(
    id=ShapeID("com.example#StreamingOutput"),
    members={"events": {"target": _EVENTS, "traits": [StreamingTrait()]}},
)


class StubInput:
    def serialize(self, serializer: ShapeSerializer) -> None:
        pass


class StubOutput:
    # Declared the same way codegen declares it on generated operation outputs.
    response_metadata: ResponseMetadata = EMPTY_RESPONSE_METADATA

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls()


class StubEvent:
    def serialize(self, serializer: ShapeSerializer) -> None:
        pass

    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self:
        return cls()


_UNARY_INPUT_SCHEMA = Schema.collection(
    id=ShapeID("com.example#UnaryInput"),
    members={"message": {"target": _STRING}},
)
_UNARY_OUTPUT_SCHEMA = Schema.collection(
    id=ShapeID("com.example#UnaryOutput"),
    members={"message": {"target": _STRING}},
)

OPERATION = APIOperation(
    input=StubInput,
    output=StubOutput,
    schema=Schema(
        id=ShapeID("com.example#StreamingOperation"),
        shape_type=ShapeType.OPERATION,
    ),
    input_schema=_INPUT_SCHEMA,
    output_schema=_OUTPUT_SCHEMA,
    error_registry=TypeRegistry({}),
    effective_auth_schemes=[],
    error_schemas=[],
)

# ``ClientCall.retryable()`` is False for operations with a streaming input, so
# OPERATION above never enters the retry loop. This one has no input stream and so
# exercises it.
UNARY_OPERATION = APIOperation(
    input=StubInput,
    output=StubOutput,
    schema=Schema(
        id=ShapeID("com.example#UnaryOperation"),
        shape_type=ShapeType.OPERATION,
    ),
    input_schema=_UNARY_INPUT_SCHEMA,
    output_schema=_UNARY_OUTPUT_SCHEMA,
    error_registry=TypeRegistry({}),
    effective_auth_schemes=[],
    error_schemas=[],
)


class StubRequest:
    def __init__(self) -> None:
        self.destination = URI(host="example.com")
        self.body = b""

    async def consume_body_async(self) -> bytes:
        return b""

    def consume_body(self) -> bytes:
        return b""


class StubResponse:
    body = b""

    async def consume_body_async(self) -> bytes:
        return b""

    def consume_body(self) -> bytes:
        return b""


class StubEventPublisher:
    async def send(self, event: Any) -> None:
        pass

    async def close(self) -> None:
        pass


class StubEventReceiver:
    async def receive(self) -> Any:
        return None

    async def close(self) -> None:
        pass


class StubProtocol:
    def __init__(self) -> None:
        self.serialize_request_calls = 0
        self.set_service_endpoint_calls = 0
        self.deserialize_response_calls = 0
        self.create_event_publisher_calls = 0
        self.create_event_receiver_calls = 0
        self.extract_response_metadata_calls = 0
        # What extraction yields; the values tests assert on.
        self.stub_response_metadata = ResponseMetadata(
            request_id="stub-request-id",
            extended_request_id="stub-extended-request-id",
            http_status_code=200,
        )
        self.extract_response_metadata_error: Exception | None = None

    @property
    def id(self) -> ShapeID:
        return ShapeID("com.example#testProtocol")

    def serialize_request(self, **kwargs: Any) -> StubRequest:
        self.serialize_request_calls += 1
        return StubRequest()

    def set_service_endpoint(self, *, request: Any, endpoint: Any) -> Any:
        self.set_service_endpoint_calls += 1
        return request

    async def deserialize_response(self, **kwargs: Any) -> StubOutput:
        self.deserialize_response_calls += 1
        return StubOutput()

    def extract_response_metadata(self, **kwargs: Any) -> ResponseMetadata:
        self.extract_response_metadata_calls += 1
        if self.extract_response_metadata_error is not None:
            raise self.extract_response_metadata_error
        return self.stub_response_metadata

    def create_event_publisher(self, **kwargs: Any) -> StubEventPublisher:
        self.create_event_publisher_calls += 1
        return StubEventPublisher()

    def create_event_receiver(self, **kwargs: Any) -> StubEventReceiver:
        self.create_event_receiver_calls += 1
        return StubEventReceiver()


class StubEndpoint:
    def __init__(self) -> None:
        self.uri = URI(host="example.com")
        self.properties = TypedProperties()


class StubEndpointResolver:
    async def resolve_endpoint(self, params: EndpointResolverParams[Any]) -> Any:
        return StubEndpoint()


class StubAuthResolver:
    def resolve_auth_scheme(self, *, auth_parameters: Any) -> list[Any]:
        return []


class UndeclaredTransport:
    """A transport that does not declare whether it supports duplex streaming."""

    TIMEOUT_EXCEPTIONS: tuple[type[Exception], ...] = ()

    def __init__(self) -> None:
        self.send_calls = 0

    async def send(self, request: Any) -> StubResponse:
        self.send_calls += 1
        return StubResponse()


class NonDuplexTransport(UndeclaredTransport):
    SUPPORTS_DUPLEX_STREAMING = False


class DuplexTransport(UndeclaredTransport):
    SUPPORTS_DUPLEX_STREAMING = True


@dataclass
class PipelineHarness:
    protocol: StubProtocol
    transport: UndeclaredTransport
    pipeline: RequestPipeline[Any, Any]


def pipeline_harness(transport: UndeclaredTransport) -> PipelineHarness:
    protocol = StubProtocol()
    pipeline = RequestPipeline(
        protocol=cast("ClientProtocol[Any, Any]", protocol),
        transport=transport,
    )
    return PipelineHarness(protocol=protocol, transport=transport, pipeline=pipeline)


def retryable_client_call(
    retry_strategy: RetryStrategy | None = None,
) -> ClientCall[Any, Any]:
    """A call that goes through the retry loop, unlike :py:func:`client_call`.

    Defaults to a strategy that allows a single attempt, so the loop gives up after
    the first failure rather than sleeping through retries.
    """
    return ClientCall(
        input=StubInput(),
        operation=UNARY_OPERATION,
        context=TypedProperties(),
        interceptor=InterceptorChain([]),
        auth_scheme_resolver=StubAuthResolver(),
        supported_auth_schemes={},
        endpoint_resolver=StubEndpointResolver(),
        retry_strategy=retry_strategy or SimpleRetryStrategy(max_attempts=1),
    )


def client_call() -> ClientCall[Any, Any]:
    return ClientCall(
        input=StubInput(),
        operation=OPERATION,
        context=TypedProperties(),
        interceptor=InterceptorChain([]),
        auth_scheme_resolver=StubAuthResolver(),
        supported_auth_schemes={},
        endpoint_resolver=StubEndpointResolver(),
        retry_strategy=None,  # type: ignore[arg-type] # unused for streaming input
    )
