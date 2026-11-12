from smithy_core._dynamic_models import ModelRegistry
from smithy_core.exceptions import ModeledError

from ._private import schemas


class ServiceError(ModeledError):
    """
    Base error for all errors in the service.

    Some exceptions do not extend from this class, including synthetic,
    implicit, and shared exception types.
    """


_MODEL_INDEX = {
    "ValidationException": "VALIDATION_EXCEPTION",
    "ValidationExceptionField": "VALIDATION_EXCEPTION_FIELD",
    "ClientOptionalDefaults": "CLIENT_OPTIONAL_DEFAULTS",
    "ComplexError": "COMPLEX_ERROR",
    "ComplexNestedErrorData": "COMPLEX_NESTED_ERROR_DATA",
    "Defaults": "DEFAULTS",
    "EmptyStructure": "EMPTY_STRUCTURE",
    "Float16Output": "FLOAT16_OUTPUT",
    "FractionalSecondsOutput": "FRACTIONAL_SECONDS_OUTPUT",
    "GreetingWithErrorsOutput": "GREETING_WITH_ERRORS_OUTPUT",
    "InvalidGreeting": "INVALID_GREETING",
    "OperationWithDefaultsInput": "OPERATION_WITH_DEFAULTS_INPUT",
    "OperationWithDefaultsOutput": "OPERATION_WITH_DEFAULTS_OUTPUT",
    "RecursiveShapesInputOutput": "RECURSIVE_SHAPES_INPUT_OUTPUT",
    "RecursiveShapesInputOutputNested1": "RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1",
    "RecursiveShapesInputOutputNested2": "RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2",
    "RpcV2CborDenseMapsInputOutput": "RPC_V2_CBOR_DENSE_MAPS_INPUT_OUTPUT",
    "RpcV2CborListInputOutput": "RPC_V2_CBOR_LIST_INPUT_OUTPUT",
    "RpcV2CborNestedUnion": "RPC_V2_CBOR_NESTED_UNION",
    "RpcV2CborNestedUnionStringValue": "RPC_V2_CBOR_NESTED_UNION",
    "RpcV2CborNestedUnionUnknown": "RPC_V2_CBOR_NESTED_UNION",
    "RpcV2CborSparseMapsInputOutput": "RPC_V2_CBOR_SPARSE_MAPS_INPUT_OUTPUT",
    "RpcV2CborUnion": "RPC_V2_CBOR_UNION",
    "RpcV2CborUnionStringValue": "RPC_V2_CBOR_UNION",
    "RpcV2CborUnionUnionValue": "RPC_V2_CBOR_UNION",
    "RpcV2CborUnionUnknown": "RPC_V2_CBOR_UNION",
    "RpcV2CborUnionInputOutput": "RPC_V2_CBOR_UNION_INPUT_OUTPUT",
    "SimpleScalarStructure": "SIMPLE_SCALAR_STRUCTURE",
    "SimpleStructure": "SIMPLE_STRUCTURE",
    "SparseNullsOperationInputOutput": "SPARSE_NULLS_OPERATION_INPUT_OUTPUT",
    "StructureListMember": "STRUCTURE_LIST_MEMBER",
    "TestEnum": "TEST_ENUM",
    "TestIntEnum": "TEST_INT_ENUM",
    "FooEnum": "FOO_ENUM",
    "GreetingStruct": "GREETING_STRUCT",
    "IntegerEnum": "INTEGER_ENUM",
}

_RENAMES: dict[str, str] = {}

_TARGET_NAMES: dict[str, str] = {}

_MODEL_NAMES = tuple(_MODEL_INDEX)
__all__ = ("ServiceError", *_MODEL_NAMES)  # pyright: ignore[reportUnsupportedDunderAll]


_registry = ModelRegistry(
    schemas,
    renames=_RENAMES,
    index=_MODEL_INDEX,
    target_names=_TARGET_NAMES,
    shape_names=frozenset(
        {
            "ClientOptionalDefaults",
            "ComplexError",
            "ComplexNestedErrorData",
            "Defaults",
            "EmptyStructure",
            "Float16Output",
            "FooEnum",
            "FractionalSecondsOutput",
            "GreetingStruct",
            "GreetingWithErrorsOutput",
            "IntegerEnum",
            "InvalidGreeting",
            "OperationWithDefaultsInput",
            "OperationWithDefaultsOutput",
            "RecursiveShapesInputOutput",
            "RecursiveShapesInputOutputNested1",
            "RecursiveShapesInputOutputNested2",
            "RpcV2CborDenseMapsInputOutput",
            "RpcV2CborListInputOutput",
            "RpcV2CborNestedUnion",
            "RpcV2CborSparseMapsInputOutput",
            "RpcV2CborUnion",
            "RpcV2CborUnionInputOutput",
            "SimpleScalarStructure",
            "SimpleStructure",
            "SparseNullsOperationInputOutput",
            "StructureListMember",
            "TestEnum",
            "TestIntEnum",
            "ValidationException",
            "ValidationExceptionField",
        }
    ),
    service_error="ServiceError",
)
del schemas, ModelRegistry, ModeledError


def __getattr__(name: str):
    value = _registry.build(name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *__all__})
