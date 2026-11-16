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
    "Float16Output": "FLOAT16_OUTPUT",
    "FractionalSecondsOutput": "FRACTIONAL_SECONDS_OUTPUT",
    "GreetingWithErrorsOutput": "GREETING_WITH_ERRORS_OUTPUT",
    "InvalidGreeting": "INVALID_GREETING",
    "OperationWithDefaultsInput": "OPERATION_WITH_DEFAULTS_INPUT",
    "OperationWithDefaultsOutput": "OPERATION_WITH_DEFAULTS_OUTPUT",
    "RecursiveShapesInputOutputNested1": "RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1",
    "RecursiveShapesInputOutputNested2": "RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2",
    "RpcV2CborNestedUnion": "RPC_V2_CBOR_NESTED_UNION",
    "RpcV2CborNestedUnionStringValue": "RPC_V2_CBOR_NESTED_UNION",
    "RpcV2CborNestedUnionUnknown": "RPC_V2_CBOR_NESTED_UNION",
    "RpcV2CborUnion": "RPC_V2_CBOR_UNION",
    "RpcV2CborUnionStringValue": "RPC_V2_CBOR_UNION",
    "RpcV2CborUnionUnionValue": "RPC_V2_CBOR_UNION",
    "RpcV2CborUnionUnknown": "RPC_V2_CBOR_UNION",
    "StructureListMember": "STRUCTURE_LIST_MEMBER",
    "TestEnum": "TEST_ENUM",
    "TestIntEnum": "TEST_INT_ENUM",
    "FooEnum": "FOO_ENUM",
    "GreetingStruct": "GREETING_STRUCT",
    "IntegerEnum": "INTEGER_ENUM",
    "EmptyInputOutputInput": "EMPTY_INPUT_OUTPUT_INPUT",
    "EmptyInputOutputOutput": "EMPTY_INPUT_OUTPUT_OUTPUT",
    "Float16Input": "FLOAT16_INPUT",
    "FractionalSecondsInput": "FRACTIONAL_SECONDS_INPUT",
    "GreetingWithErrorsInput": "GREETING_WITH_ERRORS_INPUT",
    "NoInputOutputInput": "NO_INPUT_OUTPUT_INPUT",
    "NoInputOutputOutput": "NO_INPUT_OUTPUT_OUTPUT",
    "OptionalInputOutputInput": "OPTIONAL_INPUT_OUTPUT_INPUT",
    "OptionalInputOutputOutput": "OPTIONAL_INPUT_OUTPUT_OUTPUT",
    "RecursiveShapesInput": "RECURSIVE_SHAPES_INPUT",
    "RecursiveShapesOutput": "RECURSIVE_SHAPES_OUTPUT",
    "RpcV2CborDenseMapsInput": "RPC_V2_CBOR_DENSE_MAPS_INPUT",
    "RpcV2CborDenseMapsOutput": "RPC_V2_CBOR_DENSE_MAPS_OUTPUT",
    "RpcV2CborListsInput": "RPC_V2_CBOR_LISTS_INPUT",
    "RpcV2CborListsOutput": "RPC_V2_CBOR_LISTS_OUTPUT",
    "RpcV2CborSparseMapsInput": "RPC_V2_CBOR_SPARSE_MAPS_INPUT",
    "RpcV2CborSparseMapsOutput": "RPC_V2_CBOR_SPARSE_MAPS_OUTPUT",
    "RpcV2CborUnionsInput": "RPC_V2_CBOR_UNIONS_INPUT",
    "RpcV2CborUnionsOutput": "RPC_V2_CBOR_UNIONS_OUTPUT",
    "SimpleScalarPropertiesInput": "SIMPLE_SCALAR_PROPERTIES_INPUT",
    "SimpleScalarPropertiesOutput": "SIMPLE_SCALAR_PROPERTIES_OUTPUT",
    "SparseNullsOperationInput": "SPARSE_NULLS_OPERATION_INPUT",
    "SparseNullsOperationOutput": "SPARSE_NULLS_OPERATION_OUTPUT",
}

