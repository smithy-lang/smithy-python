from __future__ import annotations

from typing import Unpack, cast, overload

from smithy_aws_core.aio.identity.chain import AsyncIdentityChain
from smithy_aws_core.config.merged_config import MergedConfig
from smithy_aws_core.config.types import ConfigSource
from smithy_aws_core.identity.components import AWSCredentialsIdentity
from smithy_core.aio.client import AsyncClient
from smithy_http.aio.interfaces import AsyncHTTPClient
from smithy_http.plugins import user_agent_plugin

from awsjson11_client import models
from awsjson11_client.aio.config import AsyncJsonProtocolConfig, Plugin
from awsjson11_client.aio.user_agent import aws_user_agent_plugin


class AsyncJsonProtocolClient(AsyncClient[AsyncJsonProtocolConfig]):
    "Client for JsonProtocol."

    _client_plugins = (aws_user_agent_plugin, user_agent_plugin)

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
    async def empty_operation(
        self,
        request: models.EmptyOperationInput | models.EmptyOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EmptyOperationOutput: ...

    @overload
    async def empty_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.EmptyOperationInputDict],
    ) -> models.EmptyOperationOutput:
        """
        Invokes the EmptyOperation operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `EmptyOperationOutput`.
        """

    async def empty_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EmptyOperationOutput:
        return await self._invoke(
            self._select_input(models.EMPTY_OPERATION, args, kwargs),
            models.EMPTY_OPERATION,
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
        3. A ComplexError error.

        Implementations must be able to successfully take a response and
        properly deserialize successful and error responses.

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
    async def kitchen_sink_operation(
        self,
        request: models.KitchenSinkOperationInput
        | models.KitchenSinkOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.KitchenSinkOperationOutput: ...

    @overload
    async def kitchen_sink_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.KitchenSinkOperationInputDict],
    ) -> models.KitchenSinkOperationOutput:
        """
        Invokes the KitchenSinkOperation operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `KitchenSinkOperationOutput`.
        """

    async def kitchen_sink_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.KitchenSinkOperationOutput:
        return await self._invoke(
            self._select_input(models.KITCHEN_SINK_OPERATION, args, kwargs),
            models.KITCHEN_SINK_OPERATION,
            [],
            plugins,
        )

    @overload
    async def null_operation(
        self,
        request: models.NullOperationInput | models.NullOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NullOperationOutput: ...

    @overload
    async def null_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NullOperationInputDict],
    ) -> models.NullOperationOutput:
        """
        Invokes the NullOperation operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `NullOperationOutput`.
        """

    async def null_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NullOperationOutput:
        return await self._invoke(
            self._select_input(models.NULL_OPERATION, args, kwargs),
            models.NULL_OPERATION,
            [],
            plugins,
        )

    @overload
    async def operation_with_optional_input_output(
        self,
        request: models.OperationWithOptionalInputOutputInput
        | models.OperationWithOptionalInputOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OperationWithOptionalInputOutputOutput: ...

    @overload
    async def operation_with_optional_input_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.OperationWithOptionalInputOutputInputDict],
    ) -> models.OperationWithOptionalInputOutputOutput:
        """
        Invokes the OperationWithOptionalInputOutput operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `OperationWithOptionalInputOutputOutput`.
        """

    async def operation_with_optional_input_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OperationWithOptionalInputOutputOutput:
        return await self._invoke(
            self._select_input(
                models.OPERATION_WITH_OPTIONAL_INPUT_OUTPUT, args, kwargs
            ),
            models.OPERATION_WITH_OPTIONAL_INPUT_OUTPUT,
            [],
            plugins,
        )

    @overload
    async def put_and_get_inline_documents(
        self,
        request: models.PutAndGetInlineDocumentsInput
        | models.PutAndGetInlineDocumentsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.PutAndGetInlineDocumentsOutput: ...

    @overload
    async def put_and_get_inline_documents(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.PutAndGetInlineDocumentsInputDict],
    ) -> models.PutAndGetInlineDocumentsOutput:
        """
        This example serializes an inline document as part of the payload.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `PutAndGetInlineDocumentsOutput`.
        """

    async def put_and_get_inline_documents(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.PutAndGetInlineDocumentsOutput:
        return await self._invoke(
            self._select_input(models.PUT_AND_GET_INLINE_DOCUMENTS, args, kwargs),
            models.PUT_AND_GET_INLINE_DOCUMENTS,
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
    async def sparse_nulls_operation(
        self,
        request: models.SparseNullsOperationInput
        | models.SparseNullsOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.SparseNullsOperationOutput: ...

    @overload
    async def sparse_nulls_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.SparseNullsOperationInputDict],
    ) -> models.SparseNullsOperationOutput:
        """
        Invokes the SparseNullsOperation operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `SparseNullsOperationOutput`.
        """

    async def sparse_nulls_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.SparseNullsOperationOutput:
        return await self._invoke(
            self._select_input(models.SPARSE_NULLS_OPERATION, args, kwargs),
            models.SPARSE_NULLS_OPERATION,
            [],
            plugins,
        )

    async def _new_config(self) -> AsyncJsonProtocolConfig:
        return await AsyncJsonProtocolConfig.resolve()

    async def _post_setup(self, config: AsyncJsonProtocolConfig) -> None:
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
        self, config: AsyncJsonProtocolConfig
    ) -> tuple[MergedConfig | None, str | None]:
        config_context = config.resolution_context()
        config_file = None
        profile_name = None
        if config_context is not None:
            config_file = await config_context.parsed_profiles()
            if config_context.profile_source is ConfigSource.OVERRIDE:
                profile_name = config_context.profile_name
        return config_file, profile_name
