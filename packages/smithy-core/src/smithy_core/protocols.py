import os
from inspect import iscoroutinefunction
from io import BytesIO

from smithy_core.aio.interfaces import ClientProtocol
from smithy_core.codecs import Codec
from smithy_core.deserializers import DeserializeableShape
from smithy_core.interfaces import Endpoint, TypedProperties, URI
from smithy_core.schemas import APIOperation
from smithy_core.serializers import SerializeableShape
from smithy_core.shapes import ShapeID
from smithy_core.traits import HTTPTrait, EndpointTrait, RestJson1Trait
from smithy_core.type_registry import TypeRegistry
from smithy_http.aio.interfaces import HTTPRequest, HTTPResponse
from smithy_http.deserializers import HTTPResponseDeserializer
from smithy_http.serializers import HTTPRequestSerializer
from smithy_json import JSONCodec


class HttpClientProtocol(ClientProtocol[HTTPRequest, HTTPResponse]):
    def set_service_endpoint(
        self,
        *,
        request: HTTPRequest,
        endpoint: Endpoint,
    ) -> HTTPRequest:
        """Update the endpoint of a transport request.

        :param request: The request whose endpoint should be updated.
        :param endpoint: The endpoint to set on the request.
        """
        uri = endpoint.uri
        uri_builder = request.destination

        if uri.scheme:
            uri_builder.scheme = uri.scheme
        if uri.host:
            uri_builder.host = uri.host
        if uri.port and uri.port > -1:
            uri_builder.port = uri.port
        if uri.path:
            # TODO: verify, uri helper?
            uri_builder.path = os.path.join(uri.path, uri_builder.path or "")
        # TODO: merge headers from the endpoint properties bag
        return request


class HttpBindingClientProtocol(HttpClientProtocol):
    @property
    def codec(self) -> Codec:
        """The codec used for the serde of input and output shapes."""
        ...

    @property
    def content_type(self) -> str:
        """The media type of the http payload."""
        ...

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
        # TODO: request binding cache like done in SJ
        serializer = HTTPRequestSerializer(
            payload_codec=self.codec,
            http_trait=operation.schema.expect_trait(HTTPTrait),  # TODO
            endpoint_trait=operation.schema.get_trait(EndpointTrait),
        )

        input.serialize(serializer=serializer)
        request = serializer.result

        if request is None:
            raise ValueError("Request is None")  # TODO

        request.fields["content-type"].add(self.content_type)
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
        if not (200 <= response.status <= 299):  # TODO: extract to utility
            # TODO: implement error serde from type registry
            raise NotImplementedError

        body = response.body
        # TODO: extract to utility, seems common
        if (read := getattr(body, "read", None)) is not None and iscoroutinefunction(
            read
        ):
            body = BytesIO(await read())

        # TODO: response binding cache like done in SJ
        deserializer = HTTPResponseDeserializer(
            payload_codec=self.codec,
            http_trait=operation.schema.expect_trait(HTTPTrait),
            response=response,
            body=body,  # type: ignore
        )

        return operation.output.deserialize(deserializer)


class RestJsonClientProtocol(HttpBindingClientProtocol):
    _id: ShapeID = RestJson1Trait.id
    _codec: JSONCodec = JSONCodec()
    _contentType: str = "application/json"

    @property
    def id(self) -> ShapeID:
        return self._id

    @property
    def codec(self) -> Codec:
        return self._codec

    @property
    def content_type(self) -> str:
        return self._contentType
