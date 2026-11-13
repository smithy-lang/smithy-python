from __future__ import annotations

from typing import Unpack, overload

from smithy_core.aio.client import AsyncClient
from smithy_http.plugins import user_agent_plugin

from rpcv2cbor_client import models
from rpcv2cbor_client.aio.config import AsyncConfig, Plugin


class AsyncRpcV2Protocol(AsyncClient[AsyncConfig]):
    "Client for RpcV2Protocol."

    _client_plugins = (user_agent_plugin,)

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

        :param plugins: Callables that change the configuration for this call
        only.
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
    async def float16(
        self,
        request: models.Float16Input | models.Float16InputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.Float16Output: ...

    @overload
    async def float16(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.Float16InputDict],
    ) -> models.Float16Output:
        """
        Invokes the Float16 operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def float16(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.Float16Output:
        return await self._invoke(
            self._select_input(models.FLOAT16, args, kwargs),
            models.FLOAT16,
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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
    async def rpc_v2_cbor_dense_maps(
        self,
        request: models.RpcV2CborDenseMapsInput | models.RpcV2CborDenseMapsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.RpcV2CborDenseMapsOutput: ...

    @overload
    async def rpc_v2_cbor_dense_maps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.RpcV2CborDenseMapsInputDict],
    ) -> models.RpcV2CborDenseMapsOutput:
        """
        The example tests basic map serialization.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def rpc_v2_cbor_dense_maps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.RpcV2CborDenseMapsOutput:
        return await self._invoke(
            self._select_input(models.RPC_V2_CBOR_DENSE_MAPS, args, kwargs),
            models.RPC_V2_CBOR_DENSE_MAPS,
            [],
            plugins,
        )

    @overload
    async def rpc_v2_cbor_lists(
        self,
        request: models.RpcV2CborListsInput | models.RpcV2CborListsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.RpcV2CborListsOutput: ...

    @overload
    async def rpc_v2_cbor_lists(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.RpcV2CborListsInputDict],
    ) -> models.RpcV2CborListsOutput:
        """
        This test case serializes JSON lists for the following cases for both
        input and output:

        1. Normal lists.
        2. Normal sets.
        3. Lists of lists.
        4. Lists of structures.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def rpc_v2_cbor_lists(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.RpcV2CborListsOutput:
        return await self._invoke(
            self._select_input(models.RPC_V2_CBOR_LISTS, args, kwargs),
            models.RPC_V2_CBOR_LISTS,
            [],
            plugins,
        )

    @overload
    async def rpc_v2_cbor_sparse_maps(
        self,
        request: models.RpcV2CborSparseMapsInput | models.RpcV2CborSparseMapsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.RpcV2CborSparseMapsOutput: ...

    @overload
    async def rpc_v2_cbor_sparse_maps(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.RpcV2CborSparseMapsInputDict],
    ) -> models.RpcV2CborSparseMapsOutput:
        """
        Invokes the RpcV2CborSparseMaps operation.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def rpc_v2_cbor_sparse_maps(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.RpcV2CborSparseMapsOutput:
        return await self._invoke(
            self._select_input(models.RPC_V2_CBOR_SPARSE_MAPS, args, kwargs),
            models.RPC_V2_CBOR_SPARSE_MAPS,
            [],
            plugins,
        )

    @overload
    async def rpc_v2_cbor_unions(
        self,
        request: models.RpcV2CborUnionsInput | models.RpcV2CborUnionsInputDict,
        /,
        *,
        plugins: list[Plugin] | None = None,
    ) -> models.RpcV2CborUnionsOutput: ...

    @overload
    async def rpc_v2_cbor_unions(
        self,
        /,
        *,
        plugins: list[Plugin] | None = None,
        **kwargs: Unpack[models.RpcV2CborUnionsInputDict],
    ) -> models.RpcV2CborUnionsOutput:
        """
        This operation uses unions for inputs and outputs.

        :param plugins: Callables that change the configuration for this call
        only.
        """

    async def rpc_v2_cbor_unions(
        self, /, *args: object, plugins: list[Plugin] | None = None, **kwargs: object
    ) -> models.RpcV2CborUnionsOutput:
        return await self._invoke(
            self._select_input(models.RPC_V2_CBOR_UNIONS, args, kwargs),
            models.RPC_V2_CBOR_UNIONS,
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

        :param plugins: Callables that change the configuration for this call
        only.
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

        :param plugins: Callables that change the configuration for this call
        only.
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

    def _new_config(self) -> AsyncConfig:
        return AsyncConfig()
