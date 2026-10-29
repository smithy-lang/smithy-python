# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, ClassVar

from smithy_core.aio.interfaces import AsyncWriter
from smithy_core.aio.interfaces.auth import AsyncAuthScheme
from smithy_core.aio.interfaces.eventstream import (
    AsyncEventPublisher,
    AsyncEventReceiver,
)
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.deserializers import DeserializeableShape, ShapeDeserializer
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import MissingDependencyError, UnsupportedStreamError
from smithy_core.interfaces import ProtocolSettings as ProtocolSettings
from smithy_core.interfaces import TypedProperties
from smithy_core.schemas import APIOperation
from smithy_core.serializers import SerializeableShape
from smithy_core.shapes import ShapeID
from smithy_http.aio.interfaces import HTTPRequest, HTTPResponse
from smithy_http.aio.protocols import (
    AsyncHttpBindingClientProtocol,
    AsyncRpcClientProtocol,
)

from ..protocols import (
    AWSErrorIdentifier,
    AWSJSONDocument,
    _AWSJSONProtocolBase,  # pyright: ignore[reportPrivateUsage]
    _AwsQueryProtocolBase,  # pyright: ignore[reportPrivateUsage]
    _AWSResponseMetadataMixin,  # pyright: ignore[reportPrivateUsage]
    _Ec2QueryProtocolBase,  # pyright: ignore[reportPrivateUsage]
    _RestJsonProtocolBase,  # pyright: ignore[reportPrivateUsage]
    _RestXmlProtocolBase,  # pyright: ignore[reportPrivateUsage]
)
from ..traits import AwsJson1_0Trait, AwsJson1_1Trait

try:
    from smithy_aws_event_stream.aio import (
        AWSEventPublisher,
        AWSEventReceiver,
        SigningConfig,
    )

    _HAS_EVENT_STREAM = True
except ImportError:
    _HAS_EVENT_STREAM = False  # type: ignore

try:
    from smithy_aws_event_stream.exceptions import MissingInitialResponse
except ImportError:
    pass

if TYPE_CHECKING:
    from smithy_aws_event_stream.aio import (
        AWSEventPublisher,
        AWSEventReceiver,
        SigningConfig,
    )
    from smithy_aws_event_stream.exceptions import MissingInitialResponse
    from typing_extensions import TypeForm


__all__ = [
    "AWSErrorIdentifier",
    "AWSJSONDocument",
    "AsyncAwsJson10ClientProtocol",
    "AsyncAwsJson11ClientProtocol",
    "AsyncAwsQueryClientProtocol",
    "AsyncEc2QueryClientProtocol",
    "AsyncRestJsonClientProtocol",
    "AsyncRestXmlClientProtocol",
]


def _assert_event_stream() -> None:
    if not _HAS_EVENT_STREAM:
        raise MissingDependencyError(
            "Attempted to use event streams, but smithy-aws-event-stream "
            "is not installed."
        )


