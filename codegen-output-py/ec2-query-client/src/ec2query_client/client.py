from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.chain.resolver import IdentityChain
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.client import Client
from smithy_http.interfaces import HTTPClient
from smithy_http.plugins import user_agent_plugin

from ec2query_client import models
from ec2query_client.config import EC2ProtocolConfig, Plugin
from ec2query_client.user_agent import aws_user_agent_plugin


class EC2ProtocolClient(Client[EC2ProtocolConfig]):
    "An EC2 query service that sends query requests and XML responses."

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

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

        :param plugins: Callables that change the configuration for this call
        only.
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
        no request or response members.

        While this should be rare, code generators must support this.

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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
    def ignores_wrapping_xml_name(
        self,
        request: models.IgnoresWrappingXmlNameInput
        | models.IgnoresWrappingXmlNameInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.IgnoresWrappingXmlNameOutput: ...

    @overload
    def ignores_wrapping_xml_name(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.IgnoresWrappingXmlNameInputDict],
    ) -> models.IgnoresWrappingXmlNameOutput:
        """
        The xmlName trait on the output structure is ignored in AWS Query.

        The wrapping element is always operation name + "Response".

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def ignores_wrapping_xml_name(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.IgnoresWrappingXmlNameOutput:
        return self._invoke(
            self._select_input(models.IGNORES_WRAPPING_XML_NAME, args, kwargs),
            models.IGNORES_WRAPPING_XML_NAME,
            [],
            plugins,
        )

    @overload
    def nested_structures(
        self,
        request: models.NestedStructuresInput | models.NestedStructuresInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NestedStructuresOutput: ...

    @overload
    def nested_structures(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NestedStructuresInputDict],
    ) -> models.NestedStructuresOutput:
        """
        This test serializes nested and recursive structure members.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def nested_structures(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NestedStructuresOutput:
        return self._invoke(
            self._select_input(models.NESTED_STRUCTURES, args, kwargs),
            models.NESTED_STRUCTURES,
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
        no request payload or response members.

        While this should be rare, code generators must support this.

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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
    def query_lists(
        self,
        request: models.QueryListsInput | models.QueryListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryListsOutput: ...

    @overload
    def query_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.QueryListsInputDict],
    ) -> models.QueryListsOutput:
        """
        This test serializes simple and complex lists.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def query_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryListsOutput:
        return self._invoke(
            self._select_input(models.QUERY_LISTS, args, kwargs),
            models.QUERY_LISTS,
            [],
            plugins,
        )

    @overload
    def query_timestamps(
        self,
        request: models.QueryTimestampsInput | models.QueryTimestampsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryTimestampsOutput: ...

    @overload
    def query_timestamps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.QueryTimestampsInputDict],
    ) -> models.QueryTimestampsOutput:
        """
        This test serializes timestamps.

        1. Timestamps are serialized as RFC 3339 date-time values by default.
        2. A timestampFormat trait on a member changes the format.
        3. A timestampFormat trait on the shape targeted by the member changes
        the format.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def query_timestamps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryTimestampsOutput:
        return self._invoke(
            self._select_input(models.QUERY_TIMESTAMPS, args, kwargs),
            models.QUERY_TIMESTAMPS,
            [],
            plugins,
        )

    @overload
    def recursive_xml_shapes(
        self,
        request: models.RecursiveXmlShapesInput | models.RecursiveXmlShapesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.RecursiveXmlShapesOutput: ...

    @overload
    def recursive_xml_shapes(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.RecursiveXmlShapesInputDict],
    ) -> models.RecursiveXmlShapesOutput:
        """
        Recursive shapes

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def recursive_xml_shapes(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.RecursiveXmlShapesOutput:
        return self._invoke(
            self._select_input(models.RECURSIVE_XML_SHAPES, args, kwargs),
            models.RECURSIVE_XML_SHAPES,
            [],
            plugins,
        )

    @overload
    def simple_input_params(
        self,
        request: models.SimpleInputParamsInput | models.SimpleInputParamsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SimpleInputParamsOutput: ...

    @overload
    def simple_input_params(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.SimpleInputParamsInputDict],
    ) -> models.SimpleInputParamsOutput:
        """
        This test serializes strings, numbers, and boolean values.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def simple_input_params(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SimpleInputParamsOutput:
        return self._invoke(
            self._select_input(models.SIMPLE_INPUT_PARAMS, args, kwargs),
            models.SIMPLE_INPUT_PARAMS,
            [],
            plugins,
        )

    @overload
    def simple_scalar_xml_properties(
        self,
        request: models.SimpleScalarXmlPropertiesInput
        | models.SimpleScalarXmlPropertiesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SimpleScalarXmlPropertiesOutput: ...

    @overload
    def simple_scalar_xml_properties(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.SimpleScalarXmlPropertiesInputDict],
    ) -> models.SimpleScalarXmlPropertiesOutput:
        """
        Invokes the SimpleScalarXmlProperties operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def simple_scalar_xml_properties(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SimpleScalarXmlPropertiesOutput:
        return self._invoke(
            self._select_input(models.SIMPLE_SCALAR_XML_PROPERTIES, args, kwargs),
            models.SIMPLE_SCALAR_XML_PROPERTIES,
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
    ) -> models.XmlBlobsOutput2: ...

    @overload
    def xml_blobs(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlBlobsInputDict],
    ) -> models.XmlBlobsOutput2:
        """
        Blobs are base64 encoded

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def xml_blobs(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlBlobsOutput2:
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
        Invokes the XmlEmptyBlobs operation.

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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
        This example serializes intEnums as top level properties, in lists,
        sets, and maps.

        :param plugins: Callables that change the configuration for this call
        only.
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
    ) -> models.XmlListsOutput2: ...

    @overload
    def xml_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlListsInputDict],
    ) -> models.XmlListsOutput2:
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

        :param plugins: Callables that change the configuration for this call
        only.
        """

    def xml_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlListsOutput2:
        return self._invoke(
            self._select_input(models.XML_LISTS, args, kwargs),
            models.XML_LISTS,
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

    def _new_config(self) -> EC2ProtocolConfig:
        return EC2ProtocolConfig.resolve()

    def _post_setup(self, config: EC2ProtocolConfig) -> None:
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
        self, config: EC2ProtocolConfig
    ) -> tuple[MergedConfig | None, str | None]:
        config_context = config.resolution_context()
        config_file = None
        profile_name = None
        if config_context is not None:
            config_file = config_context.parsed_profiles()
            if config_context.profile_source is ConfigSource.OVERRIDE:
                profile_name = config_context.profile_name
        return config_file, profile_name