_RENAMES: dict[str, str] = {}

_TARGET_NAMES: dict[str, str] = {}

_OPERATIONS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "EMPTY_INPUT_OUTPUT": (
        (),
        ("smithy.api#noAuth",),
    ),
    "FLOAT16": (
        (),
        ("smithy.api#noAuth",),
    ),
    "FRACTIONAL_SECONDS": (
        (),
        ("smithy.api#noAuth",),
    ),
    "GREETING_WITH_ERRORS": (
        (
            "smithy.protocoltests.rpcv2Cbor#ComplexError",
            "smithy.protocoltests.rpcv2Cbor#InvalidGreeting",
        ),
        ("smithy.api#noAuth",),
    ),
    "NO_INPUT_OUTPUT": (
        (),
        ("smithy.api#noAuth",),
    ),
    "OPERATION_WITH_DEFAULTS": (
        ("smithy.framework#ValidationException",),
        ("smithy.api#noAuth",),
    ),
    "OPTIONAL_INPUT_OUTPUT": (
        (),
        ("smithy.api#noAuth",),
    ),
    "RECURSIVE_SHAPES": (
        (),
        ("smithy.api#noAuth",),
    ),
    "RPC_V2_CBOR_DENSE_MAPS": (
        ("smithy.framework#ValidationException",),
        ("smithy.api#noAuth",),
    ),
    "RPC_V2_CBOR_LISTS": (
        ("smithy.framework#ValidationException",),
        ("smithy.api#noAuth",),
    ),
    "RPC_V2_CBOR_SPARSE_MAPS": (
        ("smithy.framework#ValidationException",),
        ("smithy.api#noAuth",),
    ),
    "RPC_V2_CBOR_UNIONS": (
        (),
        ("smithy.api#noAuth",),
    ),
    "SIMPLE_SCALAR_PROPERTIES": (
        (),
        ("smithy.api#noAuth",),
    ),
    "SPARSE_NULLS_OPERATION": (
        (),
        ("smithy.api#noAuth",),
    ),
}

_MODEL_NAMES = tuple(_MODEL_INDEX)
__all__ = ("ServiceError", *_MODEL_NAMES, *_OPERATIONS)  # pyright: ignore[reportUnsupportedDunderAll]


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
            "EmptyInputOutputInput",
            "EmptyInputOutputOutput",
            "Float16Input",
            "Float16Output",
            "FooEnum",
            "FractionalSecondsInput",
            "FractionalSecondsOutput",
            "GreetingStruct",
            "GreetingWithErrorsInput",
            "GreetingWithErrorsOutput",
            "IntegerEnum",
            "InvalidGreeting",
            "NoInputOutputInput",
            "NoInputOutputOutput",
            "OperationWithDefaultsInput",
            "OperationWithDefaultsOutput",
            "OptionalInputOutputInput",
            "OptionalInputOutputOutput",
            "RecursiveShapesInput",
            "RecursiveShapesInputOutputNested1",
            "RecursiveShapesInputOutputNested2",
            "RecursiveShapesOutput",
            "RpcV2CborDenseMapsInput",
            "RpcV2CborDenseMapsOutput",
            "RpcV2CborListsInput",
            "RpcV2CborListsOutput",
            "RpcV2CborNestedUnion",
            "RpcV2CborSparseMapsInput",
            "RpcV2CborSparseMapsOutput",
            "RpcV2CborUnion",
            "RpcV2CborUnionsInput",
            "RpcV2CborUnionsOutput",
            "SimpleScalarPropertiesInput",
            "SimpleScalarPropertiesOutput",
            "SparseNullsOperationInput",
            "SparseNullsOperationOutput",
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
    if (data := _OPERATIONS.get(name)) is not None:
        return globals().setdefault(name, _registry.build_operation(name, *data))
    value = _registry.build(name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *__all__})