class _AWSHttpBindingClientProtocol(
    _AWSResponseMetadataMixin, AsyncHttpBindingClientProtocol
):
    """Base for the AWS protocols that use HTTP bindings: restJson1 and restXml.

    Adds AWS response metadata. Event streams are inherited from
    ``AsyncHttpBindingClientProtocol``: events are framed as
    ``application/vnd.amazon.eventstream`` and structured event payloads use the
    protocol's payload codec.
    """

    async def create_event_publisher[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
        Event: SerializeableShape,
    ](
        self,
        *,
        operation: "APIOperation[OperationInput, OperationOutput]",
        request: HTTPRequest,
        event_type: "TypeForm[Event]",
        context: TypedProperties,
        auth_scheme: AsyncAuthScheme[Any, Any, Any, Any] | None = None,
    ) -> AsyncEventPublisher[Event]:
        _assert_event_stream()
        signing_config: SigningConfig | None = None
        if auth_scheme is not None:
            event_signer = auth_scheme.event_signer(request=request)
            if event_signer is not None:
                signing_config = SigningConfig(
                    signer=event_signer,
                    signing_properties=auth_scheme.signer_properties(context=context),
                    identity_resolver=auth_scheme.identity_resolver(context=context),
                    identity_properties=auth_scheme.identity_properties(
                        context=context
                    ),
                )

        # The HTTP body must be an async writeable. The HTTP serializers are responsible
        # for ensuring this.
        body = request.body
        if not isinstance(body, AsyncWriter) or not iscoroutinefunction(body.write):
            raise UnsupportedStreamError(
                "Input streams require an async write function, but none was present "
                "on the serialized HTTP request."
            )

        return AWSEventPublisher[Event](
            payload_codec=self.payload_codec,
            async_writer=body,
            signing_config=signing_config,
        )

    def create_event_receiver[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
        Event: DeserializeableShape,
    ](
        self,
        *,
        operation: "APIOperation[OperationInput, OperationOutput]",
        request: HTTPRequest,
        response: HTTPResponse,
        event_type: "TypeForm[Event]",
        event_deserializer: Callable[[ShapeDeserializer], Event],
        context: TypedProperties,
    ) -> AsyncEventReceiver[Event]:
        _assert_event_stream()
        return AWSEventReceiver(
            payload_codec=self.payload_codec,
            source=AsyncBytesReader(response.body),
            deserializer=event_deserializer,
        )


class AsyncRestJsonClientProtocol(_RestJsonProtocolBase, _AWSHttpBindingClientProtocol):
    """An implementation of the aws.protocols#restJson1 protocol."""


class AsyncRestXmlClientProtocol(_RestXmlProtocolBase, _AWSHttpBindingClientProtocol):
    """An implementation of the aws.protocols#restXml protocol."""


class _AWSJSONClientProtocol(_AWSJSONProtocolBase, AsyncRpcClientProtocol):
    async def deserialize_response[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> OperationOutput:
        if (
            self._is_event_stream_member(operation.output_stream_member)
            and response.status == 200
        ):
            return await self._deserialize_event_stream_response(
                operation=operation, response=response, context=context
            )

        return self._deserialize_body(
            operation=operation,
            response=response,
            body=await response.consume_body_async(),
            error_registry=error_registry,
            context=context,
        )

    def _default_output[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self, operation: APIOperation[OperationInput, OperationOutput]
    ) -> OperationOutput:
        # initial-response is required only if an empty document can't satisfy the
        # output; clients fill defaults, so only a required-without-default member does.
        if self._requires_initial_response(operation.output_schema):
            raise MissingInitialResponse()
        return self.payload_codec.deserialize(source=b"{}", shape=operation.output)


class AsyncAwsJson10ClientProtocol(_AWSJSONClientProtocol):
    """An implementation of the aws.protocols#awsJson1_0 protocol."""

    _id: ClassVar[ShapeID] = AwsJson1_0Trait.id
    _content_type: ClassVar[str] = "application/x-amz-json-1.0"


class AsyncAwsJson11ClientProtocol(_AWSJSONClientProtocol):
    """An implementation of the aws.protocols#awsJson1_1 protocol."""

    _id: ClassVar[ShapeID] = AwsJson1_1Trait.id
    _content_type: ClassVar[str] = "application/x-amz-json-1.1"


class AsyncAwsQueryClientProtocol(_AwsQueryProtocolBase, AsyncRpcClientProtocol):
    """An implementation of the aws.protocols#awsQuery protocol."""

    async def deserialize_response[
        OperationInput: SerializeableShape,
        OperationOutput: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> OperationOutput:
        return self._deserialize_body(
            operation=operation,
            response=response,
            body=await response.consume_body_async(),
            error_registry=error_registry,
            context=context,
        )


class AsyncEc2QueryClientProtocol(_Ec2QueryProtocolBase, AsyncAwsQueryClientProtocol):
    """An implementation of the aws.protocols#ec2Query protocol.

    An EC2-specific extension of awsQuery: input keys resolve via ``@ec2QueryName``
    and lists are always flattened; responses have no ``Result`` wrapper and errors
    nest under ``<Response><Errors><Error>``.
    """
