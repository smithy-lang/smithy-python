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
    "FractionalSecondsOutput": "FRACTIONAL_SECONDS_OUTPUT",
    "GreetingWithErrorsOutput": "GREETING_WITH_ERRORS_OUTPUT",
    "InvalidGreeting": "INVALID_GREETING",
    "OperationWithDefaultsInput": "OPERATION_WITH_DEFAULTS_INPUT",
    "OperationWithDefaultsOutput": "OPERATION_WITH_DEFAULTS_OUTPUT",
    "RecursiveShapesInputOutputNested1": "RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1",
    "RecursiveShapesInputOutputNested2": "RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2",
    "StructureListMember": "STRUCTURE_LIST_MEMBER",
    "TestEnum": "TEST_ENUM",
    "TestIntEnum": "TEST_INT_ENUM",
    "FooEnum": "FOO_ENUM",
    "GreetingStruct": "GREETING_STRUCT",
    "IntegerEnum": "INTEGER_ENUM",
    "BigDecimalOperationInput": "BIG_DECIMAL_OPERATION_INPUT",
    "BigDecimalOperationOutput": "BIG_DECIMAL_OPERATION_OUTPUT",
    "BigIntegerOperationInput": "BIG_INTEGER_OPERATION_INPUT",
    "BigIntegerOperationOutput": "BIG_INTEGER_OPERATION_OUTPUT",
    "EmptyInputOutputInput": "EMPTY_INPUT_OUTPUT_INPUT",
    "EmptyInputOutputOutput": "EMPTY_INPUT_OUTPUT_OUTPUT",
    "FractionalSecondsInput": "FRACTIONAL_SECONDS_INPUT",
    "GreetingWithErrorsInput": "GREETING_WITH_ERRORS_INPUT",
    "NoInputOutputInput": "NO_INPUT_OUTPUT_INPUT",
    "NoInputOutputOutput": "NO_INPUT_OUTPUT_OUTPUT",
    "OptionalInputOutputInput": "OPTIONAL_INPUT_OUTPUT_INPUT",
    "OptionalInputOutputOutput": "OPTIONAL_INPUT_OUTPUT_OUTPUT",
    "RecursiveShapesInput": "RECURSIVE_SHAPES_INPUT",
    "RecursiveShapesOutput": "RECURSIVE_SHAPES_OUTPUT",
    "RpcV2JsonDenseMapsInput": "RPC_V2_JSON_DENSE_MAPS_INPUT",
    "RpcV2JsonDenseMapsOutput": "RPC_V2_JSON_DENSE_MAPS_OUTPUT",
    "RpcV2JsonListsInput": "RPC_V2_JSON_LISTS_INPUT",
    "RpcV2JsonListsOutput": "RPC_V2_JSON_LISTS_OUTPUT",
    "RpcV2JsonSparseMapsInput": "RPC_V2_JSON_SPARSE_MAPS_INPUT",
    "RpcV2JsonSparseMapsOutput": "RPC_V2_JSON_SPARSE_MAPS_OUTPUT",
    "SimpleScalarPropertiesInput": "SIMPLE_SCALAR_PROPERTIES_INPUT",
    "SimpleScalarPropertiesOutput": "SIMPLE_SCALAR_PROPERTIES_OUTPUT",
    "SparseNullsOperationInput": "SPARSE_NULLS_OPERATION_INPUT",
    "SparseNullsOperationOutput": "SPARSE_NULLS_OPERATION_OUTPUT",
    "TimestampFormatIgnoredInput": "TIMESTAMP_FORMAT_IGNORED_INPUT",
    "TimestampFormatIgnoredOutput": "TIMESTAMP_FORMAT_IGNORED_OUTPUT",
}

_RENAMES: dict[str, str] = {}

_TARGET_NAMES: dict[str, str] = {}

_OPERATIONS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "BIG_DECIMAL_OPERATION": (
        (),
        ("smithy.api#noAuth",),
    ),
    "BIG_INTEGER_OPERATION": (
        (),
        ("smithy.api#noAuth",),
    ),
    "EMPTY_INPUT_OUTPUT": (
        (),
        ("smithy.api#noAuth",),
    ),
    "FRACTIONAL_SECONDS": (
        (),
        ("smithy.api#noAuth",),
    ),
    "GREETING_WITH_ERRORS": (
        (
            "smithy.protocoltests.rpcv2Json#ComplexError",
            "smithy.protocoltests.rpcv2Json#InvalidGreeting",
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
    "RPC_V2_JSON_DENSE_MAPS": (
        ("smithy.framework#ValidationException",),
        ("smithy.api#noAuth",),
    ),
    "RPC_V2_JSON_LISTS": (
        ("smithy.framework#ValidationException",),
        ("smithy.api#noAuth",),
    ),
    "RPC_V2_JSON_SPARSE_MAPS": (
        ("smithy.framework#ValidationException",),
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
    "TIMESTAMP_FORMAT_IGNORED": (
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
            "BigDecimalOperationInput",
            "BigDecimalOperationOutput",
            "BigIntegerOperationInput",
            "BigIntegerOperationOutput",
            "ClientOptionalDefaults",
            "ComplexError",
            "ComplexNestedErrorData",
            "Defaults",
            "EmptyInputOutputInput",
            "EmptyInputOutputOutput",
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
            "RpcV2JsonDenseMapsInput",
            "RpcV2JsonDenseMapsOutput",
            "RpcV2JsonListsInput",
            "RpcV2JsonListsOutput",
            "RpcV2JsonSparseMapsInput",
            "RpcV2JsonSparseMapsOutput",
            "SimpleScalarPropertiesInput",
            "SimpleScalarPropertiesOutput",
            "SparseNullsOperationInput",
            "SparseNullsOperationOutput",
            "StructureListMember",
            "TestEnum",
            "TestIntEnum",
            "TimestampFormatIgnoredInput",
            "TimestampFormatIgnoredOutput",
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
