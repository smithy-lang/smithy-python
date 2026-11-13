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
    "BigDecimalStructure": "BIG_DECIMAL_STRUCTURE",
    "BigIntegerStructure": "BIG_INTEGER_STRUCTURE",
    "ClientOptionalDefaults": "CLIENT_OPTIONAL_DEFAULTS",
    "ComplexError": "COMPLEX_ERROR",
    "ComplexNestedErrorData": "COMPLEX_NESTED_ERROR_DATA",
    "Defaults": "DEFAULTS",
    "EmptyStructure": "EMPTY_STRUCTURE",
    "FractionalSecondsOutput": "FRACTIONAL_SECONDS_OUTPUT",
    "GreetingWithErrorsOutput": "GREETING_WITH_ERRORS_OUTPUT",
    "InvalidGreeting": "INVALID_GREETING",
    "OperationWithDefaultsInput": "OPERATION_WITH_DEFAULTS_INPUT",
    "OperationWithDefaultsOutput": "OPERATION_WITH_DEFAULTS_OUTPUT",
    "RecursiveShapesInputOutput": "RECURSIVE_SHAPES_INPUT_OUTPUT",
    "RecursiveShapesInputOutputNested1": "RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED1",
    "RecursiveShapesInputOutputNested2": "RECURSIVE_SHAPES_INPUT_OUTPUT_NESTED2",
    "RpcV2JsonDenseMapsInputOutput": "RPC_V2_JSON_DENSE_MAPS_INPUT_OUTPUT",
    "RpcV2JsonListInputOutput": "RPC_V2_JSON_LIST_INPUT_OUTPUT",
    "RpcV2JsonSparseMapsInputOutput": "RPC_V2_JSON_SPARSE_MAPS_INPUT_OUTPUT",
    "SimpleScalarStructure": "SIMPLE_SCALAR_STRUCTURE",
    "SimpleStructure": "SIMPLE_STRUCTURE",
    "SparseNullsOperationInputOutput": "SPARSE_NULLS_OPERATION_INPUT_OUTPUT",
    "StructureListMember": "STRUCTURE_LIST_MEMBER",
    "TestEnum": "TEST_ENUM",
    "TestIntEnum": "TEST_INT_ENUM",
    "TimestampFormatIgnoredIO": "TIMESTAMP_FORMAT_IGNORED_IO",
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
            "BigDecimalStructure",
            "BigIntegerStructure",
            "ClientOptionalDefaults",
            "ComplexError",
            "ComplexNestedErrorData",
            "Defaults",
            "EmptyStructure",
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
            "RpcV2JsonDenseMapsInputOutput",
            "RpcV2JsonListInputOutput",
            "RpcV2JsonSparseMapsInputOutput",
            "SimpleScalarStructure",
            "SimpleStructure",
            "SparseNullsOperationInputOutput",
            "StructureListMember",
            "TestEnum",
            "TestIntEnum",
            "TimestampFormatIgnoredIO",
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
