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
    "ComplexError": "COMPLEX_ERROR",
    "ComplexNestedErrorData": "COMPLEX_NESTED_ERROR_DATA",
    "ContentTypeParametersInput": "CONTENT_TYPE_PARAMETERS_INPUT",
    "ContentTypeParametersOutput": "CONTENT_TYPE_PARAMETERS_OUTPUT",
    "DatetimeOffsetsOutput": "DATETIME_OFFSETS_OUTPUT",
    "EmptyStruct": "EMPTY_STRUCT",
    "ErrorWithMembers": "ERROR_WITH_MEMBERS",
    "ErrorWithoutMembers": "ERROR_WITHOUT_MEMBERS",
    "FooError": "FOO_ERROR",
    "FractionalSecondsOutput": "FRACTIONAL_SECONDS_OUTPUT",
    "GreetingWithErrorsOutput": "GREETING_WITH_ERRORS_OUTPUT",
    "HostLabelInput": "HOST_LABEL_INPUT",
    "InvalidGreeting": "INVALID_GREETING",
    "JsonEnumsInputOutput": "JSON_ENUMS_INPUT_OUTPUT",
    "JsonIntEnumsInputOutput": "JSON_INT_ENUMS_INPUT_OUTPUT",
    "KitchenSink": "KITCHEN_SINK",
    "MyUnion": "MY_UNION",
    "MyUnionStringValue": "MY_UNION",
    "MyUnionBooleanValue": "MY_UNION",
    "MyUnionNumberValue": "MY_UNION",
    "MyUnionBlobValue": "MY_UNION",
    "MyUnionTimestampValue": "MY_UNION",
    "MyUnionEnumValue": "MY_UNION",
    "MyUnionListValue": "MY_UNION",
    "MyUnionMapValue": "MY_UNION",
    "MyUnionStructureValue": "MY_UNION",
    "MyUnionUnknown": "MY_UNION",
    "NullOperationInputOutput": "NULL_OPERATION_INPUT_OUTPUT",
    "OperationWithOptionalInputOutputInput": "OPERATION_WITH_OPTIONAL_INPUT_OUTPUT_INPUT",
    "OperationWithOptionalInputOutputOutput": "OPERATION_WITH_OPTIONAL_INPUT_OUTPUT_OUTPUT",
    "PutAndGetInlineDocumentsInputOutput": "PUT_AND_GET_INLINE_DOCUMENTS_INPUT_OUTPUT",
    "PutWithContentEncodingInput": "PUT_WITH_CONTENT_ENCODING_INPUT",
    "SimpleScalarPropertiesInputOutput": "SIMPLE_SCALAR_PROPERTIES_INPUT_OUTPUT",
    "SimpleStruct": "SIMPLE_STRUCT",
    "SparseNullsOperationInputOutput": "SPARSE_NULLS_OPERATION_INPUT_OUTPUT",
    "StructWithJsonName": "STRUCT_WITH_JSON_NAME",
    "UnionInputOutput": "UNION_INPUT_OUTPUT",
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
            "ComplexError",
            "ComplexNestedErrorData",
            "ContentTypeParametersInput",
            "ContentTypeParametersOutput",
            "DatetimeOffsetsOutput",
            "EmptyStruct",
            "ErrorWithMembers",
            "ErrorWithoutMembers",
            "FooEnum",
            "FooError",
            "FractionalSecondsOutput",
            "GreetingStruct",
            "GreetingWithErrorsOutput",
            "HostLabelInput",
            "IntegerEnum",
            "InvalidGreeting",
            "JsonEnumsInputOutput",
            "JsonIntEnumsInputOutput",
            "KitchenSink",
            "MyUnion",
            "NullOperationInputOutput",
            "OperationWithOptionalInputOutputInput",
            "OperationWithOptionalInputOutputOutput",
            "PutAndGetInlineDocumentsInputOutput",
            "PutWithContentEncodingInput",
            "SimpleScalarPropertiesInputOutput",
            "SimpleStruct",
            "SparseNullsOperationInputOutput",
            "StructWithJsonName",
            "UnionInputOutput",
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
