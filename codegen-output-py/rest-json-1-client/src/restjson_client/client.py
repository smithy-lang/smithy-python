from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.chain.resolver import IdentityChain
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.client import Client
from smithy_http.interfaces import HTTPClient
from smithy_http.plugins import user_agent_plugin

from restjson_client import models
from restjson_client.config import Plugin, RestJsonProtocolConfig
from restjson_client.user_agent import aws_user_agent_plugin


class RestJsonProtocolClient(Client[RestJsonProtocolConfig]):
    "Client for RestJson."

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

    @overload
    def all_query_string_types(
        self,
        request: models.AllQueryStringTypesInput | models.AllQueryStringTypesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.AllQueryStringTypesOutput: ...

    @overload
    def all_query_string_types(
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

    def all_query_string_types(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.AllQueryStringTypesOutput:
        return self._invoke(
            self._select_input(models.ALL_QUERY_STRING_TYPES, args, kwargs),
            models.ALL_QUERY_STRING_TYPES,
            [],
            plugins,
        )

    @overload
    def constant_and_variable_query_string(
        self,
        request: models.ConstantAndVariableQueryStringInput
        | models.ConstantAndVariableQueryStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ConstantAndVariableQueryStringOutput: ...

    @overload
    def constant_and_variable_query_string(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.ConstantAndVariableQueryStringInputDict],
    ) -> models.ConstantAndVariableQueryStringOutput:
        """
        This example uses fixed query string params and variable query string
        params. The fixed query string parameters and variable parameters must
        both be serialized (implementations may need to merge them together).

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `ConstantAndVariableQueryStringOutput`.
        """

    def constant_and_variable_query_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ConstantAndVariableQueryStringOutput:
        return self._invoke(
            self._select_input(models.CONSTANT_AND_VARIABLE_QUERY_STRING, args, kwargs),
            models.CONSTANT_AND_VARIABLE_QUERY_STRING,
            [],
            plugins,
        )

    @overload
    def constant_query_string(
        self,
        request: models.ConstantQueryStringInput | models.ConstantQueryStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ConstantQueryStringOutput: ...

    @overload
    def constant_query_string(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.ConstantQueryStringInputDict],
    ) -> models.ConstantQueryStringOutput:
        """
        This example uses a constant query string parameters and a label. This
        simply tests that labels and query string parameters are compatible. The
        fixed query string parameter named "hello" should in no way conflict
        with the label, `{hello}`.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `ConstantQueryStringOutput`.
        """

    def constant_query_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ConstantQueryStringOutput:
        return self._invoke(
            self._select_input(models.CONSTANT_QUERY_STRING, args, kwargs),
            models.CONSTANT_QUERY_STRING,
            [],
            plugins,
        )

    @overload
    def content_type_parameters(
        self,
        request: models.ContentTypeParametersInput
        | models.ContentTypeParametersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ContentTypeParametersOutput: ...

    @overload
    def content_type_parameters(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.ContentTypeParametersInputDict],
    ) -> models.ContentTypeParametersOutput:
        """
        The example tests how servers must support requests containing a
        `Content-Type` header with parameters.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `ContentTypeParametersOutput`.
        """

    def content_type_parameters(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ContentTypeParametersOutput:
        return self._invoke(
            self._select_input(models.CONTENT_TYPE_PARAMETERS, args, kwargs),
            models.CONTENT_TYPE_PARAMETERS,
            [],
            plugins,
        )

    @overload
    def datetime_offsets(
        self,
        request: models.DatetimeOffsetsInput | models.DatetimeOffsetsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.DatetimeOffsetsOutput: ...

    @overload
    def datetime_offsets(
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

    def datetime_offsets(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.DatetimeOffsetsOutput:
        return self._invoke(
            self._select_input(models.DATETIME_OFFSETS, args, kwargs),
            models.DATETIME_OFFSETS,
            [],
            plugins,
        )

    @overload
    def document_type(
        self,
        request: models.DocumentTypeInput | models.DocumentTypeInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.DocumentTypeOutput: ...

    @overload
    def document_type(
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

    def document_type(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.DocumentTypeOutput:
        return self._invoke(
            self._select_input(models.DOCUMENT_TYPE, args, kwargs),
            models.DOCUMENT_TYPE,
            [],
            plugins,
        )

    @overload
    def document_type_as_map_value(
        self,
        request: models.DocumentTypeAsMapValueInput
        | models.DocumentTypeAsMapValueInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.DocumentTypeAsMapValueOutput: ...

    @overload
    def document_type_as_map_value(
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

    def document_type_as_map_value(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.DocumentTypeAsMapValueOutput:
        return self._invoke(
            self._select_input(models.DOCUMENT_TYPE_AS_MAP_VALUE, args, kwargs),
            models.DOCUMENT_TYPE_AS_MAP_VALUE,
            [],
            plugins,
        )

    @overload
    def document_type_as_payload(
        self,
        request: models.DocumentTypeAsPayloadInput
        | models.DocumentTypeAsPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.DocumentTypeAsPayloadOutput: ...

    @overload
    def document_type_as_payload(
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

    def document_type_as_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.DocumentTypeAsPayloadOutput:
        return self._invoke(
            self._select_input(models.DOCUMENT_TYPE_AS_PAYLOAD, args, kwargs),
            models.DOCUMENT_TYPE_AS_PAYLOAD,
            [],
            plugins,
        )

    @overload
    def empty_input_and_empty_output(
        self,
        request: models.EmptyInputAndEmptyOutputInput
        | models.EmptyInputAndEmptyOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EmptyInputAndEmptyOutputOutput: ...

    @overload
    def empty_input_and_empty_output(
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

    def empty_input_and_empty_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EmptyInputAndEmptyOutputOutput:
        return self._invoke(
            self._select_input(models.EMPTY_INPUT_AND_EMPTY_OUTPUT, args, kwargs),
            models.EMPTY_INPUT_AND_EMPTY_OUTPUT,
            [],
            plugins,
        )

    @overload
    def endpoint_operation(
        self,
        request: models.EndpointOperationInput | models.EndpointOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EndpointOperationOutput: ...

    @overload
    def endpoint_operation(
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

    def endpoint_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EndpointOperationOutput:
        return self._invoke(
            self._select_input(models.ENDPOINT_OPERATION, args, kwargs),
            models.ENDPOINT_OPERATION,
            [],
            plugins,
        )

    @overload
    def endpoint_with_host_label_operation(
        self,
        request: models.EndpointWithHostLabelOperationInput
        | models.EndpointWithHostLabelOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EndpointWithHostLabelOperationOutput: ...

    @overload
    def endpoint_with_host_label_operation(
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

    def endpoint_with_host_label_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EndpointWithHostLabelOperationOutput:
        return self._invoke(
            self._select_input(models.ENDPOINT_WITH_HOST_LABEL_OPERATION, args, kwargs),
            models.ENDPOINT_WITH_HOST_LABEL_OPERATION,
            [],
            plugins,
        )

    @overload
    def fractional_seconds(
        self,
        request: models.FractionalSecondsInput | models.FractionalSecondsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.FractionalSecondsOutput: ...

    @overload
    def fractional_seconds(
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

    def fractional_seconds(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.FractionalSecondsOutput:
        return self._invoke(
            self._select_input(models.FRACTIONAL_SECONDS, args, kwargs),
            models.FRACTIONAL_SECONDS,
            [],
            plugins,
        )

    @overload
    def greeting_with_errors(
        self,
        request: models.GreetingWithErrorsInput | models.GreetingWithErrorsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.GreetingWithErrorsOutput: ...

    @overload
    def greeting_with_errors(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.GreetingWithErrorsInputDict],
    ) -> models.GreetingWithErrorsOutput:
        """
        This operation has four possible return values: 1. A successful response
        in the form of GreetingWithErrorsOutput 2. An InvalidGreeting error. 3.
        A BadRequest error. 4. A FooError. Implementations must be able to
        successfully take a response and properly (de)serialize successful and
        error responses based on the the presence of the

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `GreetingWithErrorsOutput`.
        """

    def greeting_with_errors(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.GreetingWithErrorsOutput:
        return self._invoke(
            self._select_input(models.GREETING_WITH_ERRORS, args, kwargs),
            models.GREETING_WITH_ERRORS,
            [],
            plugins,
        )

    @overload
    def host_with_path_operation(
        self,
        request: models.HostWithPathOperationInput
        | models.HostWithPathOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HostWithPathOperationOutput: ...

    @overload
    def host_with_path_operation(
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

    def host_with_path_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HostWithPathOperationOutput:
        return self._invoke(
            self._select_input(models.HOST_WITH_PATH_OPERATION, args, kwargs),
            models.HOST_WITH_PATH_OPERATION,
            [],
            plugins,
        )

    @overload
    def http_checksum_required(
        self,
        request: models.HttpChecksumRequiredInput
        | models.HttpChecksumRequiredInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpChecksumRequiredOutput: ...

    @overload
    def http_checksum_required(
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

    def http_checksum_required(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpChecksumRequiredOutput:
        return self._invoke(
            self._select_input(models.HTTP_CHECKSUM_REQUIRED, args, kwargs),
            models.HTTP_CHECKSUM_REQUIRED,
            [],
            plugins,
        )

    @overload
    def http_empty_prefix_headers(
        self,
        request: models.HttpEmptyPrefixHeadersInput
        | models.HttpEmptyPrefixHeadersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpEmptyPrefixHeadersOutput: ...

    @overload
    def http_empty_prefix_headers(
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

    def http_empty_prefix_headers(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpEmptyPrefixHeadersOutput:
        return self._invoke(
            self._select_input(models.HTTP_EMPTY_PREFIX_HEADERS, args, kwargs),
            models.HTTP_EMPTY_PREFIX_HEADERS,
            [],
            plugins,
        )

    @overload
    def http_enum_payload(
        self,
        request: models.HttpEnumPayloadInput | models.HttpEnumPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpEnumPayloadOutput: ...

    @overload
    def http_enum_payload(
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

    def http_enum_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpEnumPayloadOutput:
        return self._invoke(
            self._select_input(models.HTTP_ENUM_PAYLOAD, args, kwargs),
            models.HTTP_ENUM_PAYLOAD,
            [],
            plugins,
        )

    @overload
    def http_payload_traits(
        self,
        request: models.HttpPayloadTraitsInput | models.HttpPayloadTraitsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadTraitsOutput: ...

    @overload
    def http_payload_traits(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPayloadTraitsInputDict],
    ) -> models.HttpPayloadTraitsOutput:
        """
        This example serializes a blob shape in the payload. In this example, no
        JSON document is synthesized because the payload is not a structure or a
        union type.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPayloadTraitsOutput`.
        """

    def http_payload_traits(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadTraitsOutput:
        return self._invoke(
            self._select_input(models.HTTP_PAYLOAD_TRAITS, args, kwargs),
            models.HTTP_PAYLOAD_TRAITS,
            [],
            plugins,
        )

    @overload
    def http_payload_traits_with_media_type(
        self,
        request: models.HttpPayloadTraitsWithMediaTypeInput
        | models.HttpPayloadTraitsWithMediaTypeInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadTraitsWithMediaTypeOutput: ...

    @overload
    def http_payload_traits_with_media_type(
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

    def http_payload_traits_with_media_type(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadTraitsWithMediaTypeOutput:
        return self._invoke(
            self._select_input(
                models.HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE, args, kwargs
            ),
            models.HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE,
            [],
            plugins,
        )

    @overload
    def http_payload_with_structure(
        self,
        request: models.HttpPayloadWithStructureInput
        | models.HttpPayloadWithStructureInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadWithStructureOutput: ...

    @overload
    def http_payload_with_structure(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPayloadWithStructureInputDict],
    ) -> models.HttpPayloadWithStructureOutput:
        """
        This example serializes a structure in the payload. Note that
        serializing a structure changes the wrapper element name to match the
        targeted structure.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPayloadWithStructureOutput`.
        """

    def http_payload_with_structure(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadWithStructureOutput:
        return self._invoke(
            self._select_input(models.HTTP_PAYLOAD_WITH_STRUCTURE, args, kwargs),
            models.HTTP_PAYLOAD_WITH_STRUCTURE,
            [],
            plugins,
        )

    @overload
    def http_payload_with_union(
        self,
        request: models.HttpPayloadWithUnionInput
        | models.HttpPayloadWithUnionInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadWithUnionOutput: ...

    @overload
    def http_payload_with_union(
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

    def http_payload_with_union(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadWithUnionOutput:
        return self._invoke(
            self._select_input(models.HTTP_PAYLOAD_WITH_UNION, args, kwargs),
            models.HTTP_PAYLOAD_WITH_UNION,
            [],
            plugins,
        )

    @overload
    def http_prefix_headers(
        self,
        request: models.HttpPrefixHeadersInput | models.HttpPrefixHeadersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPrefixHeadersOutput: ...

    @overload
    def http_prefix_headers(
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

    def http_prefix_headers(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPrefixHeadersOutput:
        return self._invoke(
            self._select_input(models.HTTP_PREFIX_HEADERS, args, kwargs),
            models.HTTP_PREFIX_HEADERS,
            [],
            plugins,
        )

    @overload
    def http_prefix_headers_in_response(
        self,
        request: models.HttpPrefixHeadersInResponseInput
        | models.HttpPrefixHeadersInResponseInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPrefixHeadersInResponseOutput: ...

    @overload
    def http_prefix_headers_in_response(
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

    def http_prefix_headers_in_response(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPrefixHeadersInResponseOutput:
        return self._invoke(
            self._select_input(models.HTTP_PREFIX_HEADERS_IN_RESPONSE, args, kwargs),
            models.HTTP_PREFIX_HEADERS_IN_RESPONSE,
            [],
            plugins,
        )

    @overload
    def http_query_params_only_operation(
        self,
        request: models.HttpQueryParamsOnlyOperationInput
        | models.HttpQueryParamsOnlyOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpQueryParamsOnlyOperationOutput: ...

    @overload
    def http_query_params_only_operation(
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

    def http_query_params_only_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpQueryParamsOnlyOperationOutput:
        return self._invoke(
            self._select_input(models.HTTP_QUERY_PARAMS_ONLY_OPERATION, args, kwargs),
            models.HTTP_QUERY_PARAMS_ONLY_OPERATION,
            [],
            plugins,
        )

    @overload
    def http_request_with_float_labels(
        self,
        request: models.HttpRequestWithFloatLabelsInput
        | models.HttpRequestWithFloatLabelsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpRequestWithFloatLabelsOutput: ...

    @overload
    def http_request_with_float_labels(
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

    def http_request_with_float_labels(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpRequestWithFloatLabelsOutput:
        return self._invoke(
            self._select_input(models.HTTP_REQUEST_WITH_FLOAT_LABELS, args, kwargs),
            models.HTTP_REQUEST_WITH_FLOAT_LABELS,
            [],
            plugins,
        )

    @overload
    def http_request_with_greedy_label_in_path(
        self,
        request: models.HttpRequestWithGreedyLabelInPathInput
        | models.HttpRequestWithGreedyLabelInPathInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpRequestWithGreedyLabelInPathOutput: ...

    @overload
    def http_request_with_greedy_label_in_path(
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

    def http_request_with_greedy_label_in_path(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpRequestWithGreedyLabelInPathOutput:
        return self._invoke(
            self._select_input(
                models.HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH, args, kwargs
            ),
            models.HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH,
            [],
            plugins,
        )

    @overload
    def http_request_with_labels(
        self,
        request: models.HttpRequestWithLabelsInput
        | models.HttpRequestWithLabelsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpRequestWithLabelsOutput: ...

    @overload
    def http_request_with_labels(
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

    def http_request_with_labels(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpRequestWithLabelsOutput:
        return self._invoke(
            self._select_input(models.HTTP_REQUEST_WITH_LABELS, args, kwargs),
            models.HTTP_REQUEST_WITH_LABELS,
            [],
            plugins,
        )

    @overload
    def http_request_with_labels_and_timestamp_format(
        self,
        request: models.HttpRequestWithLabelsAndTimestampFormatInput
        | models.HttpRequestWithLabelsAndTimestampFormatInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpRequestWithLabelsAndTimestampFormatOutput: ...

    @overload
    def http_request_with_labels_and_timestamp_format(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpRequestWithLabelsAndTimestampFormatInputDict],
    ) -> models.HttpRequestWithLabelsAndTimestampFormatOutput:
        """
        The example tests how requests serialize different timestamp formats in
        the URI path.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpRequestWithLabelsAndTimestampFormatOutput`.
        """

    def http_request_with_labels_and_timestamp_format(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpRequestWithLabelsAndTimestampFormatOutput:
        return self._invoke(
            self._select_input(
                models.HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT, args, kwargs
            ),
            models.HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT,
            [],
            plugins,
        )

    @overload
    def http_request_with_regex_literal(
        self,
        request: models.HttpRequestWithRegexLiteralInput
        | models.HttpRequestWithRegexLiteralInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpRequestWithRegexLiteralOutput: ...

    @overload
    def http_request_with_regex_literal(
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

    def http_request_with_regex_literal(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpRequestWithRegexLiteralOutput:
        return self._invoke(
            self._select_input(models.HTTP_REQUEST_WITH_REGEX_LITERAL, args, kwargs),
            models.HTTP_REQUEST_WITH_REGEX_LITERAL,
            [],
            plugins,
        )

    @overload
    def http_response_code(
        self,
        request: models.HttpResponseCodeInput | models.HttpResponseCodeInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpResponseCodeOutput: ...

    @overload
    def http_response_code(
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

    def http_response_code(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpResponseCodeOutput:
        return self._invoke(
            self._select_input(models.HTTP_RESPONSE_CODE, args, kwargs),
            models.HTTP_RESPONSE_CODE,
            [],
            plugins,
        )

    @overload
    def http_string_payload(
        self,
        request: models.HttpStringPayloadInput | models.HttpStringPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpStringPayloadOutput: ...

    @overload
    def http_string_payload(
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

    def http_string_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpStringPayloadOutput:
        return self._invoke(
            self._select_input(models.HTTP_STRING_PAYLOAD, args, kwargs),
            models.HTTP_STRING_PAYLOAD,
            [],
            plugins,
        )

    @overload
    def ignore_query_params_in_response(
        self,
        request: models.IgnoreQueryParamsInResponseInput
        | models.IgnoreQueryParamsInResponseInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.IgnoreQueryParamsInResponseOutput: ...

    @overload
    def ignore_query_params_in_response(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.IgnoreQueryParamsInResponseInputDict],
    ) -> models.IgnoreQueryParamsInResponseOutput:
        """
        This example ensures that query string bound request parameters are
        serialized in the body of responses if the structure is used in both the
        request and response.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `IgnoreQueryParamsInResponseOutput`.
        """

    def ignore_query_params_in_response(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.IgnoreQueryParamsInResponseOutput:
        return self._invoke(
            self._select_input(models.IGNORE_QUERY_PARAMS_IN_RESPONSE, args, kwargs),
            models.IGNORE_QUERY_PARAMS_IN_RESPONSE,
            [],
            plugins,
        )

    @overload
    def input_and_output_with_headers(
        self,
        request: models.InputAndOutputWithHeadersInput
        | models.InputAndOutputWithHeadersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.InputAndOutputWithHeadersOutput: ...

    @overload
    def input_and_output_with_headers(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.InputAndOutputWithHeadersInputDict],
    ) -> models.InputAndOutputWithHeadersOutput:
        """
        The example tests how requests and responses are serialized when there
        is no input or output payload but there are HTTP header bindings.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `InputAndOutputWithHeadersOutput`.
        """

    def input_and_output_with_headers(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.InputAndOutputWithHeadersOutput:
        return self._invoke(
            self._select_input(models.INPUT_AND_OUTPUT_WITH_HEADERS, args, kwargs),
            models.INPUT_AND_OUTPUT_WITH_HEADERS,
            [],
            plugins,
        )

    @overload
    def json_blobs(
        self,
        request: models.JsonBlobsInput | models.JsonBlobsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonBlobsOutput: ...

    @overload
    def json_blobs(
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

    def json_blobs(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonBlobsOutput:
        return self._invoke(
            self._select_input(models.JSON_BLOBS, args, kwargs),
            models.JSON_BLOBS,
            [],
            plugins,
        )

    @overload
    def json_enums(
        self,
        request: models.JsonEnumsInput | models.JsonEnumsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonEnumsOutput: ...

    @overload
    def json_enums(
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

    def json_enums(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonEnumsOutput:
        return self._invoke(
            self._select_input(models.JSON_ENUMS, args, kwargs),
            models.JSON_ENUMS,
            [],
            plugins,
        )

    @overload
    def json_int_enums(
        self,
        request: models.JsonIntEnumsInput | models.JsonIntEnumsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonIntEnumsOutput: ...

    @overload
    def json_int_enums(
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

    def json_int_enums(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonIntEnumsOutput:
        return self._invoke(
            self._select_input(models.JSON_INT_ENUMS, args, kwargs),
            models.JSON_INT_ENUMS,
            [],
            plugins,
        )

    @overload
    def json_lists(
        self,
        request: models.JsonListsInput | models.JsonListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonListsOutput: ...

    @overload
    def json_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.JsonListsInputDict],
    ) -> models.JsonListsOutput:
        """
        This test case serializes JSON lists for the following cases for both
        input and output: 1. Normal JSON lists. 2. Normal JSON sets. 3. JSON
        lists of lists. 4. Lists of structures.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `JsonListsOutput`.
        """

    def json_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonListsOutput:
        return self._invoke(
            self._select_input(models.JSON_LISTS, args, kwargs),
            models.JSON_LISTS,
            [],
            plugins,
        )

    @overload
    def json_maps(
        self,
        request: models.JsonMapsInput | models.JsonMapsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonMapsOutput: ...

    @overload
    def json_maps(
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

    def json_maps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonMapsOutput:
        return self._invoke(
            self._select_input(models.JSON_MAPS, args, kwargs),
            models.JSON_MAPS,
            [],
            plugins,
        )

    @overload
    def json_timestamps(
        self,
        request: models.JsonTimestampsInput | models.JsonTimestampsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonTimestampsOutput: ...

    @overload
    def json_timestamps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.JsonTimestampsInputDict],
    ) -> models.JsonTimestampsOutput:
        """
        This tests how timestamps are serialized, including using the default
        format of date-time and various @timestampFormat trait values.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `JsonTimestampsOutput`.
        """

    def json_timestamps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonTimestampsOutput:
        return self._invoke(
            self._select_input(models.JSON_TIMESTAMPS, args, kwargs),
            models.JSON_TIMESTAMPS,
            [],
            plugins,
        )

    @overload
    def json_unions(
        self,
        request: models.JsonUnionsInput | models.JsonUnionsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.JsonUnionsOutput: ...

    @overload
    def json_unions(
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

    def json_unions(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.JsonUnionsOutput:
        return self._invoke(
            self._select_input(models.JSON_UNIONS, args, kwargs),
            models.JSON_UNIONS,
            [],
            plugins,
        )

    @overload
    def malformed_accept_with_body(
        self,
        request: models.MalformedAcceptWithBodyInput
        | models.MalformedAcceptWithBodyInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedAcceptWithBodyOutput: ...

    @overload
    def malformed_accept_with_body(
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

    def malformed_accept_with_body(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedAcceptWithBodyOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_ACCEPT_WITH_BODY, args, kwargs),
            models.MALFORMED_ACCEPT_WITH_BODY,
            [],
            plugins,
        )

    @overload
    def malformed_accept_with_generic_string(
        self,
        request: models.MalformedAcceptWithGenericStringInput
        | models.MalformedAcceptWithGenericStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedAcceptWithGenericStringOutput: ...

    @overload
    def malformed_accept_with_generic_string(
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

    def malformed_accept_with_generic_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedAcceptWithGenericStringOutput:
        return self._invoke(
            self._select_input(
                models.MALFORMED_ACCEPT_WITH_GENERIC_STRING, args, kwargs
            ),
            models.MALFORMED_ACCEPT_WITH_GENERIC_STRING,
            [],
            plugins,
        )

    @overload
    def malformed_accept_with_payload(
        self,
        request: models.MalformedAcceptWithPayloadInput
        | models.MalformedAcceptWithPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedAcceptWithPayloadOutput: ...

    @overload
    def malformed_accept_with_payload(
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

    def malformed_accept_with_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedAcceptWithPayloadOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_ACCEPT_WITH_PAYLOAD, args, kwargs),
            models.MALFORMED_ACCEPT_WITH_PAYLOAD,
            [],
            plugins,
        )

    @overload
    def malformed_blob(
        self,
        request: models.MalformedBlobInput | models.MalformedBlobInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedBlobOutput: ...

    @overload
    def malformed_blob(
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

    def malformed_blob(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedBlobOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_BLOB, args, kwargs),
            models.MALFORMED_BLOB,
            [],
            plugins,
        )

    @overload
    def malformed_boolean(
        self,
        request: models.MalformedBooleanInput | models.MalformedBooleanInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedBooleanOutput: ...

    @overload
    def malformed_boolean(
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

    def malformed_boolean(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedBooleanOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_BOOLEAN, args, kwargs),
            models.MALFORMED_BOOLEAN,
            [],
            plugins,
        )

    @overload
    def malformed_byte(
        self,
        request: models.MalformedByteInput | models.MalformedByteInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedByteOutput: ...

    @overload
    def malformed_byte(
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

    def malformed_byte(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedByteOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_BYTE, args, kwargs),
            models.MALFORMED_BYTE,
            [],
            plugins,
        )

    @overload
    def malformed_content_type_with_body(
        self,
        request: models.MalformedContentTypeWithBodyInput
        | models.MalformedContentTypeWithBodyInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedContentTypeWithBodyOutput: ...

    @overload
    def malformed_content_type_with_body(
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

    def malformed_content_type_with_body(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedContentTypeWithBodyOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_CONTENT_TYPE_WITH_BODY, args, kwargs),
            models.MALFORMED_CONTENT_TYPE_WITH_BODY,
            [],
            plugins,
        )

    @overload
    def malformed_content_type_with_generic_string(
        self,
        request: models.MalformedContentTypeWithGenericStringInput
        | models.MalformedContentTypeWithGenericStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedContentTypeWithGenericStringOutput: ...

    @overload
    def malformed_content_type_with_generic_string(
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

    def malformed_content_type_with_generic_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedContentTypeWithGenericStringOutput:
        return self._invoke(
            self._select_input(
                models.MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING, args, kwargs
            ),
            models.MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING,
            [],
            plugins,
        )

    @overload
    def malformed_content_type_with_payload(
        self,
        request: models.MalformedContentTypeWithPayloadInput
        | models.MalformedContentTypeWithPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedContentTypeWithPayloadOutput: ...

    @overload
    def malformed_content_type_with_payload(
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

    def malformed_content_type_with_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedContentTypeWithPayloadOutput:
        return self._invoke(
            self._select_input(
                models.MALFORMED_CONTENT_TYPE_WITH_PAYLOAD, args, kwargs
            ),
            models.MALFORMED_CONTENT_TYPE_WITH_PAYLOAD,
            [],
            plugins,
        )

    @overload
    def malformed_content_type_without_body(
        self,
        request: models.MalformedContentTypeWithoutBodyInput
        | models.MalformedContentTypeWithoutBodyInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedContentTypeWithoutBodyOutput: ...

    @overload
    def malformed_content_type_without_body(
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

    def malformed_content_type_without_body(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedContentTypeWithoutBodyOutput:
        return self._invoke(
            self._select_input(
                models.MALFORMED_CONTENT_TYPE_WITHOUT_BODY, args, kwargs
            ),
            models.MALFORMED_CONTENT_TYPE_WITHOUT_BODY,
            [],
            plugins,
        )

    @overload
    def malformed_content_type_without_body_empty_input(
        self,
        request: models.MalformedContentTypeWithoutBodyEmptyInputInput
        | models.MalformedContentTypeWithoutBodyEmptyInputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedContentTypeWithoutBodyEmptyInputOutput: ...

    @overload
    def malformed_content_type_without_body_empty_input(
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

    def malformed_content_type_without_body_empty_input(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedContentTypeWithoutBodyEmptyInputOutput:
        return self._invoke(
            self._select_input(
                models.MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT, args, kwargs
            ),
            models.MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT,
            [],
            plugins,
        )

    @overload
    def malformed_double(
        self,
        request: models.MalformedDoubleInput | models.MalformedDoubleInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedDoubleOutput: ...

    @overload
    def malformed_double(
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

    def malformed_double(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedDoubleOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_DOUBLE, args, kwargs),
            models.MALFORMED_DOUBLE,
            [],
            plugins,
        )

    @overload
    def malformed_float(
        self,
        request: models.MalformedFloatInput | models.MalformedFloatInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedFloatOutput: ...

    @overload
    def malformed_float(
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

    def malformed_float(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedFloatOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_FLOAT, args, kwargs),
            models.MALFORMED_FLOAT,
            [],
            plugins,
        )

    @overload
    def malformed_integer(
        self,
        request: models.MalformedIntegerInput | models.MalformedIntegerInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedIntegerOutput: ...

    @overload
    def malformed_integer(
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

    def malformed_integer(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedIntegerOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_INTEGER, args, kwargs),
            models.MALFORMED_INTEGER,
            [],
            plugins,
        )

    @overload
    def malformed_list(
        self,
        request: models.MalformedListInput | models.MalformedListInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedListOutput: ...

    @overload
    def malformed_list(
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

    def malformed_list(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedListOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_LIST, args, kwargs),
            models.MALFORMED_LIST,
            [],
            plugins,
        )

    @overload
    def malformed_long(
        self,
        request: models.MalformedLongInput | models.MalformedLongInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedLongOutput: ...

    @overload
    def malformed_long(
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

    def malformed_long(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedLongOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_LONG, args, kwargs),
            models.MALFORMED_LONG,
            [],
            plugins,
        )

    @overload
    def malformed_map(
        self,
        request: models.MalformedMapInput | models.MalformedMapInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedMapOutput: ...

    @overload
    def malformed_map(
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

    def malformed_map(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedMapOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_MAP, args, kwargs),
            models.MALFORMED_MAP,
            [],
            plugins,
        )

    @overload
    def malformed_request_body(
        self,
        request: models.MalformedRequestBodyInput
        | models.MalformedRequestBodyInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedRequestBodyOutput: ...

    @overload
    def malformed_request_body(
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

    def malformed_request_body(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedRequestBodyOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_REQUEST_BODY, args, kwargs),
            models.MALFORMED_REQUEST_BODY,
            [],
            plugins,
        )

    @overload
    def malformed_short(
        self,
        request: models.MalformedShortInput | models.MalformedShortInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedShortOutput: ...

    @overload
    def malformed_short(
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

    def malformed_short(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedShortOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_SHORT, args, kwargs),
            models.MALFORMED_SHORT,
            [],
            plugins,
        )

    @overload
    def malformed_string(
        self,
        request: models.MalformedStringInput | models.MalformedStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedStringOutput: ...

    @overload
    def malformed_string(
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

    def malformed_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedStringOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_STRING, args, kwargs),
            models.MALFORMED_STRING,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_body_date_time(
        self,
        request: models.MalformedTimestampBodyDateTimeInput
        | models.MalformedTimestampBodyDateTimeInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampBodyDateTimeOutput: ...

    @overload
    def malformed_timestamp_body_date_time(
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

    def malformed_timestamp_body_date_time(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampBodyDateTimeOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_BODY_DATE_TIME, args, kwargs),
            models.MALFORMED_TIMESTAMP_BODY_DATE_TIME,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_body_default(
        self,
        request: models.MalformedTimestampBodyDefaultInput
        | models.MalformedTimestampBodyDefaultInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampBodyDefaultOutput: ...

    @overload
    def malformed_timestamp_body_default(
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

    def malformed_timestamp_body_default(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampBodyDefaultOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_BODY_DEFAULT, args, kwargs),
            models.MALFORMED_TIMESTAMP_BODY_DEFAULT,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_body_http_date(
        self,
        request: models.MalformedTimestampBodyHttpDateInput
        | models.MalformedTimestampBodyHttpDateInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampBodyHttpDateOutput: ...

    @overload
    def malformed_timestamp_body_http_date(
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

    def malformed_timestamp_body_http_date(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampBodyHttpDateOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_BODY_HTTP_DATE, args, kwargs),
            models.MALFORMED_TIMESTAMP_BODY_HTTP_DATE,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_header_date_time(
        self,
        request: models.MalformedTimestampHeaderDateTimeInput
        | models.MalformedTimestampHeaderDateTimeInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampHeaderDateTimeOutput: ...

    @overload
    def malformed_timestamp_header_date_time(
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

    def malformed_timestamp_header_date_time(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampHeaderDateTimeOutput:
        return self._invoke(
            self._select_input(
                models.MALFORMED_TIMESTAMP_HEADER_DATE_TIME, args, kwargs
            ),
            models.MALFORMED_TIMESTAMP_HEADER_DATE_TIME,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_header_default(
        self,
        request: models.MalformedTimestampHeaderDefaultInput
        | models.MalformedTimestampHeaderDefaultInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampHeaderDefaultOutput: ...

    @overload
    def malformed_timestamp_header_default(
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

    def malformed_timestamp_header_default(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampHeaderDefaultOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_HEADER_DEFAULT, args, kwargs),
            models.MALFORMED_TIMESTAMP_HEADER_DEFAULT,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_header_epoch(
        self,
        request: models.MalformedTimestampHeaderEpochInput
        | models.MalformedTimestampHeaderEpochInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampHeaderEpochOutput: ...

    @overload
    def malformed_timestamp_header_epoch(
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

    def malformed_timestamp_header_epoch(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampHeaderEpochOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_HEADER_EPOCH, args, kwargs),
            models.MALFORMED_TIMESTAMP_HEADER_EPOCH,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_path_default(
        self,
        request: models.MalformedTimestampPathDefaultInput
        | models.MalformedTimestampPathDefaultInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampPathDefaultOutput: ...

    @overload
    def malformed_timestamp_path_default(
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

    def malformed_timestamp_path_default(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampPathDefaultOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_PATH_DEFAULT, args, kwargs),
            models.MALFORMED_TIMESTAMP_PATH_DEFAULT,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_path_epoch(
        self,
        request: models.MalformedTimestampPathEpochInput
        | models.MalformedTimestampPathEpochInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampPathEpochOutput: ...

    @overload
    def malformed_timestamp_path_epoch(
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

    def malformed_timestamp_path_epoch(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampPathEpochOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_PATH_EPOCH, args, kwargs),
            models.MALFORMED_TIMESTAMP_PATH_EPOCH,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_path_http_date(
        self,
        request: models.MalformedTimestampPathHttpDateInput
        | models.MalformedTimestampPathHttpDateInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampPathHttpDateOutput: ...

    @overload
    def malformed_timestamp_path_http_date(
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

    def malformed_timestamp_path_http_date(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampPathHttpDateOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_PATH_HTTP_DATE, args, kwargs),
            models.MALFORMED_TIMESTAMP_PATH_HTTP_DATE,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_query_default(
        self,
        request: models.MalformedTimestampQueryDefaultInput
        | models.MalformedTimestampQueryDefaultInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampQueryDefaultOutput: ...

    @overload
    def malformed_timestamp_query_default(
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

    def malformed_timestamp_query_default(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampQueryDefaultOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_QUERY_DEFAULT, args, kwargs),
            models.MALFORMED_TIMESTAMP_QUERY_DEFAULT,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_query_epoch(
        self,
        request: models.MalformedTimestampQueryEpochInput
        | models.MalformedTimestampQueryEpochInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampQueryEpochOutput: ...

    @overload
    def malformed_timestamp_query_epoch(
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

    def malformed_timestamp_query_epoch(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampQueryEpochOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_TIMESTAMP_QUERY_EPOCH, args, kwargs),
            models.MALFORMED_TIMESTAMP_QUERY_EPOCH,
            [],
            plugins,
        )

    @overload
    def malformed_timestamp_query_http_date(
        self,
        request: models.MalformedTimestampQueryHttpDateInput
        | models.MalformedTimestampQueryHttpDateInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedTimestampQueryHttpDateOutput: ...

    @overload
    def malformed_timestamp_query_http_date(
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

    def malformed_timestamp_query_http_date(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedTimestampQueryHttpDateOutput:
        return self._invoke(
            self._select_input(
                models.MALFORMED_TIMESTAMP_QUERY_HTTP_DATE, args, kwargs
            ),
            models.MALFORMED_TIMESTAMP_QUERY_HTTP_DATE,
            [],
            plugins,
        )

    @overload
    def malformed_union(
        self,
        request: models.MalformedUnionInput | models.MalformedUnionInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MalformedUnionOutput: ...

    @overload
    def malformed_union(
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

    def malformed_union(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MalformedUnionOutput:
        return self._invoke(
            self._select_input(models.MALFORMED_UNION, args, kwargs),
            models.MALFORMED_UNION,
            [],
            plugins,
        )

    @overload
    def media_type_header(
        self,
        request: models.MediaTypeHeaderInput | models.MediaTypeHeaderInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.MediaTypeHeaderOutput: ...

    @overload
    def media_type_header(
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

    def media_type_header(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.MediaTypeHeaderOutput:
        return self._invoke(
            self._select_input(models.MEDIA_TYPE_HEADER, args, kwargs),
            models.MEDIA_TYPE_HEADER,
            [],
            plugins,
        )

    @overload
    def no_input_and_no_output(
        self,
        request: models.NoInputAndNoOutputInput | models.NoInputAndNoOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NoInputAndNoOutputOutput: ...

    @overload
    def no_input_and_no_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NoInputAndNoOutputInputDict],
    ) -> models.NoInputAndNoOutputOutput:
        """
        The example tests how requests and responses are serialized when there's
        no request or response payload because the operation has no input or
        output. While this should be rare, code generators must support this.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `NoInputAndNoOutputOutput`.
        """

    def no_input_and_no_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NoInputAndNoOutputOutput:
        return self._invoke(
            self._select_input(models.NO_INPUT_AND_NO_OUTPUT, args, kwargs),
            models.NO_INPUT_AND_NO_OUTPUT,
            [],
            plugins,
        )

    @overload
    def no_input_and_output(
        self,
        request: models.NoInputAndOutputInput | models.NoInputAndOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NoInputAndOutputOutput: ...

    @overload
    def no_input_and_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NoInputAndOutputInputDict],
    ) -> models.NoInputAndOutputOutput:
        """
        The example tests how requests and responses are serialized when there's
        no request or response payload because the operation has no input and
        the output is empty. While this should be rare, code generators must
        support this.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `NoInputAndOutputOutput`.
        """

    def no_input_and_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NoInputAndOutputOutput:
        return self._invoke(
            self._select_input(models.NO_INPUT_AND_OUTPUT, args, kwargs),
            models.NO_INPUT_AND_OUTPUT,
            [],
            plugins,
        )

    @overload
    def null_and_empty_headers_client(
        self,
        request: models.NullAndEmptyHeadersClientInput
        | models.NullAndEmptyHeadersClientInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NullAndEmptyHeadersClientOutput: ...

    @overload
    def null_and_empty_headers_client(
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

    def null_and_empty_headers_client(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NullAndEmptyHeadersClientOutput:
        return self._invoke(
            self._select_input(models.NULL_AND_EMPTY_HEADERS_CLIENT, args, kwargs),
            models.NULL_AND_EMPTY_HEADERS_CLIENT,
            [],
            plugins,
        )

    @overload
    def null_and_empty_headers_server(
        self,
        request: models.NullAndEmptyHeadersServerInput
        | models.NullAndEmptyHeadersServerInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NullAndEmptyHeadersServerOutput: ...

    @overload
    def null_and_empty_headers_server(
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

    def null_and_empty_headers_server(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NullAndEmptyHeadersServerOutput:
        return self._invoke(
            self._select_input(models.NULL_AND_EMPTY_HEADERS_SERVER, args, kwargs),
            models.NULL_AND_EMPTY_HEADERS_SERVER,
            [],
            plugins,
        )

    @overload
    def omits_null_serializes_empty_string(
        self,
        request: models.OmitsNullSerializesEmptyStringInput
        | models.OmitsNullSerializesEmptyStringInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OmitsNullSerializesEmptyStringOutput: ...

    @overload
    def omits_null_serializes_empty_string(
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

    def omits_null_serializes_empty_string(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OmitsNullSerializesEmptyStringOutput:
        return self._invoke(
            self._select_input(models.OMITS_NULL_SERIALIZES_EMPTY_STRING, args, kwargs),
            models.OMITS_NULL_SERIALIZES_EMPTY_STRING,
            [],
            plugins,
        )

    @overload
    def omits_serializing_empty_lists(
        self,
        request: models.OmitsSerializingEmptyListsInput
        | models.OmitsSerializingEmptyListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OmitsSerializingEmptyListsOutput: ...

    @overload
    def omits_serializing_empty_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.OmitsSerializingEmptyListsInputDict],
    ) -> models.OmitsSerializingEmptyListsOutput:
        """
        Omits serializing empty lists. Because empty strings are serilized as
        `Foo=`, empty lists cannot also be serialized as `Foo=` and instead must
        be omitted.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `OmitsSerializingEmptyListsOutput`.
        """

    def omits_serializing_empty_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OmitsSerializingEmptyListsOutput:
        return self._invoke(
            self._select_input(models.OMITS_SERIALIZING_EMPTY_LISTS, args, kwargs),
            models.OMITS_SERIALIZING_EMPTY_LISTS,
            [],
            plugins,
        )

    @overload
    def operation_with_defaults(
        self,
        request: models.OperationWithDefaultsInput
        | models.OperationWithDefaultsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OperationWithDefaultsOutput: ...

    @overload
    def operation_with_defaults(
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

    def operation_with_defaults(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OperationWithDefaultsOutput:
        return self._invoke(
            self._select_input(models.OPERATION_WITH_DEFAULTS, args, kwargs),
            models.OPERATION_WITH_DEFAULTS,
            [],
            plugins,
        )

    @overload
    def operation_with_nested_structure(
        self,
        request: models.OperationWithNestedStructureInput
        | models.OperationWithNestedStructureInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OperationWithNestedStructureOutput: ...

    @overload
    def operation_with_nested_structure(
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

    def operation_with_nested_structure(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OperationWithNestedStructureOutput:
        return self._invoke(
            self._select_input(models.OPERATION_WITH_NESTED_STRUCTURE, args, kwargs),
            models.OPERATION_WITH_NESTED_STRUCTURE,
            [],
            plugins,
        )

    @overload
    def post_player_action(
        self,
        request: models.PostPlayerActionInput | models.PostPlayerActionInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PostPlayerActionOutput: ...

    @overload
    def post_player_action(
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

    def post_player_action(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PostPlayerActionOutput:
        return self._invoke(
            self._select_input(models.POST_PLAYER_ACTION, args, kwargs),
            models.POST_PLAYER_ACTION,
            [],
            plugins,
        )

    @overload
    def post_union_with_json_name(
        self,
        request: models.PostUnionWithJsonNameInput
        | models.PostUnionWithJsonNameInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PostUnionWithJsonNameOutput: ...

    @overload
    def post_union_with_json_name(
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

    def post_union_with_json_name(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PostUnionWithJsonNameOutput:
        return self._invoke(
            self._select_input(models.POST_UNION_WITH_JSON_NAME, args, kwargs),
            models.POST_UNION_WITH_JSON_NAME,
            [],
            plugins,
        )

    @overload
    def put_with_content_encoding(
        self,
        request: models.PutWithContentEncodingInput
        | models.PutWithContentEncodingInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PutWithContentEncodingOutput: ...

    @overload
    def put_with_content_encoding(
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

    def put_with_content_encoding(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PutWithContentEncodingOutput:
        return self._invoke(
            self._select_input(models.PUT_WITH_CONTENT_ENCODING, args, kwargs),
            models.PUT_WITH_CONTENT_ENCODING,
            [],
            plugins,
        )

    @overload
    def query_idempotency_token_auto_fill(
        self,
        request: models.QueryIdempotencyTokenAutoFillInput
        | models.QueryIdempotencyTokenAutoFillInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryIdempotencyTokenAutoFillOutput: ...

    @overload
    def query_idempotency_token_auto_fill(
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

    def query_idempotency_token_auto_fill(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryIdempotencyTokenAutoFillOutput:
        return self._invoke(
            self._select_input(models.QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL, args, kwargs),
            models.QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL,
            [],
            plugins,
        )

    @overload
    def query_params_as_string_list_map(
        self,
        request: models.QueryParamsAsStringListMapInput
        | models.QueryParamsAsStringListMapInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryParamsAsStringListMapOutput: ...

    @overload
    def query_params_as_string_list_map(
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

    def query_params_as_string_list_map(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryParamsAsStringListMapOutput:
        return self._invoke(
            self._select_input(models.QUERY_PARAMS_AS_STRING_LIST_MAP, args, kwargs),
            models.QUERY_PARAMS_AS_STRING_LIST_MAP,
            [],
            plugins,
        )

    @overload
    def query_precedence(
        self,
        request: models.QueryPrecedenceInput | models.QueryPrecedenceInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryPrecedenceOutput: ...

    @overload
    def query_precedence(
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

    def query_precedence(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryPrecedenceOutput:
        return self._invoke(
            self._select_input(models.QUERY_PRECEDENCE, args, kwargs),
            models.QUERY_PRECEDENCE,
            [],
            plugins,
        )

    @overload
    def recursive_shapes(
        self,
        request: models.RecursiveShapesInput | models.RecursiveShapesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.RecursiveShapesOutput: ...

    @overload
    def recursive_shapes(
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

    def recursive_shapes(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.RecursiveShapesOutput:
        return self._invoke(
            self._select_input(models.RECURSIVE_SHAPES, args, kwargs),
            models.RECURSIVE_SHAPES,
            [],
            plugins,
        )

    @overload
    def response_code_http_fallback(
        self,
        request: models.ResponseCodeHttpFallbackInput
        | models.ResponseCodeHttpFallbackInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ResponseCodeHttpFallbackOutput: ...

    @overload
    def response_code_http_fallback(
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

    def response_code_http_fallback(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ResponseCodeHttpFallbackOutput:
        return self._invoke(
            self._select_input(models.RESPONSE_CODE_HTTP_FALLBACK, args, kwargs),
            models.RESPONSE_CODE_HTTP_FALLBACK,
            [],
            plugins,
        )

    @overload
    def response_code_required(
        self,
        request: models.ResponseCodeRequiredInput
        | models.ResponseCodeRequiredInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.ResponseCodeRequiredOutput: ...

    @overload
    def response_code_required(
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

    def response_code_required(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.ResponseCodeRequiredOutput:
        return self._invoke(
            self._select_input(models.RESPONSE_CODE_REQUIRED, args, kwargs),
            models.RESPONSE_CODE_REQUIRED,
            [],
            plugins,
        )

    @overload
    def simple_scalar_properties(
        self,
        request: models.SimpleScalarPropertiesInput
        | models.SimpleScalarPropertiesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SimpleScalarPropertiesOutput: ...

    @overload
    def simple_scalar_properties(
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

    def simple_scalar_properties(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SimpleScalarPropertiesOutput:
        return self._invoke(
            self._select_input(models.SIMPLE_SCALAR_PROPERTIES, args, kwargs),
            models.SIMPLE_SCALAR_PROPERTIES,
            [],
            plugins,
        )

    @overload
    def sparse_json_lists(
        self,
        request: models.SparseJsonListsInput | models.SparseJsonListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SparseJsonListsOutput: ...

    @overload
    def sparse_json_lists(
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

    def sparse_json_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SparseJsonListsOutput:
        return self._invoke(
            self._select_input(models.SPARSE_JSON_LISTS, args, kwargs),
            models.SPARSE_JSON_LISTS,
            [],
            plugins,
        )

    @overload
    def sparse_json_maps(
        self,
        request: models.SparseJsonMapsInput | models.SparseJsonMapsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SparseJsonMapsOutput: ...

    @overload
    def sparse_json_maps(
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

    def sparse_json_maps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SparseJsonMapsOutput:
        return self._invoke(
            self._select_input(models.SPARSE_JSON_MAPS, args, kwargs),
            models.SPARSE_JSON_MAPS,
            [],
            plugins,
        )

    @overload
    def test_body_structure(
        self,
        request: models.TestBodyStructureInput | models.TestBodyStructureInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestBodyStructureOutput: ...

    @overload
    def test_body_structure(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestBodyStructureInputDict],
    ) -> models.TestBodyStructureOutput:
        """
        This example operation serializes a structure in the HTTP body. It
        should ensure Content-Type: application/json is used in all requests and
        that an "empty" body is an empty JSON document ({}).

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestBodyStructureOutput`.
        """

    def test_body_structure(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestBodyStructureOutput:
        return self._invoke(
            self._select_input(models.TEST_BODY_STRUCTURE, args, kwargs),
            models.TEST_BODY_STRUCTURE,
            [],
            plugins,
        )

    @overload
    def test_get_no_input_no_payload(
        self,
        request: models.TestGetNoInputNoPayloadInput
        | models.TestGetNoInputNoPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestGetNoInputNoPayloadOutput: ...

    @overload
    def test_get_no_input_no_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestGetNoInputNoPayloadInputDict],
    ) -> models.TestGetNoInputNoPayloadOutput:
        """
        This example GET operation has no input and serializes a request without
        a HTTP body. These tests are to ensure we do not attach a body or
        related headers (Content-Length, Content-Type) to operations that
        semantically cannot produce an HTTP body.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestGetNoInputNoPayloadOutput`.
        """

    def test_get_no_input_no_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestGetNoInputNoPayloadOutput:
        return self._invoke(
            self._select_input(models.TEST_GET_NO_INPUT_NO_PAYLOAD, args, kwargs),
            models.TEST_GET_NO_INPUT_NO_PAYLOAD,
            [],
            plugins,
        )

    @overload
    def test_get_no_payload(
        self,
        request: models.TestGetNoPayloadInput | models.TestGetNoPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestGetNoPayloadOutput: ...

    @overload
    def test_get_no_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestGetNoPayloadInputDict],
    ) -> models.TestGetNoPayloadOutput:
        """
        This example GET operation serializes a request without a modeled HTTP
        body. These tests are to ensure we do not attach a body or related
        headers (Content-Length, Content-Type) to operations that semantically
        cannot produce an HTTP body.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestGetNoPayloadOutput`.
        """

    def test_get_no_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestGetNoPayloadOutput:
        return self._invoke(
            self._select_input(models.TEST_GET_NO_PAYLOAD, args, kwargs),
            models.TEST_GET_NO_PAYLOAD,
            [],
            plugins,
        )

    @overload
    def test_payload_blob(
        self,
        request: models.TestPayloadBlobInput | models.TestPayloadBlobInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestPayloadBlobOutput: ...

    @overload
    def test_payload_blob(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestPayloadBlobInputDict],
    ) -> models.TestPayloadBlobOutput:
        """
        This example operation serializes a payload targeting a blob. The Blob
        shape is not structured content and we cannot make assumptions about
        what data will be sent. This test ensures only a generic "Content-Type:
        application/octet-stream" header is used, and that we are not treating
        an empty body as an empty JSON document.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestPayloadBlobOutput`.
        """

    def test_payload_blob(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestPayloadBlobOutput:
        return self._invoke(
            self._select_input(models.TEST_PAYLOAD_BLOB, args, kwargs),
            models.TEST_PAYLOAD_BLOB,
            [],
            plugins,
        )

    @overload
    def test_payload_structure(
        self,
        request: models.TestPayloadStructureInput
        | models.TestPayloadStructureInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestPayloadStructureOutput: ...

    @overload
    def test_payload_structure(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestPayloadStructureInputDict],
    ) -> models.TestPayloadStructureOutput:
        """
        This example operation serializes a payload targeting a structure. This
        enforces the same requirements as TestBodyStructure but with the body
        specified by the @httpPayload trait.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestPayloadStructureOutput`.
        """

    def test_payload_structure(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestPayloadStructureOutput:
        return self._invoke(
            self._select_input(models.TEST_PAYLOAD_STRUCTURE, args, kwargs),
            models.TEST_PAYLOAD_STRUCTURE,
            [],
            plugins,
        )

    @overload
    def test_post_no_input_no_payload(
        self,
        request: models.TestPostNoInputNoPayloadInput
        | models.TestPostNoInputNoPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestPostNoInputNoPayloadOutput: ...

    @overload
    def test_post_no_input_no_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestPostNoInputNoPayloadInputDict],
    ) -> models.TestPostNoInputNoPayloadOutput:
        """
        This example POST operation has no input and serializes a request
        without a HTTP body. These tests are to ensure we do not attach a body
        or related headers (Content-Type) to a POST operation with no modeled
        input.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestPostNoInputNoPayloadOutput`.
        """

    def test_post_no_input_no_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestPostNoInputNoPayloadOutput:
        return self._invoke(
            self._select_input(models.TEST_POST_NO_INPUT_NO_PAYLOAD, args, kwargs),
            models.TEST_POST_NO_INPUT_NO_PAYLOAD,
            [],
            plugins,
        )

    @overload
    def test_post_no_payload(
        self,
        request: models.TestPostNoPayloadInput | models.TestPostNoPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TestPostNoPayloadOutput: ...

    @overload
    def test_post_no_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TestPostNoPayloadInputDict],
    ) -> models.TestPostNoPayloadOutput:
        """
        This example POST operation serializes a request without a modeled HTTP
        body. These tests are to ensure we do not attach a body or related
        headers (Content-Type) to a POST operation with no modeled payload.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TestPostNoPayloadOutput`.
        """

    def test_post_no_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TestPostNoPayloadOutput:
        return self._invoke(
            self._select_input(models.TEST_POST_NO_PAYLOAD, args, kwargs),
            models.TEST_POST_NO_PAYLOAD,
            [],
            plugins,
        )

    @overload
    def timestamp_format_headers(
        self,
        request: models.TimestampFormatHeadersInput
        | models.TimestampFormatHeadersInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TimestampFormatHeadersOutput: ...

    @overload
    def timestamp_format_headers(
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

    def timestamp_format_headers(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TimestampFormatHeadersOutput:
        return self._invoke(
            self._select_input(models.TIMESTAMP_FORMAT_HEADERS, args, kwargs),
            models.TIMESTAMP_FORMAT_HEADERS,
            [],
            plugins,
        )

    @overload
    def unit_input_and_output(
        self,
        request: models.UnitInputAndOutputInput | models.UnitInputAndOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.UnitInputAndOutputOutput: ...

    @overload
    def unit_input_and_output(
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

    def unit_input_and_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.UnitInputAndOutputOutput:
        return self._invoke(
            self._select_input(models.UNIT_INPUT_AND_OUTPUT, args, kwargs),
            models.UNIT_INPUT_AND_OUTPUT,
            [],
            plugins,
        )

    def _new_config(self) -> RestJsonProtocolConfig:
        return RestJsonProtocolConfig.resolve()

    def _post_setup(self, config: RestJsonProtocolConfig) -> None:
        if config.aws_credentials_identity_resolver is None:
            config_file, profile_name = self._profile_overrides(config)
            config.aws_credentials_identity_resolver = IdentityChain.create(
                AWSCredentialsIdentity,
                config_file=config_file,
                profile_name=profile_name,
                region_override=config.region,
                http_client=cast(HTTPClient | None, config.transport),
            )

    def _profile_overrides(
        self, config: RestJsonProtocolConfig
    ) -> tuple[MergedConfig | None, str | None]:
        config_context = config.resolution_context()
        config_file = None
        profile_name = None
        if config_context is not None:
            config_file = config_context.parsed_profiles()
            if config_context.profile_source is ConfigSource.OVERRIDE:
                profile_name = config_context.profile_name
        return config_file, profile_name
