# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os
from collections.abc import AsyncIterable
from inspect import iscoroutinefunction
from typing import Any

from smithy_core import URI as _URI
from smithy_core.aio.interfaces import AsyncByteStream, ClientProtocol
from smithy_core.aio.interfaces import StreamingBlob as AsyncStreamingBlob
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import CallError, ExpectationNotMetError, ModeledError
from smithy_core.interfaces import (
    Endpoint,
    SeekableBytesReader,
    TypedProperties,
    URI,
    is_streaming_blob,
)
from smithy_core.interfaces import StreamingBlob as SyncStreamingBlob
from smithy_core.prelude import DOCUMENT
from smithy_core.schemas import APIOperation
from smithy_core.serializers import SerializeableShape
from smithy_core.traits import EndpointTrait, HTTPTrait

from ..deserializers import HTTPResponseDeserializer
from ..serializers import HTTPRequestSerializer
from .interfaces import HTTPErrorIdentifier, HTTPRequest, HTTPResponse


class HttpClientProtocol(ClientProtocol[HTTPRequest, HTTPResponse]):
    """An HTTP-based protocol."""

    def set_service_endpoint(
        self,
        *,
        request: HTTPRequest,
        endpoint: Endpoint,
    ) -> HTTPRequest:
        uri = endpoint.uri
        previous = request.destination

        path = previous.path or uri.path
        if uri.path is not None and previous.path is not None:
            path = os.path.join(uri.path, previous.path.lstrip("/"))

        if path is not None and not path.startswith("/"):
            path = "/" + path

        query = previous.query or uri.query
        if uri.query and previous.query:
            query = f"{uri.query}&{previous.query}"

        request.destination = _URI(
            scheme=uri.scheme,
            username=uri.username or previous.username,
            password=uri.password or previous.password,
            host=uri.host,
            port=uri.port or previous.port,
            path=path,
            query=query,
            fragment=uri.fragment or previous.fragment,
        )

        return request


class HttpBindingClientProtocol(HttpClientProtocol):
    """An HTTP-based protocol that uses HTTP binding traits."""

    @property
    def payload_codec(self) -> Codec:
        """The codec used for the serde of input and output payloads."""
        raise NotImplementedError()

    @property
    def content_type(self) -> str:
        """The media type of the http payload."""
        raise NotImplementedError()

    @property
    def error_identifier(self) -> HTTPErrorIdentifier:
        """The class used to identify the shape IDs of errors based on fields or other
        response information."""
        raise NotImplementedError()

    def serialize_request[
        OperationInput: "SerializeableShape",
        OperationOutput: "DeserializeableShape",
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        input: OperationInput,
        endpoint: URI,
        context: TypedProperties,
    ) -> HTTPRequest:
        # TODO(optimization): request binding cache like done in SJ
        serializer = HTTPRequestSerializer(
            payload_codec=self.payload_codec,
            http_trait=operation.schema.expect_trait(HTTPTrait),
            endpoint_trait=operation.schema.get_trait(EndpointTrait),
        )

        input.serialize(serializer=serializer)
        request = serializer.result

        if request is None:
            raise ExpectationNotMetError(
                "Expected request to be serialized, but was None"
            )

        return request

    async def deserialize_response[
        OperationInput: "SerializeableShape",
        OperationOutput: "DeserializeableShape",
    ](
        self,
        *,
        operation: APIOperation[OperationInput, OperationOutput],
        request: HTTPRequest,
        response: HTTPResponse,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> OperationOutput:
        if not self._is_success(operation, context, response):
            raise await self._create_error(
                operation=operation,
                request=request,
                response=response,
                response_body=await self._buffer_async_body(response.body),
                error_registry=error_registry,
                context=context,
            )

        # if body is not streaming and is async, we have to buffer it
        body: SyncStreamingBlob | None = None
        if not operation.output_stream_member and not is_streaming_blob(body):
            body = await self._buffer_async_body(response.body)

        # TODO(optimization): response binding cache like done in SJ
        deserializer = HTTPResponseDeserializer(
            payload_codec=self.payload_codec,
            http_trait=operation.schema.expect_trait(HTTPTrait),
            response=response,
            body=body,
        )

        return operation.output.deserialize(deserializer)

    async def _buffer_async_body(self, stream: AsyncStreamingBlob) -> SyncStreamingBlob:
        match stream:
            case AsyncByteStream():
                if not iscoroutinefunction(stream.read):
                    return stream  # type: ignore
                return await stream.read()
            case AsyncIterable():
                full = b""
                async for chunk in stream:
                    full += chunk
                return full
            case _:
                return stream

    def _is_success(
        self,
        operation: APIOperation[Any, Any],
        context: TypedProperties,
        response: HTTPResponse,
    ) -> bool:
        return 200 <= response.status < 300

    async def _create_error(
        self,
        operation: APIOperation[Any, Any],
        request: HTTPRequest,
        response: HTTPResponse,
        response_body: SyncStreamingBlob,
        error_registry: TypeRegistry,
        context: TypedProperties,
    ) -> CallError:
        error_id = self.error_identifier.identify(
            operation=operation, response=response
        )

        if error_id is None and self._matches_content_type(response):
            if isinstance(response_body, bytearray):
                response_body = bytes(response_body)
            deserializer = self.payload_codec.create_deserializer(source=response_body)
            document = deserializer.read_document(schema=DOCUMENT)

            if document.discriminator in error_registry:
                error_id = document.discriminator
                if isinstance(response_body, SeekableBytesReader):
                    response_body.seek(0)

        if error_id is not None and error_id in error_registry:
            error_shape = error_registry.get(error_id)

            # make sure the error shape is derived from modeled exception
            if not issubclass(error_shape, ModeledError):
                raise ExpectationNotMetError(
                    f"Modeled errors must be derived from 'ModeledError', "
                    f"but got {error_shape}"
                )

            deserializer = HTTPResponseDeserializer(
                payload_codec=self.payload_codec,
                http_trait=operation.schema.expect_trait(HTTPTrait),
                response=response,
                body=response_body,
            )
            return error_shape.deserialize(deserializer)

        is_throttle = response.status == 429
        message = (
            f"Unknown error for operation {operation.schema.id} "
            f"- status: {response.status}"
        )
        if error_id is not None:
            message += f" - id: {error_id}"
        if response.reason is not None:
            message += f" - reason: {response.status}"
        return CallError(
            message=message,
            fault="client" if response.status < 500 else "server",
            is_throttling_error=is_throttle,
            is_retry_safe=is_throttle or None,
        )

    def _matches_content_type(self, response: HTTPResponse) -> bool:
        if "content-type" not in response.fields:
            return False
        return response.fields["content-type"].as_string() == self.content_type
