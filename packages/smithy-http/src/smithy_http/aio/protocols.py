import os
from inspect import iscoroutinefunction
from io import BytesIO

from smithy_core.aio.interfaces import ClientProtocol
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape
from smithy_core.documents import TypeRegistry
from smithy_core.exceptions import ExpectationNotMetException
from smithy_core.interfaces import Endpoint, TypedProperties, URI
from smithy_core.schemas import APIOperation
from smithy_core.serializers import SerializeableShape
from smithy_core.traits import EndpointTrait, HTTPTrait

from smithy_http.aio.interfaces import HTTPRequest, HTTPResponse
from smithy_http.deserializers import HTTPResponseDeserializer
from smithy_http.serializers import HTTPRequestSerializer


class HttpClientProtocol(ClientProtocol[HTTPRequest, HTTPResponse]):
    """An HTTP-based protocol."""

    def set_service_endpoint(
        self,
        *,
        request: HTTPRequest,
        endpoint: Endpoint,
    ) -> HTTPRequest:
        uri = endpoint.uri
        uri_builder = request.destination

        if uri.scheme:
            uri_builder.scheme = uri.scheme
        if uri.host:
            uri_builder.host = uri.host
        if uri.port and uri.port > -1:
            uri_builder.port = uri.port
        if uri.path:
            uri_builder.path = os.path.join(uri.path, uri_builder.path or "")
        # TODO: merge headers from the endpoint properties bag
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
            raise ExpectationNotMetException(
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
        if not (200 <= response.status <= 299):
            # TODO: implement error serde from type registry
            raise NotImplementedError

        body = response.body

        # if body is not streaming and is async, we have to buffer it
        if not operation.output_stream_member:
            if (
                read := getattr(body, "read", None)
            ) is not None and iscoroutinefunction(read):
                body = BytesIO(await read())

        # TODO(optimization): response binding cache like done in SJ
        deserializer = HTTPResponseDeserializer(
            payload_codec=self.payload_codec,
            http_trait=operation.schema.expect_trait(HTTPTrait),
            response=response,
            body=body,  # type: ignore
        )

        return operation.output.deserialize(deserializer)
