from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.chain.resolver import IdentityChain
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.client import Client
from smithy_http.interfaces import HTTPClient
from smithy_http.plugins import user_agent_plugin

from restxml_client import models
from restxml_client.config import Plugin, RestXmlProtocolConfig
from restxml_client.user_agent import aws_user_agent_plugin


class RestXmlProtocolClient(Client[RestXmlProtocolConfig]):
    "A REST XML service that sends XML requests and responses."

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
    def body_with_xml_name(
        self,
        request: models.BodyWithXmlNameInput | models.BodyWithXmlNameInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.BodyWithXmlNameOutput: ...

    @overload
    def body_with_xml_name(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.BodyWithXmlNameInputDict],
    ) -> models.BodyWithXmlNameOutput:
        """
        The following example serializes a body that uses an XML name,
        changing the wrapper name.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `BodyWithXmlNameOutput`.
        """

    def body_with_xml_name(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.BodyWithXmlNameOutput:
        return self._invoke(
            self._select_input(models.BODY_WITH_XML_NAME, args, kwargs),
            models.BODY_WITH_XML_NAME,
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
        params.
        The fixed query string parameters and variable parameters must both be
        serialized (implementations may need to merge them together).

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
        The example tests how servers must support requests
        containing a `Content-Type` header with parameters.

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
    def endpoint_with_host_label_header_operation(
        self,
        request: models.EndpointWithHostLabelHeaderOperationInput
        | models.EndpointWithHostLabelHeaderOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EndpointWithHostLabelHeaderOperationOutput: ...

    @overload
    def endpoint_with_host_label_header_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.EndpointWithHostLabelHeaderOperationInputDict],
    ) -> models.EndpointWithHostLabelHeaderOperationOutput:
        """
        Invokes the EndpointWithHostLabelHeaderOperation operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `EndpointWithHostLabelHeaderOperationOutput`.
        """

    def endpoint_with_host_label_header_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EndpointWithHostLabelHeaderOperationOutput:
        return self._invoke(
            self._select_input(
                models.ENDPOINT_WITH_HOST_LABEL_HEADER_OPERATION, args, kwargs
            ),
            models.ENDPOINT_WITH_HOST_LABEL_HEADER_OPERATION,
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
    def flattened_xml_map(
        self,
        request: models.FlattenedXmlMapInput | models.FlattenedXmlMapInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.FlattenedXmlMapOutput: ...

    @overload
    def flattened_xml_map(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.FlattenedXmlMapInputDict],
    ) -> models.FlattenedXmlMapOutput:
        """
        Flattened maps

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `FlattenedXmlMapOutput`.
        """

    def flattened_xml_map(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.FlattenedXmlMapOutput:
        return self._invoke(
            self._select_input(models.FLATTENED_XML_MAP, args, kwargs),
            models.FLATTENED_XML_MAP,
            [],
            plugins,
        )

    @overload
    def flattened_xml_map_with_xml_name(
        self,
        request: models.FlattenedXmlMapWithXmlNameInput
        | models.FlattenedXmlMapWithXmlNameInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.FlattenedXmlMapWithXmlNameOutput: ...

    @overload
    def flattened_xml_map_with_xml_name(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.FlattenedXmlMapWithXmlNameInputDict],
    ) -> models.FlattenedXmlMapWithXmlNameOutput:
        """
        Flattened maps with @xmlName

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `FlattenedXmlMapWithXmlNameOutput`.
        """

    def flattened_xml_map_with_xml_name(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.FlattenedXmlMapWithXmlNameOutput:
        return self._invoke(
            self._select_input(models.FLATTENED_XML_MAP_WITH_XML_NAME, args, kwargs),
            models.FLATTENED_XML_MAP_WITH_XML_NAME,
            [],
            plugins,
        )

    @overload
    def flattened_xml_map_with_xml_namespace(
        self,
        request: models.FlattenedXmlMapWithXmlNamespaceInput
        | models.FlattenedXmlMapWithXmlNamespaceInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.FlattenedXmlMapWithXmlNamespaceOutput: ...

    @overload
    def flattened_xml_map_with_xml_namespace(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.FlattenedXmlMapWithXmlNamespaceInputDict],
    ) -> models.FlattenedXmlMapWithXmlNamespaceOutput:
        """
        Flattened maps with @xmlNamespace and @xmlName

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `FlattenedXmlMapWithXmlNamespaceOutput`.
        """

    def flattened_xml_map_with_xml_namespace(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.FlattenedXmlMapWithXmlNamespaceOutput:
        return self._invoke(
            self._select_input(
                models.FLATTENED_XML_MAP_WITH_XML_NAMESPACE, args, kwargs
            ),
            models.FLATTENED_XML_MAP_WITH_XML_NAMESPACE,
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
        This operation has three possible return values:

        1. A successful response in the form of GreetingWithErrorsOutput
        2. An InvalidGreeting error.
        3. A BadRequest error.

        Implementations must be able to successfully take a response and
        properly (de)serialize successful and error responses based on the
        the presence of the

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
        This example serializes a blob shape in the payload.

        In this example, no XML document is synthesized because the payload is
        not a structure or a union type.

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
    def http_payload_with_member_xml_name(
        self,
        request: models.HttpPayloadWithMemberXmlNameInput
        | models.HttpPayloadWithMemberXmlNameInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadWithMemberXmlNameOutput: ...

    @overload
    def http_payload_with_member_xml_name(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPayloadWithMemberXmlNameInputDict],
    ) -> models.HttpPayloadWithMemberXmlNameOutput:
        """
        The following example serializes a payload that uses an XML name
        on the member, changing the wrapper name.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPayloadWithMemberXmlNameOutput`.
        """

    def http_payload_with_member_xml_name(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadWithMemberXmlNameOutput:
        return self._invoke(
            self._select_input(models.HTTP_PAYLOAD_WITH_MEMBER_XML_NAME, args, kwargs),
            models.HTTP_PAYLOAD_WITH_MEMBER_XML_NAME,
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
        This example serializes a structure in the payload.

        Note that serializing a structure changes the wrapper element name
        to match the targeted structure.

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
    def http_payload_with_xml_name(
        self,
        request: models.HttpPayloadWithXmlNameInput
        | models.HttpPayloadWithXmlNameInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadWithXmlNameOutput: ...

    @overload
    def http_payload_with_xml_name(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPayloadWithXmlNameInputDict],
    ) -> models.HttpPayloadWithXmlNameOutput:
        """
        The following example serializes a payload that uses an XML name,
        changing the wrapper name.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPayloadWithXmlNameOutput`.
        """

    def http_payload_with_xml_name(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadWithXmlNameOutput:
        return self._invoke(
            self._select_input(models.HTTP_PAYLOAD_WITH_XML_NAME, args, kwargs),
            models.HTTP_PAYLOAD_WITH_XML_NAME,
            [],
            plugins,
        )

    @overload
    def http_payload_with_xml_namespace(
        self,
        request: models.HttpPayloadWithXmlNamespaceInput
        | models.HttpPayloadWithXmlNamespaceInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadWithXmlNamespaceOutput: ...

    @overload
    def http_payload_with_xml_namespace(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPayloadWithXmlNamespaceInputDict],
    ) -> models.HttpPayloadWithXmlNamespaceOutput:
        """
        The following example serializes a payload that uses an XML namespace.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPayloadWithXmlNamespaceOutput`.
        """

    def http_payload_with_xml_namespace(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadWithXmlNamespaceOutput:
        return self._invoke(
            self._select_input(models.HTTP_PAYLOAD_WITH_XML_NAMESPACE, args, kwargs),
            models.HTTP_PAYLOAD_WITH_XML_NAMESPACE,
            [],
            plugins,
        )

    @overload
    def http_payload_with_xml_namespace_and_prefix(
        self,
        request: models.HttpPayloadWithXmlNamespaceAndPrefixInput
        | models.HttpPayloadWithXmlNamespaceAndPrefixInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.HttpPayloadWithXmlNamespaceAndPrefixOutput: ...

    @overload
    def http_payload_with_xml_namespace_and_prefix(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.HttpPayloadWithXmlNamespaceAndPrefixInputDict],
    ) -> models.HttpPayloadWithXmlNamespaceAndPrefixOutput:
        """
        The following example serializes a payload that uses an XML namespace.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `HttpPayloadWithXmlNamespaceAndPrefixOutput`.
        """

    def http_payload_with_xml_namespace_and_prefix(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.HttpPayloadWithXmlNamespaceAndPrefixOutput:
        return self._invoke(
            self._select_input(
                models.HTTP_PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX, args, kwargs
            ),
            models.HTTP_PAYLOAD_WITH_XML_NAMESPACE_AND_PREFIX,
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
        the
        URI path.

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
        serialized in the body of responses if the structure is used in both
        the request and response.

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
        is
        no input or output payload but there are HTTP header bindings.

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
    def nested_xml_map_with_xml_name(
        self,
        request: models.NestedXmlMapWithXmlNameInput
        | models.NestedXmlMapWithXmlNameInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NestedXmlMapWithXmlNameOutput: ...

    @overload
    def nested_xml_map_with_xml_name(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NestedXmlMapWithXmlNameInputDict],
    ) -> models.NestedXmlMapWithXmlNameOutput:
        """
        Nested Xml Maps with key/values with @xmlName

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `NestedXmlMapWithXmlNameOutput`.
        """

    def nested_xml_map_with_xml_name(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NestedXmlMapWithXmlNameOutput:
        return self._invoke(
            self._select_input(models.NESTED_XML_MAP_WITH_XML_NAME, args, kwargs),
            models.NESTED_XML_MAP_WITH_XML_NAME,
            [],
            plugins,
        )

    @overload
    def nested_xml_maps(
        self,
        request: models.NestedXmlMapsInput | models.NestedXmlMapsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NestedXmlMapsOutput: ...

    @overload
    def nested_xml_maps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NestedXmlMapsInputDict],
    ) -> models.NestedXmlMapsOutput:
        """
        Invokes the NestedXmlMaps operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `NestedXmlMapsOutput`.
        """

    def nested_xml_maps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NestedXmlMapsOutput:
        return self._invoke(
            self._select_input(models.NESTED_XML_MAPS, args, kwargs),
            models.NESTED_XML_MAPS,
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
        output.
        While this should be rare, code generators must support this.

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
        the
        output is empty. While this should be rare, code generators must support
        this.

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
        The example tests how timestamp request and response headers are
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
    def xml_attributes(
        self,
        request: models.XmlAttributesInput | models.XmlAttributesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlAttributesOutput: ...

    @overload
    def xml_attributes(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlAttributesInputDict],
    ) -> models.XmlAttributesOutput:
        """
        This example serializes an XML attributes on synthesized document.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlAttributesOutput`.
        """

    def xml_attributes(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlAttributesOutput:
        return self._invoke(
            self._select_input(models.XML_ATTRIBUTES, args, kwargs),
            models.XML_ATTRIBUTES,
            [],
            plugins,
        )

    @overload
    def xml_attributes_in_middle(
        self,
        request: models.XmlAttributesInMiddleInput
        | models.XmlAttributesInMiddleInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlAttributesInMiddleOutput: ...

    @overload
    def xml_attributes_in_middle(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlAttributesInMiddleInputDict],
    ) -> models.XmlAttributesInMiddleOutput:
        """
        This example serializes an XML attribute on a payload when it's defined
        in the middle of the member list.
        This tests that implementations correctly write attributes immediately
        after the element start tag,
        which is critical for languages like C# where attribute writing must
        happen before child elements.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlAttributesInMiddleOutput`.
        """

    def xml_attributes_in_middle(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlAttributesInMiddleOutput:
        return self._invoke(
            self._select_input(models.XML_ATTRIBUTES_IN_MIDDLE, args, kwargs),
            models.XML_ATTRIBUTES_IN_MIDDLE,
            [],
            plugins,
        )

    @overload
    def xml_attributes_on_payload(
        self,
        request: models.XmlAttributesOnPayloadInput
        | models.XmlAttributesOnPayloadInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlAttributesOnPayloadOutput: ...

    @overload
    def xml_attributes_on_payload(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlAttributesOnPayloadInputDict],
    ) -> models.XmlAttributesOnPayloadOutput:
        """
        This example serializes an XML attributes on a document targeted by
        httpPayload.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlAttributesOnPayloadOutput`.
        """

    def xml_attributes_on_payload(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlAttributesOnPayloadOutput:
        return self._invoke(
            self._select_input(models.XML_ATTRIBUTES_ON_PAYLOAD, args, kwargs),
            models.XML_ATTRIBUTES_ON_PAYLOAD,
            [],
            plugins,
        )

    @overload
    def xml_blobs(
        self,
        request: models.XmlBlobsInput | models.XmlBlobsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlBlobsOutput: ...

    @overload
    def xml_blobs(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlBlobsInputDict],
    ) -> models.XmlBlobsOutput:
        """
        Blobs are base64 encoded

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlBlobsOutput`.
        """

    def xml_blobs(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlBlobsOutput:
        return self._invoke(
            self._select_input(models.XML_BLOBS, args, kwargs),
            models.XML_BLOBS,
            [],
            plugins,
        )

    @overload
    def xml_empty_blobs(
        self,
        request: models.XmlEmptyBlobsInput | models.XmlEmptyBlobsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlEmptyBlobsOutput: ...

    @overload
    def xml_empty_blobs(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlEmptyBlobsInputDict],
    ) -> models.XmlEmptyBlobsOutput:
        """
        Blobs are base64 encoded

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlEmptyBlobsOutput`.
        """

    def xml_empty_blobs(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlEmptyBlobsOutput:
        return self._invoke(
            self._select_input(models.XML_EMPTY_BLOBS, args, kwargs),
            models.XML_EMPTY_BLOBS,
            [],
            plugins,
        )

    @overload
    def xml_empty_lists(
        self,
        request: models.XmlEmptyListsInput | models.XmlEmptyListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlEmptyListsOutput: ...

    @overload
    def xml_empty_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlEmptyListsInputDict],
    ) -> models.XmlEmptyListsOutput:
        """
        Invokes the XmlEmptyLists operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlEmptyListsOutput`.
        """

    def xml_empty_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlEmptyListsOutput:
        return self._invoke(
            self._select_input(models.XML_EMPTY_LISTS, args, kwargs),
            models.XML_EMPTY_LISTS,
            [],
            plugins,
        )

    @overload
    def xml_empty_maps(
        self,
        request: models.XmlEmptyMapsInput | models.XmlEmptyMapsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlEmptyMapsOutput: ...

    @overload
    def xml_empty_maps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlEmptyMapsInputDict],
    ) -> models.XmlEmptyMapsOutput:
        """
        Invokes the XmlEmptyMaps operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlEmptyMapsOutput`.
        """

    def xml_empty_maps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlEmptyMapsOutput:
        return self._invoke(
            self._select_input(models.XML_EMPTY_MAPS, args, kwargs),
            models.XML_EMPTY_MAPS,
            [],
            plugins,
        )

    @overload
    def xml_empty_strings(
        self,
        request: models.XmlEmptyStringsInput | models.XmlEmptyStringsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlEmptyStringsOutput: ...

    @overload
    def xml_empty_strings(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlEmptyStringsInputDict],
    ) -> models.XmlEmptyStringsOutput:
        """
        Invokes the XmlEmptyStrings operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlEmptyStringsOutput`.
        """

    def xml_empty_strings(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlEmptyStringsOutput:
        return self._invoke(
            self._select_input(models.XML_EMPTY_STRINGS, args, kwargs),
            models.XML_EMPTY_STRINGS,
            [],
            plugins,
        )

    @overload
    def xml_enums(
        self,
        request: models.XmlEnumsInput | models.XmlEnumsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlEnumsOutput: ...

    @overload
    def xml_enums(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlEnumsInputDict],
    ) -> models.XmlEnumsOutput:
        """
        This example serializes enums as top level properties, in lists, sets,
        and maps.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlEnumsOutput`.
        """

    def xml_enums(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlEnumsOutput:
        return self._invoke(
            self._select_input(models.XML_ENUMS, args, kwargs),
            models.XML_ENUMS,
            [],
            plugins,
        )

    @overload
    def xml_int_enums(
        self,
        request: models.XmlIntEnumsInput | models.XmlIntEnumsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlIntEnumsOutput: ...

    @overload
    def xml_int_enums(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlIntEnumsInputDict],
    ) -> models.XmlIntEnumsOutput:
        """
        This example serializes enums as top level properties, in lists, sets,
        and maps.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlIntEnumsOutput`.
        """

    def xml_int_enums(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlIntEnumsOutput:
        return self._invoke(
            self._select_input(models.XML_INT_ENUMS, args, kwargs),
            models.XML_INT_ENUMS,
            [],
            plugins,
        )

    @overload
    def xml_lists(
        self,
        request: models.XmlListsInput | models.XmlListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlListsOutput: ...

    @overload
    def xml_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlListsInputDict],
    ) -> models.XmlListsOutput:
        """
        This test case serializes XML lists for the following cases for both
        input and output:

        1. Normal XML lists.
        2. Normal XML sets.
        3. XML lists of lists.
        4. XML lists with @xmlName on its members
        5. Flattened XML lists.
        6. Flattened XML lists with @xmlName.
        7. Flattened XML lists with @xmlNamespace.
        8. Lists of structures.
        9. Flattened XML list of structures

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlListsOutput`.
        """

    def xml_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlListsOutput:
        return self._invoke(
            self._select_input(models.XML_LISTS, args, kwargs),
            models.XML_LISTS,
            [],
            plugins,
        )

    @overload
    def xml_map_with_xml_namespace(
        self,
        request: models.XmlMapWithXmlNamespaceInput
        | models.XmlMapWithXmlNamespaceInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlMapWithXmlNamespaceOutput: ...

    @overload
    def xml_map_with_xml_namespace(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlMapWithXmlNamespaceInputDict],
    ) -> models.XmlMapWithXmlNamespaceOutput:
        """
        Maps with @xmlNamespace and @xmlName

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlMapWithXmlNamespaceOutput`.
        """

    def xml_map_with_xml_namespace(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlMapWithXmlNamespaceOutput:
        return self._invoke(
            self._select_input(models.XML_MAP_WITH_XML_NAMESPACE, args, kwargs),
            models.XML_MAP_WITH_XML_NAMESPACE,
            [],
            plugins,
        )

    @overload
    def xml_maps(
        self,
        request: models.XmlMapsInput | models.XmlMapsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlMapsOutput: ...

    @overload
    def xml_maps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlMapsInputDict],
    ) -> models.XmlMapsOutput:
        """
        The example tests basic map serialization.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlMapsOutput`.
        """

    def xml_maps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlMapsOutput:
        return self._invoke(
            self._select_input(models.XML_MAPS, args, kwargs),
            models.XML_MAPS,
            [],
            plugins,
        )

    @overload
    def xml_maps_xml_name(
        self,
        request: models.XmlMapsXmlNameInput | models.XmlMapsXmlNameInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlMapsXmlNameOutput: ...

    @overload
    def xml_maps_xml_name(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlMapsXmlNameInputDict],
    ) -> models.XmlMapsXmlNameOutput:
        """
        Invokes the XmlMapsXmlName operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlMapsXmlNameOutput`.
        """

    def xml_maps_xml_name(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlMapsXmlNameOutput:
        return self._invoke(
            self._select_input(models.XML_MAPS_XML_NAME, args, kwargs),
            models.XML_MAPS_XML_NAME,
            [],
            plugins,
        )

    @overload
    def xml_namespaces(
        self,
        request: models.XmlNamespacesInput | models.XmlNamespacesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlNamespacesOutput: ...

    @overload
    def xml_namespaces(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlNamespacesInputDict],
    ) -> models.XmlNamespacesOutput:
        """
        Invokes the XmlNamespaces operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlNamespacesOutput`.
        """

    def xml_namespaces(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlNamespacesOutput:
        return self._invoke(
            self._select_input(models.XML_NAMESPACES, args, kwargs),
            models.XML_NAMESPACES,
            [],
            plugins,
        )

    @overload
    def xml_timestamps(
        self,
        request: models.XmlTimestampsInput | models.XmlTimestampsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlTimestampsOutput: ...

    @overload
    def xml_timestamps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlTimestampsInputDict],
    ) -> models.XmlTimestampsOutput:
        """
        This tests how timestamps are serialized, including using the
        default format of date-time and various @timestampFormat trait
        values.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlTimestampsOutput`.
        """

    def xml_timestamps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlTimestampsOutput:
        return self._invoke(
            self._select_input(models.XML_TIMESTAMPS, args, kwargs),
            models.XML_TIMESTAMPS,
            [],
            plugins,
        )

    @overload
    def xml_unions(
        self,
        request: models.XmlUnionsInput | models.XmlUnionsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlUnionsOutput: ...

    @overload
    def xml_unions(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlUnionsInputDict],
    ) -> models.XmlUnionsOutput:
        """
        Invokes the XmlUnions operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlUnionsOutput`.
        """

    def xml_unions(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlUnionsOutput:
        return self._invoke(
            self._select_input(models.XML_UNIONS, args, kwargs),
            models.XML_UNIONS,
            [],
            plugins,
        )

    def _new_config(self) -> RestXmlProtocolConfig:
        return RestXmlProtocolConfig.resolve()

    def _post_setup(self, config: RestXmlProtocolConfig) -> None:
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
        self, config: RestXmlProtocolConfig
    ) -> tuple[MergedConfig | None, str | None]:
        config_context = config.resolution_context()
        config_file = None
        profile_name = None
        if config_context is not None:
            config_file = config_context.parsed_profiles()
            if config_context.profile_source is ConfigSource.OVERRIDE:
                profile_name = config_context.profile_name
        return config_file, profile_name
