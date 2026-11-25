from __future__ import annotations

from typing import Unpack, overload

from smithy_core.aio.client import AsyncClient
from smithy_http.plugins import user_agent_plugin

from rpcv2json_client import models
from rpcv2json_client.aio.config import AsyncConfig, Plugin


class AsyncRpcV2JsonProtocol(AsyncClient[AsyncConfig]):
    "Client for RpcV2JsonProtocol."

    _client_plugins = (user_agent_plugin,)

    @overload
    async def big_decimal_operation(
        self,
        request: models.BigDecimalOperationInput | models.BigDecimalOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.BigDecimalOperationOutput: ...

    @overload
    async def big_decimal_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.BigDecimalOperationInputDict],
    ) -> models.BigDecimalOperationOutput:
        """
        Invokes the BigDecimalOperation operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `BigDecimalOperationOutput`.
        """

    async def big_decimal_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.BigDecimalOperationOutput:
        return await self._invoke(
            self._select_input(models.BIG_DECIMAL_OPERATION, args, kwargs),
            models.BIG_DECIMAL_OPERATION,
            [],
            plugins,
        )

    @overload
    async def big_integer_operation(
        self,
        request: models.BigIntegerOperationInput | models.BigIntegerOperationInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.BigIntegerOperationOutput: ...

    @overload
    async def big_integer_operation(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.BigIntegerOperationInputDict],
    ) -> models.BigIntegerOperationOutput:
        """
        Invokes the BigIntegerOperation operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `BigIntegerOperationOutput`.
        """

    async def big_integer_operation(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.BigIntegerOperationOutput:
        return await self._invoke(
            self._select_input(models.BIG_INTEGER_OPERATION, args, kwargs),
            models.BIG_INTEGER_OPERATION,
            [],
            plugins,
        )

    @overload
    async def empty_input_output(
        self,
        request: models.EmptyInputOutputInput | models.EmptyInputOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.EmptyInputOutputOutput: ...

    @overload
    async def empty_input_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.EmptyInputOutputInputDict],
    ) -> models.EmptyInputOutputOutput:
        """
        Invokes the EmptyInputOutput operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `EmptyInputOutputOutput`.
        """

    async def empty_input_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.EmptyInputOutputOutput:
        return await self._invoke(
            self._select_input(models.EMPTY_INPUT_OUTPUT, args, kwargs),
            models.EMPTY_INPUT_OUTPUT,
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
    async def no_input_output(
        self,
        request: models.NoInputOutputInput | models.NoInputOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.NoInputOutputOutput: ...

    @overload
    async def no_input_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.NoInputOutputInputDict],
    ) -> models.NoInputOutputOutput:
        """
        Invokes the NoInputOutput operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `NoInputOutputOutput`.
        """

    async def no_input_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.NoInputOutputOutput:
        return await self._invoke(
            self._select_input(models.NO_INPUT_OUTPUT, args, kwargs),
            models.NO_INPUT_OUTPUT,
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
    async def optional_input_output(
        self,
        request: models.OptionalInputOutputInput | models.OptionalInputOutputInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.OptionalInputOutputOutput: ...

    @overload
    async def optional_input_output(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.OptionalInputOutputInputDict],
    ) -> models.OptionalInputOutputOutput:
        """
        Invokes the OptionalInputOutput operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `OptionalInputOutputOutput`.
        """

    async def optional_input_output(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.OptionalInputOutputOutput:
        return await self._invoke(
            self._select_input(models.OPTIONAL_INPUT_OUTPUT, args, kwargs),
            models.OPTIONAL_INPUT_OUTPUT,
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
        Invokes the RecursiveShapes operation.

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
    async def rpc_v2_json_dense_maps(
        self,
        request: models.RpcV2JsonDenseMapsInput | models.RpcV2JsonDenseMapsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.RpcV2JsonDenseMapsOutput: ...

    @overload
    async def rpc_v2_json_dense_maps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.RpcV2JsonDenseMapsInputDict],
    ) -> models.RpcV2JsonDenseMapsOutput:
        """
        The example tests basic map serialization.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `RpcV2JsonDenseMapsOutput`.
        """

    async def rpc_v2_json_dense_maps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.RpcV2JsonDenseMapsOutput:
        return await self._invoke(
            self._select_input(models.RPC_V2_JSON_DENSE_MAPS, args, kwargs),
            models.RPC_V2_JSON_DENSE_MAPS,
            [],
            plugins,
        )

    @overload
    async def rpc_v2_json_lists(
        self,
        request: models.RpcV2JsonListsInput | models.RpcV2JsonListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.RpcV2JsonListsOutput: ...

    @overload
    async def rpc_v2_json_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.RpcV2JsonListsInputDict],
    ) -> models.RpcV2JsonListsOutput:
        """
        This test case serializes JSON lists for the following cases for both
        input and output:

        1. Normal lists.
        2. Normal sets.
        3. Lists of lists.
        4. Lists of structures.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `RpcV2JsonListsOutput`.
        """

    async def rpc_v2_json_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.RpcV2JsonListsOutput:
        return await self._invoke(
            self._select_input(models.RPC_V2_JSON_LISTS, args, kwargs),
            models.RPC_V2_JSON_LISTS,
            [],
            plugins,
        )

    @overload
    async def rpc_v2_json_sparse_maps(
        self,
        request: models.RpcV2JsonSparseMapsInput | models.RpcV2JsonSparseMapsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.RpcV2JsonSparseMapsOutput: ...

    @overload
    async def rpc_v2_json_sparse_maps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.RpcV2JsonSparseMapsInputDict],
    ) -> models.RpcV2JsonSparseMapsOutput:
        """
        Invokes the RpcV2JsonSparseMaps operation.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `RpcV2JsonSparseMapsOutput`.
        """

    async def rpc_v2_json_sparse_maps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.RpcV2JsonSparseMapsOutput:
        return await self._invoke(
            self._select_input(models.RPC_V2_JSON_SPARSE_MAPS, args, kwargs),
            models.RPC_V2_JSON_SPARSE_MAPS,
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

    @overload
    async def timestamp_format_ignored(
        self,
        request: models.TimestampFormatIgnoredInput
        | models.TimestampFormatIgnoredInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.TimestampFormatIgnoredOutput: ...

    @overload
    async def timestamp_format_ignored(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.TimestampFormatIgnoredInputDict],
    ) -> models.TimestampFormatIgnoredOutput:
        """
        This operation tests that the rpcv2Json protocol always uses
        epoch-seconds
        for timestamp serialization, regardless of the `timestampFormat` trait.
        Members targeting `DateTime` (date-time), `HttpDate` (http-date), and
        `EpochSeconds` (epoch-seconds) must all serialize as JSON numbers.

        Args:
            plugins:
                Callables that change the configuration for this call only.

        Returns:
            An instance of `TimestampFormatIgnoredOutput`.
        """

    async def timestamp_format_ignored(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.TimestampFormatIgnoredOutput:
        return await self._invoke(
            self._select_input(models.TIMESTAMP_FORMAT_IGNORED, args, kwargs),
            models.TIMESTAMP_FORMAT_IGNORED,
            [],
            plugins,
        )

    def _new_config(self) -> AsyncConfig:
        return AsyncConfig()
