from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.aio.identity.chain import AsyncIdentityChain
from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.aio.client import AsyncClient
from smithy_http.aio.interfaces import AsyncHTTPClient
from smithy_http.plugins import user_agent_plugin

from ec2query_client import models
from ec2query_client.aio.config import AsyncEC2ProtocolConfig, Plugin
from ec2query_client.aio.user_agent import aws_user_agent_plugin


class AsyncEC2ProtocolClient(AsyncClient[AsyncEC2ProtocolConfig]):
    "An EC2 query service that sends query requests and XML responses."

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

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
        no request or response members.

        While this should be rare, code generators must support this.

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
        This operation has three possible return values:

        1. A successful response in the form of GreetingWithErrorsOutput
        2. An InvalidGreeting error.
        3. A BadRequest error.

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
    async def ignores_wrapping_xml_name(
        self,
        request: models.IgnoresWrappingXmlNameInput
        | models.IgnoresWrappingXmlNameInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.IgnoresWrappingXmlNameOutput: ...

    @overload
    async def ignores_wrapping_xml_name(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.IgnoresWrappingXmlNameInputDict],
    ) -> models.IgnoresWrappingXmlNameOutput:
        """
        The xmlName trait on the output structure is ignored in AWS Query.

        The wrapping element is always operation name + "Response".

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `IgnoresWrappingXmlNameOutput`.
        """

    async def ignores_wrapping_xml_name(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.IgnoresWrappingXmlNameOutput:
        return await self._invoke(
            self._select_input(models.IGNORES_WRAPPING_XML_NAME, args, kwargs),
            models.IGNORES_WRAPPING_XML_NAME,
            [],
            plugins,
        )

    @overload
    async def nested_structures(
        self,
        request: models.NestedStructuresInput | models.NestedStructuresInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NestedStructuresOutput: ...

    @overload
    async def nested_structures(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NestedStructuresInputDict],
    ) -> models.NestedStructuresOutput:
        """
        This test serializes nested and recursive structure members.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `NestedStructuresOutput`.
        """

    async def nested_structures(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NestedStructuresOutput:
        return await self._invoke(
            self._select_input(models.NESTED_STRUCTURES, args, kwargs),
            models.NESTED_STRUCTURES,
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
        no request payload or response members.

        While this should be rare, code generators must support this.

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
    async def query_lists(
        self,
        request: models.QueryListsInput | models.QueryListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryListsOutput: ...

    @overload
    async def query_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.QueryListsInputDict],
    ) -> models.QueryListsOutput:
        """
        This test serializes simple and complex lists.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `QueryListsOutput`.
        """

    async def query_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryListsOutput:
        return await self._invoke(
            self._select_input(models.QUERY_LISTS, args, kwargs),
            models.QUERY_LISTS,
            [],
            plugins,
        )

    @overload
    async def query_timestamps(
        self,
        request: models.QueryTimestampsInput | models.QueryTimestampsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.QueryTimestampsOutput: ...

    @overload
    async def query_timestamps(
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

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `QueryTimestampsOutput`.
        """

    async def query_timestamps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.QueryTimestampsOutput:
        return await self._invoke(
            self._select_input(models.QUERY_TIMESTAMPS, args, kwargs),
            models.QUERY_TIMESTAMPS,
            [],
            plugins,
        )

    @overload
    async def recursive_xml_shapes(
        self,
        request: models.RecursiveXmlShapesInput | models.RecursiveXmlShapesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.RecursiveXmlShapesOutput: ...

    @overload
    async def recursive_xml_shapes(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.RecursiveXmlShapesInputDict],
    ) -> models.RecursiveXmlShapesOutput:
        """
        Recursive shapes

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `RecursiveXmlShapesOutput`.
        """

    async def recursive_xml_shapes(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.RecursiveXmlShapesOutput:
        return await self._invoke(
            self._select_input(models.RECURSIVE_XML_SHAPES, args, kwargs),
            models.RECURSIVE_XML_SHAPES,
            [],
            plugins,
        )

    @overload
    async def simple_input_params(
        self,
        request: models.SimpleInputParamsInput | models.SimpleInputParamsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SimpleInputParamsOutput: ...

    @overload
    async def simple_input_params(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.SimpleInputParamsInputDict],
    ) -> models.SimpleInputParamsOutput:
        """
        This test serializes strings, numbers, and boolean values.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `SimpleInputParamsOutput`.
        """

    async def simple_input_params(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SimpleInputParamsOutput:
        return await self._invoke(
            self._select_input(models.SIMPLE_INPUT_PARAMS, args, kwargs),
            models.SIMPLE_INPUT_PARAMS,
            [],
            plugins,
        )

    @overload
    async def simple_scalar_xml_properties(
        self,
        request: models.SimpleScalarXmlPropertiesInput
        | models.SimpleScalarXmlPropertiesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SimpleScalarXmlPropertiesOutput: ...

    @overload
    async def simple_scalar_xml_properties(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.SimpleScalarXmlPropertiesInputDict],
    ) -> models.SimpleScalarXmlPropertiesOutput:
        """
        Invokes the SimpleScalarXmlProperties operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `SimpleScalarXmlPropertiesOutput`.
        """

    async def simple_scalar_xml_properties(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SimpleScalarXmlPropertiesOutput:
        return await self._invoke(
            self._select_input(models.SIMPLE_SCALAR_XML_PROPERTIES, args, kwargs),
            models.SIMPLE_SCALAR_XML_PROPERTIES,
            [],
            plugins,
        )

    @overload
    async def xml_blobs(
        self,
        request: models.XmlBlobsInput | models.XmlBlobsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlBlobsOutput2: ...

    @overload
    async def xml_blobs(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlBlobsInputDict],
    ) -> models.XmlBlobsOutput2:
        """
        Blobs are base64 encoded

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlBlobsOutput2`.
        """

    async def xml_blobs(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlBlobsOutput2:
        return await self._invoke(
            self._select_input(models.XML_BLOBS, args, kwargs),
            models.XML_BLOBS,
            [],
            plugins,
        )

    @overload
    async def xml_empty_blobs(
        self,
        request: models.XmlEmptyBlobsInput | models.XmlEmptyBlobsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlEmptyBlobsOutput: ...

    @overload
    async def xml_empty_blobs(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlEmptyBlobsInputDict],
    ) -> models.XmlEmptyBlobsOutput:
        """
        Invokes the XmlEmptyBlobs operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlEmptyBlobsOutput`.
        """

    async def xml_empty_blobs(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlEmptyBlobsOutput:
        return await self._invoke(
            self._select_input(models.XML_EMPTY_BLOBS, args, kwargs),
            models.XML_EMPTY_BLOBS,
            [],
            plugins,
        )

    @overload
    async def xml_empty_lists(
        self,
        request: models.XmlEmptyListsInput | models.XmlEmptyListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlEmptyListsOutput: ...

    @overload
    async def xml_empty_lists(
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

    async def xml_empty_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlEmptyListsOutput:
        return await self._invoke(
            self._select_input(models.XML_EMPTY_LISTS, args, kwargs),
            models.XML_EMPTY_LISTS,
            [],
            plugins,
        )

    @overload
    async def xml_enums(
        self,
        request: models.XmlEnumsInput | models.XmlEnumsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlEnumsOutput: ...

    @overload
    async def xml_enums(
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

    async def xml_enums(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlEnumsOutput:
        return await self._invoke(
            self._select_input(models.XML_ENUMS, args, kwargs),
            models.XML_ENUMS,
            [],
            plugins,
        )

    @overload
    async def xml_int_enums(
        self,
        request: models.XmlIntEnumsInput | models.XmlIntEnumsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlIntEnumsOutput: ...

    @overload
    async def xml_int_enums(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.XmlIntEnumsInputDict],
    ) -> models.XmlIntEnumsOutput:
        """
        This example serializes intEnums as top level properties, in lists,
        sets, and maps.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlIntEnumsOutput`.
        """

    async def xml_int_enums(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlIntEnumsOutput:
        return await self._invoke(
            self._select_input(models.XML_INT_ENUMS, args, kwargs),
            models.XML_INT_ENUMS,
            [],
            plugins,
        )

    @overload
    async def xml_lists(
        self,
        request: models.XmlListsInput | models.XmlListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlListsOutput2: ...

    @overload
    async def xml_lists(
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

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `XmlListsOutput2`.
        """

    async def xml_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlListsOutput2:
        return await self._invoke(
            self._select_input(models.XML_LISTS, args, kwargs),
            models.XML_LISTS,
            [],
            plugins,
        )

    @overload
    async def xml_namespaces(
        self,
        request: models.XmlNamespacesInput | models.XmlNamespacesInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlNamespacesOutput: ...

    @overload
    async def xml_namespaces(
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

    async def xml_namespaces(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlNamespacesOutput:
        return await self._invoke(
            self._select_input(models.XML_NAMESPACES, args, kwargs),
            models.XML_NAMESPACES,
            [],
            plugins,
        )

    @overload
    async def xml_timestamps(
        self,
        request: models.XmlTimestampsInput | models.XmlTimestampsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.XmlTimestampsOutput: ...

    @overload
    async def xml_timestamps(
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

    async def xml_timestamps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.XmlTimestampsOutput:
        return await self._invoke(
            self._select_input(models.XML_TIMESTAMPS, args, kwargs),
            models.XML_TIMESTAMPS,
            [],
            plugins,
        )

    async def _new_config(self) -> AsyncEC2ProtocolConfig:
        return await AsyncEC2ProtocolConfig.resolve()

    async def _post_setup(self, config: AsyncEC2ProtocolConfig) -> None:
        if config.aws_credentials_identity_resolver is None:
            config_file, profile_name = await self._profile_overrides(config)
            config.aws_credentials_identity_resolver = await AsyncIdentityChain.create(
                AWSCredentialsIdentity,
                config_file=config_file,
                profile_name=profile_name,
                region_override=config.region,
                http_client=cast(AsyncHTTPClient | None, config.transport),
            )

    async def _profile_overrides(
        self, config: AsyncEC2ProtocolConfig
    ) -> tuple[MergedConfig | None, str | None]:
        config_context = config.resolution_context()
        config_file = None
        profile_name = None
        if config_context is not None:
            config_file = await config_context.parsed_profiles()
            if config_context.profile_source is ConfigSource.OVERRIDE:
                profile_name = config_context.profile_name
        return config_file, profile_name
