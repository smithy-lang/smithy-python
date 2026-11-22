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
    "InvalidGreeting": "INVALID_GREETING",
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
    "OperationWithOptionalInputOutputInput": "OPERATION_WITH_OPTIONAL_INPUT_OUTPUT_INPUT",
    "OperationWithOptionalInputOutputOutput": "OPERATION_WITH_OPTIONAL_INPUT_OUTPUT_OUTPUT",
    "PutWithContentEncodingInput": "PUT_WITH_CONTENT_ENCODING_INPUT",
    "SimpleStruct": "SIMPLE_STRUCT",
    "StructWithJsonName": "STRUCT_WITH_JSON_NAME",
    "FooEnum": "FOO_ENUM",
    "GreetingStruct": "GREETING_STRUCT",
    "IntegerEnum": "INTEGER_ENUM",
    "DatetimeOffsetsInput": "DATETIME_OFFSETS_INPUT",
    "EmptyOperationInput": "EMPTY_OPERATION_INPUT",
    "EmptyOperationOutput": "EMPTY_OPERATION_OUTPUT",
    "EndpointOperationInput": "ENDPOINT_OPERATION_INPUT",
    "EndpointOperationOutput": "ENDPOINT_OPERATION_OUTPUT",
    "EndpointWithHostLabelOperationInput": "ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT",
    "EndpointWithHostLabelOperationOutput": "ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT",
    "FractionalSecondsInput": "FRACTIONAL_SECONDS_INPUT",
    "GreetingWithErrorsInput": "GREETING_WITH_ERRORS_INPUT",
    "HostWithPathOperationInput": "HOST_WITH_PATH_OPERATION_INPUT",
    "HostWithPathOperationOutput": "HOST_WITH_PATH_OPERATION_OUTPUT",
    "JsonEnumsInput": "JSON_ENUMS_INPUT",
    "JsonEnumsOutput": "JSON_ENUMS_OUTPUT",
    "JsonIntEnumsInput": "JSON_INT_ENUMS_INPUT",
    "JsonIntEnumsOutput": "JSON_INT_ENUMS_OUTPUT",
    "JsonUnionsInput": "JSON_UNIONS_INPUT",
    "JsonUnionsOutput": "JSON_UNIONS_OUTPUT",
    "KitchenSinkOperationInput": "KITCHEN_SINK_OPERATION_INPUT",
    "KitchenSinkOperationOutput": "KITCHEN_SINK_OPERATION_OUTPUT",
    "NullOperationInput": "NULL_OPERATION_INPUT",
    "NullOperationOutput": "NULL_OPERATION_OUTPUT",
    "PutAndGetInlineDocumentsInput": "PUT_AND_GET_INLINE_DOCUMENTS_INPUT",
    "PutAndGetInlineDocumentsOutput": "PUT_AND_GET_INLINE_DOCUMENTS_OUTPUT",
    "PutWithContentEncodingOutput": "PUT_WITH_CONTENT_ENCODING_OUTPUT",
    "SimpleScalarPropertiesInput": "SIMPLE_SCALAR_PROPERTIES_INPUT",
    "SimpleScalarPropertiesOutput": "SIMPLE_SCALAR_PROPERTIES_OUTPUT",
    "SparseNullsOperationInput": "SPARSE_NULLS_OPERATION_INPUT",
    "SparseNullsOperationOutput": "SPARSE_NULLS_OPERATION_OUTPUT",
}

_RENAMES: dict[str, str] = {}

_TARGET_NAMES: dict[str, str] = {}

_OPERATIONS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "CONTENT_TYPE_PARAMETERS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "DATETIME_OFFSETS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "EMPTY_OPERATION": (
        (),
        ("aws.auth#sigv4",),
    ),
    "ENDPOINT_OPERATION": (
        (),
        ("aws.auth#sigv4",),
    ),
    "ENDPOINT_WITH_HOST_LABEL_OPERATION": (
        (),
        ("aws.auth#sigv4",),
    ),
    "FRACTIONAL_SECONDS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "GREETING_WITH_ERRORS": (
        (
            "aws.protocoltests.json#ComplexError",
            "aws.protocoltests.json#FooError",
            "aws.protocoltests.json#InvalidGreeting",
        ),
        ("aws.auth#sigv4",),
    ),
    "HOST_WITH_PATH_OPERATION": (
        (),
        ("aws.auth#sigv4",),
    ),
    "JSON_ENUMS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "JSON_INT_ENUMS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "JSON_UNIONS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "KITCHEN_SINK_OPERATION": (
        (
            "aws.protocoltests.json#ErrorWithMembers",
            "aws.protocoltests.json#ErrorWithoutMembers",
        ),
        ("aws.auth#sigv4",),
    ),
    "NULL_OPERATION": (
        (),
        ("aws.auth#sigv4",),
    ),
    "OPERATION_WITH_OPTIONAL_INPUT_OUTPUT": (
        (),
        ("aws.auth#sigv4",),
    ),
    "PUT_AND_GET_INLINE_DOCUMENTS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "PUT_WITH_CONTENT_ENCODING": (
        (),
        ("aws.auth#sigv4",),
    ),
    "SIMPLE_SCALAR_PROPERTIES": (
        (),
        ("aws.auth#sigv4",),
    ),
    "SPARSE_NULLS_OPERATION": (
        (),
        ("aws.auth#sigv4",),
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
            "ComplexError",
            "ComplexNestedErrorData",
            "ContentTypeParametersInput",
            "ContentTypeParametersOutput",
            "DatetimeOffsetsInput",
            "DatetimeOffsetsOutput",
            "EmptyOperationInput",
            "EmptyOperationOutput",
            "EmptyStruct",
            "EndpointOperationInput",
            "EndpointOperationOutput",
            "EndpointWithHostLabelOperationInput",
            "EndpointWithHostLabelOperationOutput",
            "ErrorWithMembers",
            "ErrorWithoutMembers",
            "FooEnum",
            "FooError",
            "FractionalSecondsInput",
            "FractionalSecondsOutput",
            "GreetingStruct",
            "GreetingWithErrorsInput",
            "GreetingWithErrorsOutput",
            "HostWithPathOperationInput",
            "HostWithPathOperationOutput",
            "IntegerEnum",
            "InvalidGreeting",
            "JsonEnumsInput",
            "JsonEnumsOutput",
            "JsonIntEnumsInput",
            "JsonIntEnumsOutput",
            "JsonUnionsInput",
            "JsonUnionsOutput",
            "KitchenSink",
            "KitchenSinkOperationInput",
            "KitchenSinkOperationOutput",
            "MyUnion",
            "NullOperationInput",
            "NullOperationOutput",
            "OperationWithOptionalInputOutputInput",
            "OperationWithOptionalInputOutputOutput",
            "PutAndGetInlineDocumentsInput",
            "PutAndGetInlineDocumentsOutput",
            "PutWithContentEncodingInput",
            "PutWithContentEncodingOutput",
            "SimpleScalarPropertiesInput",
            "SimpleScalarPropertiesOutput",
            "SimpleStruct",
            "SparseNullsOperationInput",
            "SparseNullsOperationOutput",
            "StructWithJsonName",
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
