from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.aio.identity.chain import AsyncIdentityChain
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.aio.client import AsyncClient
from smithy_http.aio.interfaces import AsyncHTTPClient
from smithy_http.plugins import user_agent_plugin

from restjson_client import models
from restjson_client.aio.config import AsyncRestJsonProtocolConfig, Plugin
from restjson_client.aio.user_agent import aws_user_agent_plugin


class AsyncRestJsonProtocolClient(AsyncClient[AsyncRestJsonProtocolConfig]):
    "Client for RestJson."

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

    @overload
    async def all_query_string_types(
        self,
        request: models.AllQueryStringTypesInput | models.AllQueryStringTypesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.AllQueryStringTypesOutput: ...

    @overload
    async def all_query_string_types(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.AllQueryStringTypesInputDict],
    ) -> models.AllQueryStringTypesOutput:
        """
        This example uses all query string types.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `AllQueryStringTypesOutput`.
        """

    async def all_query_string_types(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.AllQueryStringTypesOutput:
        return await self._invoke(
            self._select_input(models.ALL_QUERY_STRING_TYPES, args, kwargs),
            models.ALL_QUERY_STRING_TYPES,
            [],
            plugins,
        )

    @overload
    async def constant_and_variable_query_string(
        self,
        request: models.ConstantAndVariableQueryStringInput
        | models.ConstantAndVariableQueryStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ConstantAndVariableQueryStringOutput: ...

    @overload
    async def constant_and_variable_query_string(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.ConstantAndVariableQueryStringInputDict],
    ) -> models.ConstantAndVariableQueryStringOutput:
        """
        This example uses fixed query string params and variable query string
        params.
        The fixed query string parameters and variable parameters must both be
        serialized (implementations may need to merge them together).

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `ConstantAndVariableQueryStringOutput`.
        """

    async def constant_and_variable_query_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ConstantAndVariableQueryStringOutput:
        return await self._invoke(
            self._select_input(models.CONSTANT_AND_VARIABLE_QUERY_STRING, args, kwargs),
            models.CONSTANT_AND_VARIABLE_QUERY_STRING,
            [],
            plugins,
        )

    @overload
    async def constant_query_string(
        self,
        request: models.ConstantQueryStringInput | models.ConstantQueryStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ConstantQueryStringOutput: ...

    @overload
    async def constant_query_string(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.ConstantQueryStringInputDict],
    ) -> models.ConstantQueryStringOutput:
        """
        This example uses a constant query string parameters and a label.
        This simply tests that labels and query string parameters are
        compatible. The fixed query string parameter named "hello" should
        in no way conflict with the label, `{hello}`.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `ConstantQueryStringOutput`.
        """

    async def constant_query_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ConstantQueryStringOutput:
        return await self._invoke(
            self._select_input(models.CONSTANT_QUERY_STRING, args, kwargs),
            models.CONSTANT_QUERY_STRING,
            [],
            plugins,
        )

    @overload
    async def content_type_parameters(
        self,
        request: models.ContentTypeParametersInput
        | models.ContentTypeParametersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ContentTypeParametersOutput: ...

    @overload
    async def content_type_parameters(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.ContentTypeParametersInputDict],
    ) -> models.ContentTypeParametersOutput:
        """
        The example tests how servers must support requests
        containing a `Content-Type` header with parameters.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `ContentTypeParametersOutput`.
        """

    async def content_type_parameters(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ContentTypeParametersOutput:
        return await self._invoke(
            self._select_input(models.CONTENT_TYPE_PARAMETERS, args, kwargs),
            models.CONTENT_TYPE_PARAMETERS,
            [],
            plugins,
        )

    @overload
    async def datetime_offsets(
        self,
        request: models.DatetimeOffsetsInput | models.DatetimeOffsetsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.DatetimeOffsetsOutput: ...

    @overload
    async def datetime_offsets(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.DatetimeOffsetsInputDict],
    ) -> models.DatetimeOffsetsOutput:
        """
        Invokes the DatetimeOffsets operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `DatetimeOffsetsOutput`.
        """

    async def datetime_offsets(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.DatetimeOffsetsOutput:
        return await self._invoke(
            self._select_input(models.DATETIME_OFFSETS, args, kwargs),
            models.DATETIME_OFFSETS,
            [],
            plugins,
        )

    @overload
    async def document_type(
        self,
        request: models.DocumentTypeInput | models.DocumentTypeInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.DocumentTypeOutput: ...

    @overload
    async def document_type(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.DocumentTypeInputDict],
    ) -> models.DocumentTypeOutput:
        """
        This example serializes a document as part of the payload.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `DocumentTypeOutput`.
        """

    async def document_type(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.DocumentTypeOutput:
        return await self._invoke(
            self._select_input(models.DOCUMENT_TYPE, args, kwargs),
            models.DOCUMENT_TYPE,
            [],
            plugins,
        )

    @overload
    async def document_type_as_map_value(
        self,
        request: models.DocumentTypeAsMapValueInput
        | models.DocumentTypeAsMapValueInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.DocumentTypeAsMapValueOutput: ...

    @overload
    async def document_type_as_map_value(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.DocumentTypeAsMapValueInputDict],
    ) -> models.DocumentTypeAsMapValueOutput:
        """
        This example serializes documents as the value of maps.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `DocumentTypeAsMapValueOutput`.
        """

    async def document_type_as_map_value(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.DocumentTypeAsMapValueOutput:
        return await self._invoke(
            self._select_input(models.DOCUMENT_TYPE_AS_MAP_VALUE, args, kwargs),
            models.DOCUMENT_TYPE_AS_MAP_VALUE,
            [],
            plugins,
        )

    @overload
    async def document_type_as_payload(
        self,
        request: models.DocumentTypeAsPayloadInput
        | models.DocumentTypeAsPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.DocumentTypeAsPayloadOutput: ...

    @overload
    async def document_type_as_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.DocumentTypeAsPayloadInputDict],
    ) -> models.DocumentTypeAsPayloadOutput:
        """
        This example serializes a document as the entire HTTP payload.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `DocumentTypeAsPayloadOutput`.
        """

    async def document_type_as_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.DocumentTypeAsPayloadOutput:
        return await self._invoke(
            self._select_input(models.DOCUMENT_TYPE_AS_PAYLOAD, args, kwargs),
            models.DOCUMENT_TYPE_AS_PAYLOAD,
            [],
            plugins,
        )

    @overload
    async def empty_input_and_empty_output(
        self,
        request: models.EmptyInputAndEmptyOutputInput
        | models.EmptyInputAndEmptyOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EmptyInputAndEmptyOutputOutput: ...

    @overload
    async def empty_input_and_empty_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.EmptyInputAndEmptyOutputInputDict],
    ) -> models.EmptyInputAndEmptyOutputOutput:
        """
        The example tests how requests and responses are serialized when there's
        no request or response payload because the operation has an empty input
        and empty output structure that reuses the same shape. While this should
        be rare, code generators must support this.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `EmptyInputAndEmptyOutputOutput`.
        """

    async def empty_input_and_empty_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EmptyInputAndEmptyOutputOutput:
        return await self._invoke(
            self._select_input(models.EMPTY_INPUT_AND_EMPTY_OUTPUT, args, kwargs),
            models.EMPTY_INPUT_AND_EMPTY_OUTPUT,
            [],
            plugins,
        )

    @overload
    async def endpoint_operation(
        self,
        request: models.EndpointOperationInput | models.EndpointOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EndpointOperationOutput: ...

    @overload
    async def endpoint_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.EndpointOperationInputDict],
    ) -> models.EndpointOperationOutput:
        """
        Invokes the EndpointOperation operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `EndpointOperationOutput`.
        """

    async def endpoint_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EndpointOperationOutput:
        return await self._invoke(
            self._select_input(models.ENDPOINT_OPERATION, args, kwargs),
            models.ENDPOINT_OPERATION,
            [],
            plugins,
        )

    @overload
    async def endpoint_with_host_label_operation(
        self,
        request: models.EndpointWithHostLabelOperationInput
        | models.EndpointWithHostLabelOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EndpointWithHostLabelOperationOutput: ...

    @overload
    async def endpoint_with_host_label_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.EndpointWithHostLabelOperationInputDict],
    ) -> models.EndpointWithHostLabelOperationOutput:
        """
        Invokes the EndpointWithHostLabelOperation operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `EndpointWithHostLabelOperationOutput`.
        """

    async def endpoint_with_host_label_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EndpointWithHostLabelOperationOutput:
        return await self._invoke(
            self._select_input(models.ENDPOINT_WITH_HOST_LABEL_OPERATION, args, kwargs),
            models.ENDPOINT_WITH_HOST_LABEL_OPERATION,
            [],
            plugins,
        )

    @overload
    async def fractional_seconds(
        self,
        request: models.FractionalSecondsInput | models.FractionalSecondsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.FractionalSecondsOutput: ...

    @overload
    async def fractional_seconds(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.FractionalSecondsInputDict],
    ) -> models.FractionalSecondsOutput:
        """
        Invokes the FractionalSeconds operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `FractionalSecondsOutput`.
        """

    async def fractional_seconds(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.FractionalSecondsOutput:
        return await self._invoke(
            self._select_input(models.FRACTIONAL_SECONDS, args, kwargs),
            models.FRACTIONAL_SECONDS,
            [],
            plugins,
        )

    @overload
    async def greeting_with_errors(
        self,
        request: models.GreetingWithErrorsInput | models.GreetingWithErrorsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.GreetingWithErrorsOutput: ...

    @overload
    async def greeting_with_errors(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.GreetingWithErrorsInputDict],
    ) -> models.GreetingWithErrorsOutput:
        """
        This operation has four possible return values:

        1. A successful response in the form of GreetingWithErrorsOutput
        2. An InvalidGreeting error.
        3. A BadRequest error.
        4. A FooError.

        Implementations must be able to successfully take a response and
        properly (de)serialize successful and error responses based on the
        the presence of the

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `GreetingWithErrorsOutput`.
        """

    async def greeting_with_errors(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.GreetingWithErrorsOutput:
        return await self._invoke(
            self._select_input(models.GREETING_WITH_ERRORS, args, kwargs),
            models.GREETING_WITH_ERRORS,
            [],
            plugins,
        )

    @overload
    async def host_with_path_operation(
        self,
        request: models.HostWithPathOperationInput
        | models.HostWithPathOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HostWithPathOperationOutput: ...

    @overload
    async def host_with_path_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HostWithPathOperationInputDict],
    ) -> models.HostWithPathOperationOutput:
        """
        Invokes the HostWithPathOperation operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HostWithPathOperationOutput`.
        """

    async def host_with_path_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HostWithPathOperationOutput:
        return await self._invoke(
            self._select_input(models.HOST_WITH_PATH_OPERATION, args, kwargs),
            models.HOST_WITH_PATH_OPERATION,
            [],
            plugins,
        )

    @overload
    async def http_checksum_required(
        self,
        request: models.HttpChecksumRequiredInput
        | models.HttpChecksumRequiredInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpChecksumRequiredOutput: ...

    @overload
    async def http_checksum_required(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpChecksumRequiredInputDict],
    ) -> models.HttpChecksumRequiredOutput:
        """
        This example tests httpChecksumRequired trait

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpChecksumRequiredOutput`.
        """

    async def http_checksum_required(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpChecksumRequiredOutput:
        return await self._invoke(
            self._select_input(models.HTTP_CHECKSUM_REQUIRED, args, kwargs),
            models.HTTP_CHECKSUM_REQUIRED,
            [],
            plugins,
        )

    @overload
    async def http_empty_prefix_headers(
        self,
        request: models.HttpEmptyPrefixHeadersInput
        | models.HttpEmptyPrefixHeadersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpEmptyPrefixHeadersOutput: ...

    @overload
    async def http_empty_prefix_headers(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpEmptyPrefixHeadersInputDict],
    ) -> models.HttpEmptyPrefixHeadersOutput:
        """
        Clients that perform this test extract all headers from the response.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpEmptyPrefixHeadersOutput`.
        """

    async def http_empty_prefix_headers(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpEmptyPrefixHeadersOutput:
        return await self._invoke(
            self._select_input(models.HTTP_EMPTY_PREFIX_HEADERS, args, kwargs),
            models.HTTP_EMPTY_PREFIX_HEADERS,
            [],
            plugins,
        )

    @overload
    async def http_enum_payload(
        self,
        request: models.HttpEnumPayloadInput | models.HttpEnumPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpEnumPayloadOutput: ...

    @overload
    async def http_enum_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpEnumPayloadInputDict],
    ) -> models.HttpEnumPayloadOutput:
        """
        Invokes the HttpEnumPayload operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpEnumPayloadOutput`.
        """

    async def http_enum_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpEnumPayloadOutput:
        return await self._invoke(
            self._select_input(models.HTTP_ENUM_PAYLOAD, args, kwargs),
            models.HTTP_ENUM_PAYLOAD,
            [],
            plugins,
        )

    @overload
    async def http_payload_traits(
        self,
        request: models.HttpPayloadTraitsInput | models.HttpPayloadTraitsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadTraitsOutput: ...

    @overload
    async def http_payload_traits(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPayloadTraitsInputDict],
    ) -> models.HttpPayloadTraitsOutput:
        """
        This example serializes a blob shape in the payload.

        In this example, no JSON document is synthesized because the payload is
        not a structure or a union type.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPayloadTraitsOutput`.
        """

    async def http_payload_traits(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadTraitsOutput:
        return await self._invoke(
            self._select_input(models.HTTP_PAYLOAD_TRAITS, args, kwargs),
            models.HTTP_PAYLOAD_TRAITS,
            [],
            plugins,
        )

    @overload
    async def http_payload_traits_with_media_type(
        self,
        request: models.HttpPayloadTraitsWithMediaTypeInput
        | models.HttpPayloadTraitsWithMediaTypeInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadTraitsWithMediaTypeOutput: ...

    @overload
    async def http_payload_traits_with_media_type(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPayloadTraitsWithMediaTypeInputDict],
    ) -> models.HttpPayloadTraitsWithMediaTypeOutput:
        """
        This example uses a `@mediaType` trait on the payload to force a custom
        content-type to be serialized.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPayloadTraitsWithMediaTypeOutput`.
        """

    async def http_payload_traits_with_media_type(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadTraitsWithMediaTypeOutput:
        return await self._invoke(
            self._select_input(
                models.HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE, args, kwargs
            ),
            models.HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE,
            [],
            plugins,
        )

    @overload
    async def http_payload_with_structure(
        self,
        request: models.HttpPayloadWithStructureInput
        | models.HttpPayloadWithStructureInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadWithStructureOutput: ...

    @overload
    async def http_payload_with_structure(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPayloadWithStructureInputDict],
    ) -> models.HttpPayloadWithStructureOutput:
        """
        This example serializes a structure in the payload.

        Note that serializing a structure changes the wrapper element name
        to match the targeted structure.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPayloadWithStructureOutput`.
        """

    async def http_payload_with_structure(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadWithStructureOutput:
        return await self._invoke(
            self._select_input(models.HTTP_PAYLOAD_WITH_STRUCTURE, args, kwargs),
            models.HTTP_PAYLOAD_WITH_STRUCTURE,
            [],
            plugins,
        )

    @overload
    async def http_payload_with_union(
        self,
        request: models.HttpPayloadWithUnionInput
        | models.HttpPayloadWithUnionInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadWithUnionOutput: ...

    @overload
    async def http_payload_with_union(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPayloadWithUnionInputDict],
    ) -> models.HttpPayloadWithUnionOutput:
        """
        This example serializes a union in the payload.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPayloadWithUnionOutput`.
        """

    async def http_payload_with_union(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadWithUnionOutput:
        return await self._invoke(
            self._select_input(models.HTTP_PAYLOAD_WITH_UNION, args, kwargs),
            models.HTTP_PAYLOAD_WITH_UNION,
            [],
            plugins,
        )

    @overload
    async def http_prefix_headers(
        self,
        request: models.HttpPrefixHeadersInput | models.HttpPrefixHeadersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPrefixHeadersOutput: ...

    @overload
    async def http_prefix_headers(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPrefixHeadersInputDict],
    ) -> models.HttpPrefixHeadersOutput:
        """
        This examples adds headers to the input of a request and response by
        prefix.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPrefixHeadersOutput`.
        """

    async def http_prefix_headers(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPrefixHeadersOutput:
        return await self._invoke(
            self._select_input(models.HTTP_PREFIX_HEADERS, args, kwargs),
            models.HTTP_PREFIX_HEADERS,
            [],
            plugins,
        )

    @overload
    async def http_prefix_headers_in_response(
        self,
        request: models.HttpPrefixHeadersInResponseInput
        | models.HttpPrefixHeadersInResponseInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPrefixHeadersInResponseOutput: ...

    @overload
    async def http_prefix_headers_in_response(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPrefixHeadersInResponseInputDict],
    ) -> models.HttpPrefixHeadersInResponseOutput:
        """
        Clients that perform this test extract all headers from the response.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPrefixHeadersInResponseOutput`.
        """

    async def http_prefix_headers_in_response(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPrefixHeadersInResponseOutput:
        return await self._invoke(
            self._select_input(models.HTTP_PREFIX_HEADERS_IN_RESPONSE, args, kwargs),
            models.HTTP_PREFIX_HEADERS_IN_RESPONSE,
            [],
            plugins,
        )

    @overload
    async def http_query_params_only_operation(
        self,
        request: models.HttpQueryParamsOnlyOperationInput
        | models.HttpQueryParamsOnlyOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpQueryParamsOnlyOperationOutput: ...

    @overload
    async def http_query_params_only_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpQueryParamsOnlyOperationInputDict],
    ) -> models.HttpQueryParamsOnlyOperationOutput:
        """
        This example tests httpQueryParams when no other query parameters exist.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpQueryParamsOnlyOperationOutput`.
        """

    async def http_query_params_only_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpQueryParamsOnlyOperationOutput:
        return await self._invoke(
            self._select_input(models.HTTP_QUERY_PARAMS_ONLY_OPERATION, args, kwargs),
            models.HTTP_QUERY_PARAMS_ONLY_OPERATION,
            [],
            plugins,
        )

    @overload
    async def http_request_with_float_labels(
        self,
        request: models.HttpRequestWithFloatLabelsInput
        | models.HttpRequestWithFloatLabelsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpRequestWithFloatLabelsOutput: ...

    @overload
    async def http_request_with_float_labels(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpRequestWithFloatLabelsInputDict],
    ) -> models.HttpRequestWithFloatLabelsOutput:
        """
        Invokes the HttpRequestWithFloatLabels operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpRequestWithFloatLabelsOutput`.
        """

    async def http_request_with_float_labels(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpRequestWithFloatLabelsOutput:
        return await self._invoke(
            self._select_input(models.HTTP_REQUEST_WITH_FLOAT_LABELS, args, kwargs),
            models.HTTP_REQUEST_WITH_FLOAT_LABELS,
            [],
            plugins,
        )

    @overload
    async def http_request_with_greedy_label_in_path(
        self,
        request: models.HttpRequestWithGreedyLabelInPathInput
        | models.HttpRequestWithGreedyLabelInPathInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpRequestWithGreedyLabelInPathOutput: ...

    @overload
    async def http_request_with_greedy_label_in_path(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpRequestWithGreedyLabelInPathInputDict],
    ) -> models.HttpRequestWithGreedyLabelInPathOutput:
        """
        Invokes the HttpRequestWithGreedyLabelInPath operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpRequestWithGreedyLabelInPathOutput`.
        """

    async def http_request_with_greedy_label_in_path(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpRequestWithGreedyLabelInPathOutput:
        return await self._invoke(
            self._select_input(
                models.HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH, args, kwargs
            ),
            models.HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH,
            [],
            plugins,
        )

    @overload
    async def http_request_with_labels(
        self,
        request: models.HttpRequestWithLabelsInput
        | models.HttpRequestWithLabelsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpRequestWithLabelsOutput: ...

    @overload
    async def http_request_with_labels(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpRequestWithLabelsInputDict],
    ) -> models.HttpRequestWithLabelsOutput:
        """
        The example tests how requests are serialized when there's no input
        payload but there are HTTP labels.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpRequestWithLabelsOutput`.
        """

    async def http_request_with_labels(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpRequestWithLabelsOutput:
        return await self._invoke(
            self._select_input(models.HTTP_REQUEST_WITH_LABELS, args, kwargs),
            models.HTTP_REQUEST_WITH_LABELS,
            [],
            plugins,
        )

    @overload
    async def http_request_with_labels_and_timestamp_format(
        self,
        request: models.HttpRequestWithLabelsAndTimestampFormatInput
        | models.HttpRequestWithLabelsAndTimestampFormatInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpRequestWithLabelsAndTimestampFormatOutput: ...

    @overload
    async def http_request_with_labels_and_timestamp_format(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpRequestWithLabelsAndTimestampFormatInputDict],
    ) -> models.HttpRequestWithLabelsAndTimestampFormatOutput:
        """
        The example tests how requests serialize different timestamp formats in
        the
        URI path.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpRequestWithLabelsAndTimestampFormatOutput`.
        """

    async def http_request_with_labels_and_timestamp_format(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpRequestWithLabelsAndTimestampFormatOutput:
        return await self._invoke(
            self._select_input(
                models.HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT, args, kwargs
            ),
            models.HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT,
            [],
            plugins,
        )

    @overload
    async def http_request_with_regex_literal(
        self,
        request: models.HttpRequestWithRegexLiteralInput
        | models.HttpRequestWithRegexLiteralInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpRequestWithRegexLiteralOutput: ...

    @overload
    async def http_request_with_regex_literal(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpRequestWithRegexLiteralInputDict],
    ) -> models.HttpRequestWithRegexLiteralOutput:
        """
        Invokes the HttpRequestWithRegexLiteral operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpRequestWithRegexLiteralOutput`.
        """

    async def http_request_with_regex_literal(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpRequestWithRegexLiteralOutput:
        return await self._invoke(
            self._select_input(models.HTTP_REQUEST_WITH_REGEX_LITERAL, args, kwargs),
            models.HTTP_REQUEST_WITH_REGEX_LITERAL,
            [],
            plugins,
        )

    @overload
    async def http_response_code(
        self,
        request: models.HttpResponseCodeInput | models.HttpResponseCodeInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpResponseCodeOutput: ...

    @overload
    async def http_response_code(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpResponseCodeInputDict],
    ) -> models.HttpResponseCodeOutput:
        """
        Invokes the HttpResponseCode operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpResponseCodeOutput`.
        """

    async def http_response_code(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpResponseCodeOutput:
        return await self._invoke(
            self._select_input(models.HTTP_RESPONSE_CODE, args, kwargs),
            models.HTTP_RESPONSE_CODE,
            [],
            plugins,
        )

    @overload
    async def http_string_payload(
        self,
        request: models.HttpStringPayloadInput | models.HttpStringPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpStringPayloadOutput: ...

    @overload
    async def http_string_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpStringPayloadInputDict],
    ) -> models.HttpStringPayloadOutput:
        """
        Invokes the HttpStringPayload operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpStringPayloadOutput`.
        """

    async def http_string_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpStringPayloadOutput:
        return await self._invoke(
            self._select_input(models.HTTP_STRING_PAYLOAD, args, kwargs),
            models.HTTP_STRING_PAYLOAD,
            [],
            plugins,
        )

    @overload
    async def ignore_query_params_in_response(
        self,
        request: models.IgnoreQueryParamsInResponseInput
        | models.IgnoreQueryParamsInResponseInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.IgnoreQueryParamsInResponseOutput: ...

    @overload
    async def ignore_query_params_in_response(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.IgnoreQueryParamsInResponseInputDict],
    ) -> models.IgnoreQueryParamsInResponseOutput:
        """
        This example ensures that query string bound request parameters are
        serialized in the body of responses if the structure is used in both
        the request and response.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `IgnoreQueryParamsInResponseOutput`.
        """

    async def ignore_query_params_in_response(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.IgnoreQueryParamsInResponseOutput:
        return await self._invoke(
            self._select_input(models.IGNORE_QUERY_PARAMS_IN_RESPONSE, args, kwargs),
            models.IGNORE_QUERY_PARAMS_IN_RESPONSE,
            [],
            plugins,
        )

    @overload
    async def input_and_output_with_headers(
        self,
        request: models.InputAndOutputWithHeadersInput
        | models.InputAndOutputWithHeadersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.InputAndOutputWithHeadersOutput: ...

    @overload
    async def input_and_output_with_headers(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.InputAndOutputWithHeadersInputDict],
    ) -> models.InputAndOutputWithHeadersOutput:
        """
        The example tests how requests and responses are serialized when there
        is
        no input or output payload but there are HTTP header bindings.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `InputAndOutputWithHeadersOutput`.
        """

    async def input_and_output_with_headers(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.InputAndOutputWithHeadersOutput:
        return await self._invoke(
            self._select_input(models.INPUT_AND_OUTPUT_WITH_HEADERS, args, kwargs),
            models.INPUT_AND_OUTPUT_WITH_HEADERS,
            [],
            plugins,
        )

    @overload
    async def json_blobs(
        self,
        request: models.JsonBlobsInput | models.JsonBlobsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonBlobsOutput: ...

    @overload
    async def json_blobs(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.JsonBlobsInputDict],
    ) -> models.JsonBlobsOutput:
        """
        Blobs are base64 encoded

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `JsonBlobsOutput`.
        """

    async def json_blobs(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonBlobsOutput:
        return await self._invoke(
            self._select_input(models.JSON_BLOBS, args, kwargs),
            models.JSON_BLOBS,
            [],
            plugins,
        )

    @overload
    async def json_enums(
        self,
        request: models.JsonEnumsInput | models.JsonEnumsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonEnumsOutput: ...

    @overload
    async def json_enums(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.JsonEnumsInputDict],
    ) -> models.JsonEnumsOutput:
        """
        This example serializes enums as top level properties, in lists, sets,
        and maps.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `JsonEnumsOutput`.
        """

    async def json_enums(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonEnumsOutput:
        return await self._invoke(
            self._select_input(models.JSON_ENUMS, args, kwargs),
            models.JSON_ENUMS,
            [],
            plugins,
        )

    @overload
    async def json_int_enums(
        self,
        request: models.JsonIntEnumsInput | models.JsonIntEnumsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonIntEnumsOutput: ...

    @overload
    async def json_int_enums(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.JsonIntEnumsInputDict],
    ) -> models.JsonIntEnumsOutput:
        """
        This example serializes intEnums as top level properties, in lists,
        sets, and maps.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `JsonIntEnumsOutput`.
        """

    async def json_int_enums(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonIntEnumsOutput:
        return await self._invoke(
            self._select_input(models.JSON_INT_ENUMS, args, kwargs),
            models.JSON_INT_ENUMS,
            [],
            plugins,
        )

    @overload
    async def json_lists(
        self,
        request: models.JsonListsInput | models.JsonListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonListsOutput: ...

    @overload
    async def json_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.JsonListsInputDict],
    ) -> models.JsonListsOutput:
        """
        This test case serializes JSON lists for the following cases for both
        input and output:

        1. Normal JSON lists.
        2. Normal JSON sets.
        3. JSON lists of lists.
        4. Lists of structures.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `JsonListsOutput`.
        """

    async def json_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonListsOutput:
        return await self._invoke(
            self._select_input(models.JSON_LISTS, args, kwargs),
            models.JSON_LISTS,
            [],
            plugins,
        )

    @overload
    async def json_maps(
        self,
        request: models.JsonMapsInput | models.JsonMapsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonMapsOutput: ...

    @overload
    async def json_maps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.JsonMapsInputDict],
    ) -> models.JsonMapsOutput:
        """
        The example tests basic map serialization.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `JsonMapsOutput`.
        """

    async def json_maps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonMapsOutput:
        return await self._invoke(
            self._select_input(models.JSON_MAPS, args, kwargs),
            models.JSON_MAPS,
            [],
            plugins,
        )

    @overload
    async def json_timestamps(
        self,
        request: models.JsonTimestampsInput | models.JsonTimestampsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonTimestampsOutput: ...

    @overload
    async def json_timestamps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.JsonTimestampsInputDict],
    ) -> models.JsonTimestampsOutput:
        """
        This tests how timestamps are serialized, including using the
        default format of date-time and various @timestampFormat trait
        values.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `JsonTimestampsOutput`.
        """

    async def json_timestamps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonTimestampsOutput:
        return await self._invoke(
            self._select_input(models.JSON_TIMESTAMPS, args, kwargs),
            models.JSON_TIMESTAMPS,
            [],
            plugins,
        )

    @overload
    async def json_unions(
        self,
        request: models.JsonUnionsInput | models.JsonUnionsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonUnionsOutput: ...

    @overload
    async def json_unions(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.JsonUnionsInputDict],
    ) -> models.JsonUnionsOutput:
        """
        This operation uses unions for inputs and outputs.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `JsonUnionsOutput`.
        """

    async def json_unions(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonUnionsOutput:
        return await self._invoke(
            self._select_input(models.JSON_UNIONS, args, kwargs),
            models.JSON_UNIONS,
            [],
            plugins,
        )

    @overload
    async def malformed_accept_with_body(
        self,
        request: models.MalformedAcceptWithBodyInput
        | models.MalformedAcceptWithBodyInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedAcceptWithBodyOutput: ...

    @overload
    async def malformed_accept_with_body(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedAcceptWithBodyInputDict],
    ) -> models.MalformedAcceptWithBodyOutput:
        """
        Invokes the MalformedAcceptWithBody operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedAcceptWithBodyOutput`.
        """

    async def malformed_accept_with_body(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedAcceptWithBodyOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_ACCEPT_WITH_BODY, args, kwargs),
            models.MALFORMED_ACCEPT_WITH_BODY,
            [],
            plugins,
        )

    @overload
    async def malformed_accept_with_generic_string(
        self,
        request: models.MalformedAcceptWithGenericStringInput
        | models.MalformedAcceptWithGenericStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedAcceptWithGenericStringOutput: ...

    @overload
    async def malformed_accept_with_generic_string(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedAcceptWithGenericStringInputDict],
    ) -> models.MalformedAcceptWithGenericStringOutput:
        """
        Invokes the MalformedAcceptWithGenericString operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedAcceptWithGenericStringOutput`.
        """

    async def malformed_accept_with_generic_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedAcceptWithGenericStringOutput:
        return await self._invoke(
            self._select_input(
                models.MALFORMED_ACCEPT_WITH_GENERIC_STRING, args, kwargs
            ),
            models.MALFORMED_ACCEPT_WITH_GENERIC_STRING,
            [],
            plugins,
        )

    @overload
    async def malformed_accept_with_payload(
        self,
        request: models.MalformedAcceptWithPayloadInput
        | models.MalformedAcceptWithPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedAcceptWithPayloadOutput: ...

    @overload
    async def malformed_accept_with_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedAcceptWithPayloadInputDict],
    ) -> models.MalformedAcceptWithPayloadOutput:
        """
        Invokes the MalformedAcceptWithPayload operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedAcceptWithPayloadOutput`.
        """

    async def malformed_accept_with_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedAcceptWithPayloadOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_ACCEPT_WITH_PAYLOAD, args, kwargs),
            models.MALFORMED_ACCEPT_WITH_PAYLOAD,
            [],
            plugins,
        )

    @overload
    async def malformed_blob(
        self,
        request: models.MalformedBlobInput | models.MalformedBlobInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedBlobOutput: ...

    @overload
    async def malformed_blob(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedBlobInputDict],
    ) -> models.MalformedBlobOutput:
        """
        Invokes the MalformedBlob operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedBlobOutput`.
        """

    async def malformed_blob(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedBlobOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_BLOB, args, kwargs),
            models.MALFORMED_BLOB,
            [],
            plugins,
        )

    @overload
    async def malformed_boolean(
        self,
        request: models.MalformedBooleanInput | models.MalformedBooleanInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedBooleanOutput: ...

    @overload
    async def malformed_boolean(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedBooleanInputDict],
    ) -> models.MalformedBooleanOutput:
        """
        Invokes the MalformedBoolean operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedBooleanOutput`.
        """

    async def malformed_boolean(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedBooleanOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_BOOLEAN, args, kwargs),
            models.MALFORMED_BOOLEAN,
            [],
            plugins,
        )

    @overload
    async def malformed_byte(
        self,
        request: models.MalformedByteInput | models.MalformedByteInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedByteOutput: ...

    @overload
    async def malformed_byte(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedByteInputDict],
    ) -> models.MalformedByteOutput:
        """
        Invokes the MalformedByte operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedByteOutput`.
        """

    async def malformed_byte(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedByteOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_BYTE, args, kwargs),
            models.MALFORMED_BYTE,
            [],
            plugins,
        )

    @overload
    async def malformed_content_type_with_body(
        self,
        request: models.MalformedContentTypeWithBodyInput
        | models.MalformedContentTypeWithBodyInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedContentTypeWithBodyOutput: ...

    @overload
    async def malformed_content_type_with_body(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedContentTypeWithBodyInputDict],
    ) -> models.MalformedContentTypeWithBodyOutput:
        """
        Invokes the MalformedContentTypeWithBody operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedContentTypeWithBodyOutput`.
        """

    async def malformed_content_type_with_body(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedContentTypeWithBodyOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_CONTENT_TYPE_WITH_BODY, args, kwargs),
            models.MALFORMED_CONTENT_TYPE_WITH_BODY,
            [],
            plugins,
        )

    @overload
    async def malformed_content_type_with_generic_string(
        self,
        request: models.MalformedContentTypeWithGenericStringInput
        | models.MalformedContentTypeWithGenericStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedContentTypeWithGenericStringOutput: ...

    @overload
    async def malformed_content_type_with_generic_string(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedContentTypeWithGenericStringInputDict],
    ) -> models.MalformedContentTypeWithGenericStringOutput:
        """
        Invokes the MalformedContentTypeWithGenericString operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedContentTypeWithGenericStringOutput`.
        """

    async def malformed_content_type_with_generic_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedContentTypeWithGenericStringOutput:
        return await self._invoke(
            self._select_input(
                models.MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING, args, kwargs
            ),
            models.MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING,
            [],
            plugins,
        )

    @overload
    async def malformed_content_type_with_payload(
        self,
        request: models.MalformedContentTypeWithPayloadInput
        | models.MalformedContentTypeWithPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedContentTypeWithPayloadOutput: ...

    @overload
    async def malformed_content_type_with_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedContentTypeWithPayloadInputDict],
    ) -> models.MalformedContentTypeWithPayloadOutput:
        """
        Invokes the MalformedContentTypeWithPayload operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedContentTypeWithPayloadOutput`.
        """

    async def malformed_content_type_with_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedContentTypeWithPayloadOutput:
        return await self._invoke(
            self._select_input(
                models.MALFORMED_CONTENT_TYPE_WITH_PAYLOAD, args, kwargs
            ),
            models.MALFORMED_CONTENT_TYPE_WITH_PAYLOAD,
            [],
            plugins,
        )

    @overload
    async def malformed_content_type_without_body(
        self,
        request: models.MalformedContentTypeWithoutBodyInput
        | models.MalformedContentTypeWithoutBodyInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedContentTypeWithoutBodyOutput: ...

    @overload
    async def malformed_content_type_without_body(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedContentTypeWithoutBodyInputDict],
    ) -> models.MalformedContentTypeWithoutBodyOutput:
        """
        Invokes the MalformedContentTypeWithoutBody operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedContentTypeWithoutBodyOutput`.
        """

    async def malformed_content_type_without_body(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedContentTypeWithoutBodyOutput:
        return await self._invoke(
            self._select_input(
                models.MALFORMED_CONTENT_TYPE_WITHOUT_BODY, args, kwargs
            ),
            models.MALFORMED_CONTENT_TYPE_WITHOUT_BODY,
            [],
            plugins,
        )

    @overload
    async def malformed_content_type_without_body_empty_input(
        self,
        request: models.MalformedContentTypeWithoutBodyEmptyInputInput
        | models.MalformedContentTypeWithoutBodyEmptyInputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedContentTypeWithoutBodyEmptyInputOutput: ...

    @overload
    async def malformed_content_type_without_body_empty_input(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedContentTypeWithoutBodyEmptyInputInputDict],
    ) -> models.MalformedContentTypeWithoutBodyEmptyInputOutput:
        """
        Invokes the MalformedContentTypeWithoutBodyEmptyInput operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedContentTypeWithoutBodyEmptyInputOutput`.
        """

    async def malformed_content_type_without_body_empty_input(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedContentTypeWithoutBodyEmptyInputOutput:
        return await self._invoke(
            self._select_input(
                models.MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT, args, kwargs
            ),
            models.MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT,
            [],
            plugins,
        )

    @overload
    async def malformed_double(
        self,
        request: models.MalformedDoubleInput | models.MalformedDoubleInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedDoubleOutput: ...

    @overload
    async def malformed_double(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedDoubleInputDict],
    ) -> models.MalformedDoubleOutput:
        """
        Invokes the MalformedDouble operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedDoubleOutput`.
        """

    async def malformed_double(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedDoubleOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_DOUBLE, args, kwargs),
            models.MALFORMED_DOUBLE,
            [],
            plugins,
        )

    @overload
    async def malformed_float(
        self,
        request: models.MalformedFloatInput | models.MalformedFloatInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedFloatOutput: ...

    @overload
    async def malformed_float(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedFloatInputDict],
    ) -> models.MalformedFloatOutput:
        """
        Invokes the MalformedFloat operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedFloatOutput`.
        """

    async def malformed_float(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedFloatOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_FLOAT, args, kwargs),
            models.MALFORMED_FLOAT,
            [],
            plugins,
        )

    @overload
    async def malformed_integer(
        self,
        request: models.MalformedIntegerInput | models.MalformedIntegerInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedIntegerOutput: ...

    @overload
    async def malformed_integer(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedIntegerInputDict],
    ) -> models.MalformedIntegerOutput:
        """
        Invokes the MalformedInteger operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedIntegerOutput`.
        """

    async def malformed_integer(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedIntegerOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_INTEGER, args, kwargs),
            models.MALFORMED_INTEGER,
            [],
            plugins,
        )

    @overload
    async def malformed_list(
        self,
        request: models.MalformedListInput | models.MalformedListInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedListOutput: ...

    @overload
    async def malformed_list(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedListInputDict],
    ) -> models.MalformedListOutput:
        """
        Invokes the MalformedList operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedListOutput`.
        """

    async def malformed_list(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedListOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_LIST, args, kwargs),
            models.MALFORMED_LIST,
            [],
            plugins,
        )

    @overload
    async def malformed_long(
        self,
        request: models.MalformedLongInput | models.MalformedLongInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedLongOutput: ...

    @overload
    async def malformed_long(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedLongInputDict],
    ) -> models.MalformedLongOutput:
        """
        Invokes the MalformedLong operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedLongOutput`.
        """

    async def malformed_long(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedLongOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_LONG, args, kwargs),
            models.MALFORMED_LONG,
            [],
            plugins,
        )

    @overload
    async def malformed_map(
        self,
        request: models.MalformedMapInput | models.MalformedMapInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedMapOutput: ...

    @overload
    async def malformed_map(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedMapInputDict],
    ) -> models.MalformedMapOutput:
        """
        Invokes the MalformedMap operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedMapOutput`.
        """

    async def malformed_map(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedMapOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_MAP, args, kwargs),
            models.MALFORMED_MAP,
            [],
            plugins,
        )

    @overload
    async def malformed_request_body(
        self,
        request: models.MalformedRequestBodyInput
        | models.MalformedRequestBodyInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedRequestBodyOutput: ...

    @overload
    async def malformed_request_body(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedRequestBodyInputDict],
    ) -> models.MalformedRequestBodyOutput:
        """
        Invokes the MalformedRequestBody operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedRequestBodyOutput`.
        """

    async def malformed_request_body(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedRequestBodyOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_REQUEST_BODY, args, kwargs),
            models.MALFORMED_REQUEST_BODY,
            [],
            plugins,
        )

    @overload
    async def malformed_short(
        self,
        request: models.MalformedShortInput | models.MalformedShortInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedShortOutput: ...

    @overload
    async def malformed_short(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedShortInputDict],
    ) -> models.MalformedShortOutput:
        """
        Invokes the MalformedShort operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedShortOutput`.
        """

    async def malformed_short(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedShortOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_SHORT, args, kwargs),
            models.MALFORMED_SHORT,
            [],
            plugins,
        )

    @overload
    async def malformed_string(
        self,
        request: models.MalformedStringInput | models.MalformedStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedStringOutput: ...

    @overload
    async def malformed_string(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedStringInputDict],
    ) -> models.MalformedStringOutput:
        """
        Invokes the MalformedString operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedStringOutput`.
        """

    async def malformed_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedStringOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_STRING, args, kwargs),
            models.MALFORMED_STRING,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_body_date_time(
        self,
        request: models.MalformedTimestampBodyDateTimeInput
        | models.MalformedTimestampBodyDateTimeInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampBodyDateTimeOutput: ...

    @overload
    async def malformed_timestamp_body_date_time(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampBodyDateTimeInputDict],
    ) -> models.MalformedTimestampBodyDateTimeOutput:
        """
        Invokes the MalformedTimestampBodyDateTime operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampBodyDateTimeOutput`.
        """

    async def malformed_timestamp_body_date_time(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampBodyDateTimeOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_BODY_DATE_TIME, args, kwargs),
            models.MALFORMED_TIMESTAMP_BODY_DATE_TIME,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_body_default(
        self,
        request: models.MalformedTimestampBodyDefaultInput
        | models.MalformedTimestampBodyDefaultInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampBodyDefaultOutput: ...

    @overload
    async def malformed_timestamp_body_default(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampBodyDefaultInputDict],
    ) -> models.MalformedTimestampBodyDefaultOutput:
        """
        Invokes the MalformedTimestampBodyDefault operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampBodyDefaultOutput`.
        """

    async def malformed_timestamp_body_default(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampBodyDefaultOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_BODY_DEFAULT, args, kwargs),
            models.MALFORMED_TIMESTAMP_BODY_DEFAULT,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_body_http_date(
        self,
        request: models.MalformedTimestampBodyHttpDateInput
        | models.MalformedTimestampBodyHttpDateInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampBodyHttpDateOutput: ...

    @overload
    async def malformed_timestamp_body_http_date(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampBodyHttpDateInputDict],
    ) -> models.MalformedTimestampBodyHttpDateOutput:
        """
        Invokes the MalformedTimestampBodyHttpDate operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampBodyHttpDateOutput`.
        """

    async def malformed_timestamp_body_http_date(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampBodyHttpDateOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_BODY_HTTP_DATE, args, kwargs),
            models.MALFORMED_TIMESTAMP_BODY_HTTP_DATE,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_header_date_time(
        self,
        request: models.MalformedTimestampHeaderDateTimeInput
        | models.MalformedTimestampHeaderDateTimeInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampHeaderDateTimeOutput: ...

    @overload
    async def malformed_timestamp_header_date_time(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampHeaderDateTimeInputDict],
    ) -> models.MalformedTimestampHeaderDateTimeOutput:
        """
        Invokes the MalformedTimestampHeaderDateTime operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampHeaderDateTimeOutput`.
        """

    async def malformed_timestamp_header_date_time(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampHeaderDateTimeOutput:
        return await self._invoke(
            self._select_input(
                models.MALFORMED_TIMESTAMP_HEADER_DATE_TIME, args, kwargs
            ),
            models.MALFORMED_TIMESTAMP_HEADER_DATE_TIME,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_header_default(
        self,
        request: models.MalformedTimestampHeaderDefaultInput
        | models.MalformedTimestampHeaderDefaultInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampHeaderDefaultOutput: ...

    @overload
    async def malformed_timestamp_header_default(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampHeaderDefaultInputDict],
    ) -> models.MalformedTimestampHeaderDefaultOutput:
        """
        Invokes the MalformedTimestampHeaderDefault operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampHeaderDefaultOutput`.
        """

    async def malformed_timestamp_header_default(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampHeaderDefaultOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_HEADER_DEFAULT, args, kwargs),
            models.MALFORMED_TIMESTAMP_HEADER_DEFAULT,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_header_epoch(
        self,
        request: models.MalformedTimestampHeaderEpochInput
        | models.MalformedTimestampHeaderEpochInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampHeaderEpochOutput: ...

    @overload
    async def malformed_timestamp_header_epoch(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampHeaderEpochInputDict],
    ) -> models.MalformedTimestampHeaderEpochOutput:
        """
        Invokes the MalformedTimestampHeaderEpoch operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampHeaderEpochOutput`.
        """

    async def malformed_timestamp_header_epoch(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampHeaderEpochOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_HEADER_EPOCH, args, kwargs),
            models.MALFORMED_TIMESTAMP_HEADER_EPOCH,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_path_default(
        self,
        request: models.MalformedTimestampPathDefaultInput
        | models.MalformedTimestampPathDefaultInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampPathDefaultOutput: ...

    @overload
    async def malformed_timestamp_path_default(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampPathDefaultInputDict],
    ) -> models.MalformedTimestampPathDefaultOutput:
        """
        Invokes the MalformedTimestampPathDefault operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampPathDefaultOutput`.
        """

    async def malformed_timestamp_path_default(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampPathDefaultOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_PATH_DEFAULT, args, kwargs),
            models.MALFORMED_TIMESTAMP_PATH_DEFAULT,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_path_epoch(
        self,
        request: models.MalformedTimestampPathEpochInput
        | models.MalformedTimestampPathEpochInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampPathEpochOutput: ...

    @overload
    async def malformed_timestamp_path_epoch(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampPathEpochInputDict],
    ) -> models.MalformedTimestampPathEpochOutput:
        """
        Invokes the MalformedTimestampPathEpoch operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampPathEpochOutput`.
        """

    async def malformed_timestamp_path_epoch(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampPathEpochOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_PATH_EPOCH, args, kwargs),
            models.MALFORMED_TIMESTAMP_PATH_EPOCH,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_path_http_date(
        self,
        request: models.MalformedTimestampPathHttpDateInput
        | models.MalformedTimestampPathHttpDateInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampPathHttpDateOutput: ...

    @overload
    async def malformed_timestamp_path_http_date(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampPathHttpDateInputDict],
    ) -> models.MalformedTimestampPathHttpDateOutput:
        """
        Invokes the MalformedTimestampPathHttpDate operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampPathHttpDateOutput`.
        """

    async def malformed_timestamp_path_http_date(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampPathHttpDateOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_PATH_HTTP_DATE, args, kwargs),
            models.MALFORMED_TIMESTAMP_PATH_HTTP_DATE,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_query_default(
        self,
        request: models.MalformedTimestampQueryDefaultInput
        | models.MalformedTimestampQueryDefaultInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampQueryDefaultOutput: ...

    @overload
    async def malformed_timestamp_query_default(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampQueryDefaultInputDict],
    ) -> models.MalformedTimestampQueryDefaultOutput:
        """
        Invokes the MalformedTimestampQueryDefault operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampQueryDefaultOutput`.
        """

    async def malformed_timestamp_query_default(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampQueryDefaultOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_QUERY_DEFAULT, args, kwargs),
            models.MALFORMED_TIMESTAMP_QUERY_DEFAULT,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_query_epoch(
        self,
        request: models.MalformedTimestampQueryEpochInput
        | models.MalformedTimestampQueryEpochInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampQueryEpochOutput: ...

    @overload
    async def malformed_timestamp_query_epoch(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampQueryEpochInputDict],
    ) -> models.MalformedTimestampQueryEpochOutput:
        """
        Invokes the MalformedTimestampQueryEpoch operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampQueryEpochOutput`.
        """

    async def malformed_timestamp_query_epoch(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampQueryEpochOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_QUERY_EPOCH, args, kwargs),
            models.MALFORMED_TIMESTAMP_QUERY_EPOCH,
            [],
            plugins,
        )

    @overload
    async def malformed_timestamp_query_http_date(
        self,
        request: models.MalformedTimestampQueryHttpDateInput
        | models.MalformedTimestampQueryHttpDateInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampQueryHttpDateOutput: ...

    @overload
    async def malformed_timestamp_query_http_date(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedTimestampQueryHttpDateInputDict],
    ) -> models.MalformedTimestampQueryHttpDateOutput:
        """
        Invokes the MalformedTimestampQueryHttpDate operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedTimestampQueryHttpDateOutput`.
        """

    async def malformed_timestamp_query_http_date(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampQueryHttpDateOutput:
        return await self._invoke(
            self._select_input(
                models.MALFORMED_TIMESTAMP_QUERY_HTTP_DATE, args, kwargs
            ),
            models.MALFORMED_TIMESTAMP_QUERY_HTTP_DATE,
            [],
            plugins,
        )

    @overload
    async def malformed_union(
        self,
        request: models.MalformedUnionInput | models.MalformedUnionInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedUnionOutput: ...

    @overload
    async def malformed_union(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MalformedUnionInputDict],
    ) -> models.MalformedUnionOutput:
        """
        Invokes the MalformedUnion operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MalformedUnionOutput`.
        """

    async def malformed_union(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedUnionOutput:
        return await self._invoke(
            self._select_input(models.MALFORMED_UNION, args, kwargs),
            models.MALFORMED_UNION,
            [],
            plugins,
        )

    @overload
    async def media_type_header(
        self,
        request: models.MediaTypeHeaderInput | models.MediaTypeHeaderInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MediaTypeHeaderOutput: ...

    @overload
    async def media_type_header(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.MediaTypeHeaderInputDict],
    ) -> models.MediaTypeHeaderOutput:
        """
        This example ensures that mediaType strings are base64 encoded in
        headers.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `MediaTypeHeaderOutput`.
        """

    async def media_type_header(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MediaTypeHeaderOutput:
        return await self._invoke(
            self._select_input(models.MEDIA_TYPE_HEADER, args, kwargs),
            models.MEDIA_TYPE_HEADER,
            [],
            plugins,
        )

    @overload
    async def no_input_and_no_output(
        self,
        request: models.NoInputAndNoOutputInput | models.NoInputAndNoOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NoInputAndNoOutputOutput: ...

    @overload
    async def no_input_and_no_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NoInputAndNoOutputInputDict],
    ) -> models.NoInputAndNoOutputOutput:
        """
        The example tests how requests and responses are serialized when there's
        no request or response payload because the operation has no input or
        output.
        While this should be rare, code generators must support this.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `NoInputAndNoOutputOutput`.
        """

    async def no_input_and_no_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NoInputAndNoOutputOutput:
        return await self._invoke(
            self._select_input(models.NO_INPUT_AND_NO_OUTPUT, args, kwargs),
            models.NO_INPUT_AND_NO_OUTPUT,
            [],
            plugins,
        )

    @overload
    async def no_input_and_output(
        self,
        request: models.NoInputAndOutputInput | models.NoInputAndOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NoInputAndOutputOutput: ...

    @overload
    async def no_input_and_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NoInputAndOutputInputDict],
    ) -> models.NoInputAndOutputOutput:
        """
        The example tests how requests and responses are serialized when there's
        no request or response payload because the operation has no input and
        the
        output is empty. While this should be rare, code generators must support
        this.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `NoInputAndOutputOutput`.
        """

    async def no_input_and_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NoInputAndOutputOutput:
        return await self._invoke(
            self._select_input(models.NO_INPUT_AND_OUTPUT, args, kwargs),
            models.NO_INPUT_AND_OUTPUT,
            [],
            plugins,
        )

    @overload
    async def null_and_empty_headers_client(
        self,
        request: models.NullAndEmptyHeadersClientInput
        | models.NullAndEmptyHeadersClientInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NullAndEmptyHeadersClientOutput: ...

    @overload
    async def null_and_empty_headers_client(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NullAndEmptyHeadersClientInputDict],
    ) -> models.NullAndEmptyHeadersClientOutput:
        """
        Null headers are not sent over the wire, empty headers are serialized to
        ""

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `NullAndEmptyHeadersClientOutput`.
        """

    async def null_and_empty_headers_client(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NullAndEmptyHeadersClientOutput:
        return await self._invoke(
            self._select_input(models.NULL_AND_EMPTY_HEADERS_CLIENT, args, kwargs),
            models.NULL_AND_EMPTY_HEADERS_CLIENT,
            [],
            plugins,
        )

    @overload
    async def null_and_empty_headers_server(
        self,
        request: models.NullAndEmptyHeadersServerInput
        | models.NullAndEmptyHeadersServerInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NullAndEmptyHeadersServerOutput: ...

    @overload
    async def null_and_empty_headers_server(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NullAndEmptyHeadersServerInputDict],
    ) -> models.NullAndEmptyHeadersServerOutput:
        """
        Null headers are not sent over the wire, empty headers are serialized to
        ""

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `NullAndEmptyHeadersServerOutput`.
        """

    async def null_and_empty_headers_server(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NullAndEmptyHeadersServerOutput:
        return await self._invoke(
            self._select_input(models.NULL_AND_EMPTY_HEADERS_SERVER, args, kwargs),
            models.NULL_AND_EMPTY_HEADERS_SERVER,
            [],
            plugins,
        )

    @overload
    async def omits_null_serializes_empty_string(
        self,
        request: models.OmitsNullSerializesEmptyStringInput
        | models.OmitsNullSerializesEmptyStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OmitsNullSerializesEmptyStringOutput: ...

    @overload
    async def omits_null_serializes_empty_string(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.OmitsNullSerializesEmptyStringInputDict],
    ) -> models.OmitsNullSerializesEmptyStringOutput:
        """
        Omits null, but serializes empty string value.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `OmitsNullSerializesEmptyStringOutput`.
        """

    async def omits_null_serializes_empty_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OmitsNullSerializesEmptyStringOutput:
        return await self._invoke(
            self._select_input(models.OMITS_NULL_SERIALIZES_EMPTY_STRING, args, kwargs),
            models.OMITS_NULL_SERIALIZES_EMPTY_STRING,
            [],
            plugins,
        )

    @overload
    async def omits_serializing_empty_lists(
        self,
        request: models.OmitsSerializingEmptyListsInput
        | models.OmitsSerializingEmptyListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OmitsSerializingEmptyListsOutput: ...

    @overload
    async def omits_serializing_empty_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.OmitsSerializingEmptyListsInputDict],
    ) -> models.OmitsSerializingEmptyListsOutput:
        """
        Omits serializing empty lists. Because empty strings are serilized as
        `Foo=`, empty lists cannot also be serialized as `Foo=` and instead
        must be omitted.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `OmitsSerializingEmptyListsOutput`.
        """

    async def omits_serializing_empty_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OmitsSerializingEmptyListsOutput:
        return await self._invoke(
            self._select_input(models.OMITS_SERIALIZING_EMPTY_LISTS, args, kwargs),
            models.OMITS_SERIALIZING_EMPTY_LISTS,
            [],
            plugins,
        )

    @overload
    async def operation_with_defaults(
        self,
        request: models.OperationWithDefaultsInput
        | models.OperationWithDefaultsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OperationWithDefaultsOutput: ...

    @overload
    async def operation_with_defaults(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.OperationWithDefaultsInputDict],
    ) -> models.OperationWithDefaultsOutput:
        """
        Invokes the OperationWithDefaults operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `OperationWithDefaultsOutput`.
        """

    async def operation_with_defaults(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OperationWithDefaultsOutput:
        return await self._invoke(
            self._select_input(models.OPERATION_WITH_DEFAULTS, args, kwargs),
            models.OPERATION_WITH_DEFAULTS,
            [],
            plugins,
        )

    @overload
    async def operation_with_nested_structure(
        self,
        request: models.OperationWithNestedStructureInput
        | models.OperationWithNestedStructureInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OperationWithNestedStructureOutput: ...

    @overload
    async def operation_with_nested_structure(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.OperationWithNestedStructureInputDict],
    ) -> models.OperationWithNestedStructureOutput:
        """
        Invokes the OperationWithNestedStructure operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `OperationWithNestedStructureOutput`.
        """

    async def operation_with_nested_structure(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OperationWithNestedStructureOutput:
        return await self._invoke(
            self._select_input(models.OPERATION_WITH_NESTED_STRUCTURE, args, kwargs),
            models.OPERATION_WITH_NESTED_STRUCTURE,
            [],
            plugins,
        )

    @overload
    async def post_player_action(
        self,
        request: models.PostPlayerActionInput | models.PostPlayerActionInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PostPlayerActionOutput: ...

    @overload
    async def post_player_action(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.PostPlayerActionInputDict],
    ) -> models.PostPlayerActionOutput:
        """
        This operation defines a union with a Unit member.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `PostPlayerActionOutput`.
        """

    async def post_player_action(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PostPlayerActionOutput:
        return await self._invoke(
            self._select_input(models.POST_PLAYER_ACTION, args, kwargs),
            models.POST_PLAYER_ACTION,
            [],
            plugins,
        )

    @overload
    async def post_union_with_json_name(
        self,
        request: models.PostUnionWithJsonNameInput
        | models.PostUnionWithJsonNameInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PostUnionWithJsonNameOutput: ...

    @overload
    async def post_union_with_json_name(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.PostUnionWithJsonNameInputDict],
    ) -> models.PostUnionWithJsonNameOutput:
        """
        This operation defines a union that uses jsonName on some members.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `PostUnionWithJsonNameOutput`.
        """

    async def post_union_with_json_name(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PostUnionWithJsonNameOutput:
        return await self._invoke(
            self._select_input(models.POST_UNION_WITH_JSON_NAME, args, kwargs),
            models.POST_UNION_WITH_JSON_NAME,
            [],
            plugins,
        )

    @overload
    async def put_with_content_encoding(
        self,
        request: models.PutWithContentEncodingInput
        | models.PutWithContentEncodingInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PutWithContentEncodingOutput: ...

    @overload
    async def put_with_content_encoding(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.PutWithContentEncodingInputDict],
    ) -> models.PutWithContentEncodingOutput:
        """
        Invokes the PutWithContentEncoding operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `PutWithContentEncodingOutput`.
        """

    async def put_with_content_encoding(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PutWithContentEncodingOutput:
        return await self._invoke(
            self._select_input(models.PUT_WITH_CONTENT_ENCODING, args, kwargs),
            models.PUT_WITH_CONTENT_ENCODING,
            [],
            plugins,
        )

    @overload
    async def query_idempotency_token_auto_fill(
        self,
        request: models.QueryIdempotencyTokenAutoFillInput
        | models.QueryIdempotencyTokenAutoFillInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryIdempotencyTokenAutoFillOutput: ...

    @overload
    async def query_idempotency_token_auto_fill(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.QueryIdempotencyTokenAutoFillInputDict],
    ) -> models.QueryIdempotencyTokenAutoFillOutput:
        """
        Automatically adds idempotency tokens.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `QueryIdempotencyTokenAutoFillOutput`.
        """

    async def query_idempotency_token_auto_fill(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryIdempotencyTokenAutoFillOutput:
        return await self._invoke(
            self._select_input(models.QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL, args, kwargs),
            models.QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL,
            [],
            plugins,
        )

    @overload
    async def query_params_as_string_list_map(
        self,
        request: models.QueryParamsAsStringListMapInput
        | models.QueryParamsAsStringListMapInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryParamsAsStringListMapOutput: ...

    @overload
    async def query_params_as_string_list_map(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.QueryParamsAsStringListMapInputDict],
    ) -> models.QueryParamsAsStringListMapOutput:
        """
        Invokes the QueryParamsAsStringListMap operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `QueryParamsAsStringListMapOutput`.
        """

    async def query_params_as_string_list_map(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryParamsAsStringListMapOutput:
        return await self._invoke(
            self._select_input(models.QUERY_PARAMS_AS_STRING_LIST_MAP, args, kwargs),
            models.QUERY_PARAMS_AS_STRING_LIST_MAP,
            [],
            plugins,
        )

    @overload
    async def query_precedence(
        self,
        request: models.QueryPrecedenceInput | models.QueryPrecedenceInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryPrecedenceOutput: ...

    @overload
    async def query_precedence(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.QueryPrecedenceInputDict],
    ) -> models.QueryPrecedenceOutput:
        """
        Invokes the QueryPrecedence operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `QueryPrecedenceOutput`.
        """

    async def query_precedence(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryPrecedenceOutput:
        return await self._invoke(
            self._select_input(models.QUERY_PRECEDENCE, args, kwargs),
            models.QUERY_PRECEDENCE,
            [],
            plugins,
        )

    @overload
    async def recursive_shapes(
        self,
        request: models.RecursiveShapesInput | models.RecursiveShapesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.RecursiveShapesOutput: ...

    @overload
    async def recursive_shapes(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.RecursiveShapesInputDict],
    ) -> models.RecursiveShapesOutput:
        """
        Recursive shapes

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `RecursiveShapesOutput`.
        """

    async def recursive_shapes(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.RecursiveShapesOutput:
        return await self._invoke(
            self._select_input(models.RECURSIVE_SHAPES, args, kwargs),
            models.RECURSIVE_SHAPES,
            [],
            plugins,
        )

    @overload
    async def response_code_http_fallback(
        self,
        request: models.ResponseCodeHttpFallbackInput
        | models.ResponseCodeHttpFallbackInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ResponseCodeHttpFallbackOutput: ...

    @overload
    async def response_code_http_fallback(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.ResponseCodeHttpFallbackInputDict],
    ) -> models.ResponseCodeHttpFallbackOutput:
        """
        Invokes the ResponseCodeHttpFallback operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `ResponseCodeHttpFallbackOutput`.
        """

    async def response_code_http_fallback(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ResponseCodeHttpFallbackOutput:
        return await self._invoke(
            self._select_input(models.RESPONSE_CODE_HTTP_FALLBACK, args, kwargs),
            models.RESPONSE_CODE_HTTP_FALLBACK,
            [],
            plugins,
        )

    @overload
    async def response_code_required(
        self,
        request: models.ResponseCodeRequiredInput
        | models.ResponseCodeRequiredInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ResponseCodeRequiredOutput: ...

    @overload
    async def response_code_required(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.ResponseCodeRequiredInputDict],
    ) -> models.ResponseCodeRequiredOutput:
        """
        Invokes the ResponseCodeRequired operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `ResponseCodeRequiredOutput`.
        """

    async def response_code_required(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ResponseCodeRequiredOutput:
        return await self._invoke(
            self._select_input(models.RESPONSE_CODE_REQUIRED, args, kwargs),
            models.RESPONSE_CODE_REQUIRED,
            [],
            plugins,
        )

    @overload
    async def simple_scalar_properties(
        self,
        request: models.SimpleScalarPropertiesInput
        | models.SimpleScalarPropertiesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SimpleScalarPropertiesOutput: ...

    @overload
    async def simple_scalar_properties(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.SimpleScalarPropertiesInputDict],
    ) -> models.SimpleScalarPropertiesOutput:
        """
        Invokes the SimpleScalarProperties operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `SimpleScalarPropertiesOutput`.
        """

    async def simple_scalar_properties(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SimpleScalarPropertiesOutput:
        return await self._invoke(
            self._select_input(models.SIMPLE_SCALAR_PROPERTIES, args, kwargs),
            models.SIMPLE_SCALAR_PROPERTIES,
            [],
            plugins,
        )

    @overload
    async def sparse_json_lists(
        self,
        request: models.SparseJsonListsInput | models.SparseJsonListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SparseJsonListsOutput: ...

    @overload
    async def sparse_json_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.SparseJsonListsInputDict],
    ) -> models.SparseJsonListsOutput:
        """
        Invokes the SparseJsonLists operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `SparseJsonListsOutput`.
        """

    async def sparse_json_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SparseJsonListsOutput:
        return await self._invoke(
            self._select_input(models.SPARSE_JSON_LISTS, args, kwargs),
            models.SPARSE_JSON_LISTS,
            [],
            plugins,
        )

    @overload
    async def sparse_json_maps(
        self,
        request: models.SparseJsonMapsInput | models.SparseJsonMapsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SparseJsonMapsOutput: ...

    @overload
    async def sparse_json_maps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.SparseJsonMapsInputDict],
    ) -> models.SparseJsonMapsOutput:
        """
        This example tests sparse map serialization.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `SparseJsonMapsOutput`.
        """

    async def sparse_json_maps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SparseJsonMapsOutput:
        return await self._invoke(
            self._select_input(models.SPARSE_JSON_MAPS, args, kwargs),
            models.SPARSE_JSON_MAPS,
            [],
            plugins,
        )

    @overload
    async def test_body_structure(
        self,
        request: models.TestBodyStructureInput | models.TestBodyStructureInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestBodyStructureOutput: ...

    @overload
    async def test_body_structure(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestBodyStructureInputDict],
    ) -> models.TestBodyStructureOutput:
        """
        This example operation serializes a structure in the HTTP body.

        It should ensure Content-Type: application/json is
        used in all requests and that an "empty" body is
        an empty JSON document ({}).


        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestBodyStructureOutput`.
        """

    async def test_body_structure(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestBodyStructureOutput:
        return await self._invoke(
            self._select_input(models.TEST_BODY_STRUCTURE, args, kwargs),
            models.TEST_BODY_STRUCTURE,
            [],
            plugins,
        )

    @overload
    async def test_get_no_input_no_payload(
        self,
        request: models.TestGetNoInputNoPayloadInput
        | models.TestGetNoInputNoPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestGetNoInputNoPayloadOutput: ...

    @overload
    async def test_get_no_input_no_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestGetNoInputNoPayloadInputDict],
    ) -> models.TestGetNoInputNoPayloadOutput:
        """
        This example GET operation has no input and serializes a request without
        a HTTP body.

        These tests are to ensure we do not attach a body or related headers
        (Content-Length, Content-Type) to operations that semantically
        cannot produce an HTTP body.


        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestGetNoInputNoPayloadOutput`.
        """

    async def test_get_no_input_no_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestGetNoInputNoPayloadOutput:
        return await self._invoke(
            self._select_input(models.TEST_GET_NO_INPUT_NO_PAYLOAD, args, kwargs),
            models.TEST_GET_NO_INPUT_NO_PAYLOAD,
            [],
            plugins,
        )

    @overload
    async def test_get_no_payload(
        self,
        request: models.TestGetNoPayloadInput | models.TestGetNoPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestGetNoPayloadOutput: ...

    @overload
    async def test_get_no_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestGetNoPayloadInputDict],
    ) -> models.TestGetNoPayloadOutput:
        """
        This example GET operation serializes a request without a modeled HTTP
        body.

        These tests are to ensure we do not attach a body or related headers
        (Content-Length, Content-Type) to operations that semantically
        cannot produce an HTTP body.


        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestGetNoPayloadOutput`.
        """

    async def test_get_no_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestGetNoPayloadOutput:
        return await self._invoke(
            self._select_input(models.TEST_GET_NO_PAYLOAD, args, kwargs),
            models.TEST_GET_NO_PAYLOAD,
            [],
            plugins,
        )

    @overload
    async def test_payload_blob(
        self,
        request: models.TestPayloadBlobInput | models.TestPayloadBlobInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestPayloadBlobOutput: ...

    @overload
    async def test_payload_blob(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestPayloadBlobInputDict],
    ) -> models.TestPayloadBlobOutput:
        """
        This example operation serializes a payload targeting a blob.

        The Blob shape is not structured content and we cannot
        make assumptions about what data will be sent. This test ensures
        only a generic "Content-Type: application/octet-stream" header
        is used, and that we are not treating an empty body as an
        empty JSON document.


        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestPayloadBlobOutput`.
        """

    async def test_payload_blob(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestPayloadBlobOutput:
        return await self._invoke(
            self._select_input(models.TEST_PAYLOAD_BLOB, args, kwargs),
            models.TEST_PAYLOAD_BLOB,
            [],
            plugins,
        )

    @overload
    async def test_payload_structure(
        self,
        request: models.TestPayloadStructureInput
        | models.TestPayloadStructureInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestPayloadStructureOutput: ...

    @overload
    async def test_payload_structure(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestPayloadStructureInputDict],
    ) -> models.TestPayloadStructureOutput:
        """
        This example operation serializes a payload targeting a structure.

        This enforces the same requirements as TestBodyStructure
        but with the body specified by the @httpPayload trait.


        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestPayloadStructureOutput`.
        """

    async def test_payload_structure(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestPayloadStructureOutput:
        return await self._invoke(
            self._select_input(models.TEST_PAYLOAD_STRUCTURE, args, kwargs),
            models.TEST_PAYLOAD_STRUCTURE,
            [],
            plugins,
        )

    @overload
    async def test_post_no_input_no_payload(
        self,
        request: models.TestPostNoInputNoPayloadInput
        | models.TestPostNoInputNoPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestPostNoInputNoPayloadOutput: ...

    @overload
    async def test_post_no_input_no_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestPostNoInputNoPayloadInputDict],
    ) -> models.TestPostNoInputNoPayloadOutput:
        """
        This example POST operation has no input and serializes a request
        without a HTTP body.

        These tests are to ensure we do not attach a body or related headers
        (Content-Type) to a POST operation with no modeled input.


        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestPostNoInputNoPayloadOutput`.
        """

    async def test_post_no_input_no_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestPostNoInputNoPayloadOutput:
        return await self._invoke(
            self._select_input(models.TEST_POST_NO_INPUT_NO_PAYLOAD, args, kwargs),
            models.TEST_POST_NO_INPUT_NO_PAYLOAD,
            [],
            plugins,
        )

    @overload
    async def test_post_no_payload(
        self,
        request: models.TestPostNoPayloadInput | models.TestPostNoPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestPostNoPayloadOutput: ...

    @overload
    async def test_post_no_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestPostNoPayloadInputDict],
    ) -> models.TestPostNoPayloadOutput:
        """
        This example POST operation serializes a request without a modeled HTTP
        body.

        These tests are to ensure we do not attach a body or related headers
        (Content-Type) to a POST operation with no modeled payload.


        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestPostNoPayloadOutput`.
        """

    async def test_post_no_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestPostNoPayloadOutput:
        return await self._invoke(
            self._select_input(models.TEST_POST_NO_PAYLOAD, args, kwargs),
            models.TEST_POST_NO_PAYLOAD,
            [],
            plugins,
        )

    @overload
    async def timestamp_format_headers(
        self,
        request: models.TimestampFormatHeadersInput
        | models.TimestampFormatHeadersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TimestampFormatHeadersOutput: ...

    @overload
    async def timestamp_format_headers(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TimestampFormatHeadersInputDict],
    ) -> models.TimestampFormatHeadersOutput:
        """
        This example tests how timestamp request and response headers are
        serialized.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TimestampFormatHeadersOutput`.
        """

    async def timestamp_format_headers(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TimestampFormatHeadersOutput:
        return await self._invoke(
            self._select_input(models.TIMESTAMP_FORMAT_HEADERS, args, kwargs),
            models.TIMESTAMP_FORMAT_HEADERS,
            [],
            plugins,
        )

    @overload
    async def unit_input_and_output(
        self,
        request: models.UnitInputAndOutputInput | models.UnitInputAndOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.UnitInputAndOutputOutput: ...

    @overload
    async def unit_input_and_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.UnitInputAndOutputInputDict],
    ) -> models.UnitInputAndOutputOutput:
        """
        This test is similar to NoInputAndNoOutput, but uses explicit Unit
        types.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `UnitInputAndOutputOutput`.
        """

    async def unit_input_and_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.UnitInputAndOutputOutput:
        return await self._invoke(
            self._select_input(models.UNIT_INPUT_AND_OUTPUT, args, kwargs),
            models.UNIT_INPUT_AND_OUTPUT,
            [],
            plugins,
        )

    async def _new_config(self) -> AsyncRestJsonProtocolConfig:
        return await AsyncRestJsonProtocolConfig.resolve()

    async def _post_setup(self, config: AsyncRestJsonProtocolConfig) -> None:
        if config.aws_credentials_identity_resolver is None:
            config_context = config.resolution_context()
            config_file = None
            profile_name = None
            if config_context is not None:
                config_file = await config_context.parsed_profiles()
                if config_context.profile_source is ConfigSource.OVERRIDE:
                    profile_name = config_context.profile_name
            config.aws_credentials_identity_resolver = await AsyncIdentityChain.create(
                AWSCredentialsIdentity,
                config_file=config_file,
                profile_name=profile_name,
                region_override=config.region,
                http_client=cast(AsyncHTTPClient | None, config.transport),
            )
