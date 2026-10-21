#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Synchronous AWS client protocols.

Each reuses its async counterpart for everything except the two mode-coupled
seams: the request body (the async SigV4 signer requires an async body, the sync
signer a sync one) and the response body read. ``deserialize_response`` delegates
to the shared sync ``_deserialize_from_body`` tail; ``serialize_request`` emits a
plain-bytes body readable by the sync signer and transport.
"""

from io import BytesIO
from typing import Any

from smithy_core import URI as _URI
from smithy_core.aio.types import AsyncBytesReader
from smithy_core.deserializers import DeserializeableShape
from smithy_core.documents import TypeRegistry
from smithy_core.interfaces import TypedProperties, URI
from smithy_core.schemas import APIOperation
from smithy_core.serializers import SerializeableShape
from smithy_http import tuples_to_fields
from smithy_http.aio import HTTPRequest as _HTTPRequest
from smithy_http.aio.interfaces import HTTPRequest, HTTPResponse

from .aio.protocols import AwsJson10ClientProtocol as _AsyncAwsJson10ClientProtocol
from .aio.protocols import AwsJson11ClientProtocol as _AsyncAwsJson11ClientProtocol
from .aio.protocols import AwsQueryClientProtocol as _AsyncAwsQueryClientProtocol
from .aio.protocols import Ec2QueryClientProtocol as _AsyncEc2QueryClientProtocol
from .aio.protocols import RestJsonClientProtocol as _AsyncRestJsonClientProtocol
from .aio.protocols import RestXmlClientProtocol as _AsyncRestXmlClientProtocol


def _sync_body(body: Any) -> BytesIO:
    """Drain an in-memory serialized request body to a seekable BytesIO.

    The HTTP serializer wraps a seekable in-memory buffer in AsyncBytesReader;
    the sync signer needs an Iterable[bytes] (a raw bytes object iterates as
    ints) and the transport a sync reader. Event-stream bodies are not reachable
    here (protocol tests do not stream).
    """
    if isinstance(body, bytes | bytearray):
        return BytesIO(bytes(body))
    if isinstance(body, BytesIO):
        body.seek(0)
        return body
    if isinstance(body, AsyncBytesReader):
        data = body._data  # type: ignore[reportPrivateUsage]  # seekable BytesIO for in-memory serialization
        if isinstance(data, BytesIO):
            data.seek(0)
            return data
    raise TypeError(f"Cannot synchronously read request body of type {type(body)}")


def _sync_json_serialize(
    protocol: Any, operation: APIOperation[Any, Any], input: Any
) -> HTTPRequest:
    payload = protocol.payload_codec.serialize(shape=input)
    return _HTTPRequest(
        method="POST",
        destination=_URI(host="", path="/"),
        fields=tuples_to_fields(
            [
                ("content-type", protocol.content_type),
                ("content-length", str(len(payload))),
                (
                    "x-amz-target",
                    f"{protocol._service_name}.{operation.schema.id.name}",
                ),
            ]
        ),
        body=BytesIO(payload),
    )


class AwsJson10ClientProtocol(_AsyncAwsJson10ClientProtocol):
    """Synchronous implementation of the aws.protocols#awsJson1_0 protocol."""

    def serialize_request[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        input: I,
        endpoint: URI,
        context: TypedProperties,
    ) -> HTTPRequest:
        return _sync_json_serialize(self, operation, input)

    def deserialize_response[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> O:
        return self._deserialize_from_body(
            body=response.consume_body(),
            operation=operation,
            response=response,
            error_registry=error_registry,
            context=context,
        )


class AwsJson11ClientProtocol(_AsyncAwsJson11ClientProtocol):
    """Synchronous implementation of the aws.protocols#awsJson1_1 protocol."""

    def serialize_request[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        input: I,
        endpoint: URI,
        context: TypedProperties,
    ) -> HTTPRequest:
        return _sync_json_serialize(self, operation, input)

    def deserialize_response[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> O:
        return self._deserialize_from_body(
            body=response.consume_body(),
            operation=operation,
            response=response,
            error_registry=error_registry,
            context=context,
        )


class AwsQueryClientProtocol(_AsyncAwsQueryClientProtocol):
    """Synchronous implementation of the aws.protocols#awsQuery protocol."""

    def serialize_request[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        input: I,
        endpoint: URI,
        context: TypedProperties,
    ) -> HTTPRequest:
        sink = BytesIO()
        params: list[tuple[str, str]] = []
        serializer = self._create_serializer(
            sink=sink, action=self._action_name(operation), params=params
        )
        input.serialize(serializer)
        serializer.flush()
        content_length = sink.tell()
        sink.seek(0)
        return _HTTPRequest(
            method="POST",
            destination=_URI(host="", path="/"),
            fields=tuples_to_fields(
                [
                    ("content-type", self.content_type),
                    ("content-length", str(content_length)),
                ]
            ),
            body=sink,
        )

    def deserialize_response[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> O:
        return self._deserialize_from_body(
            body=response.consume_body(),
            operation=operation,
            response=response,
            error_registry=error_registry,
            context=context,
        )


class RestJsonClientProtocol(_AsyncRestJsonClientProtocol):
    """Synchronous implementation of the aws.protocols#restJson1 protocol."""

    def serialize_request[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        input: I,
        endpoint: URI,
        context: TypedProperties,
    ) -> HTTPRequest:
        # Reuse the HTTP-binding serializer, then drain the async body to bytes
        # so the sync signer/transport can read it.
        request = super().serialize_request(
            operation=operation, input=input, endpoint=endpoint, context=context
        )
        request.body = _sync_body(request.body)
        return request

    def deserialize_response[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> O:
        body = None
        if not operation.output_stream_member:
            body = response.consume_body()
        return self._deserialize_from_body(
            body=body,
            operation=operation,
            request=request,
            response=response,
            error_registry=error_registry,
            context=context,
        )


class Ec2QueryClientProtocol(_AsyncEc2QueryClientProtocol):
    """Synchronous implementation of the aws.protocols#ec2Query protocol."""

    def serialize_request[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        input: I,
        endpoint: URI,
        context: TypedProperties,
    ) -> HTTPRequest:
        sink = BytesIO()
        params: list[tuple[str, str]] = []
        serializer = self._create_serializer(
            sink=sink, action=self._action_name(operation), params=params
        )
        input.serialize(serializer)
        serializer.flush()
        content_length = sink.tell()
        sink.seek(0)
        return _HTTPRequest(
            method="POST",
            destination=_URI(host="", path="/"),
            fields=tuples_to_fields(
                [
                    ("content-type", self.content_type),
                    ("content-length", str(content_length)),
                ]
            ),
            body=sink,
        )

    def deserialize_response[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> O:
        return self._deserialize_from_body(
            body=response.consume_body(),
            operation=operation,
            response=response,
            error_registry=error_registry,
            context=context,
        )


class RestXmlClientProtocol(_AsyncRestXmlClientProtocol):
    """Synchronous implementation of the aws.protocols#restXml protocol."""

    def serialize_request[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        input: I,
        endpoint: URI,
        context: TypedProperties,
    ) -> HTTPRequest:
        request = super().serialize_request(
            operation=operation, input=input, endpoint=endpoint, context=context
        )
        request.body = _sync_body(request.body)
        return request

    def deserialize_response[  # type: ignore[override]
        I: SerializeableShape,
        O: DeserializeableShape,
    ](
        self,
        *,
        operation: APIOperation[I, O],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> O:
        body = None
        if not operation.output_stream_member:
            body = response.consume_body()
        return self._deserialize_from_body(
            body=body,
            operation=operation,
            request=request,
            response=response,
            error_registry=error_registry,
            context=context,
        )
