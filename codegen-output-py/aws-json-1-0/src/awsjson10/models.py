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
    "ClientOptionalDefaults": "CLIENT_OPTIONAL_DEFAULTS",
    "ComplexError": "COMPLEX_ERROR",
    "ComplexNestedErrorData": "COMPLEX_NESTED_ERROR_DATA",
    "ContentTypeParametersInput": "CONTENT_TYPE_PARAMETERS_INPUT",
    "ContentTypeParametersOutput": "CONTENT_TYPE_PARAMETERS_OUTPUT",
    "Defaults": "DEFAULTS",
    "Dialog": "DIALOG",
    "EmptyInputAndEmptyOutputInput": "EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT",
    "EmptyInputAndEmptyOutputOutput": "EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT",
    "EndpointWithHostLabelOperationInput": "ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT",
    "Farewell": "FAREWELL",
    "FooError": "FOO_ERROR",
    "GreetingWithErrorsInput": "GREETING_WITH_ERRORS_INPUT",
    "GreetingWithErrorsOutput": "GREETING_WITH_ERRORS_OUTPUT",
    "InvalidGreeting": "INVALID_GREETING",
    "JsonUnionsInput": "JSON_UNIONS_INPUT",
    "JsonUnionsOutput": "JSON_UNIONS_OUTPUT",
    "MyUnion": "MY_UNION",
    "MyUnionStringValue": "MY_UNION",
    "MyUnionBooleanValue": "MY_UNION",
    "MyUnionNumberValue": "MY_UNION",
    "MyUnionBlobValue": "MY_UNION",
    "MyUnionTimestampValue": "MY_UNION",
    "MyUnionEnumValue": "MY_UNION",
    "MyUnionIntEnumValue": "MY_UNION",
    "MyUnionListValue": "MY_UNION",
    "MyUnionMapValue": "MY_UNION",
    "MyUnionStructureValue": "MY_UNION",
    "MyUnionUnknown": "MY_UNION",
    "NoInputAndOutputOutput": "NO_INPUT_AND_OUTPUT_OUTPUT",
    "OperationWithDefaultsInput": "OPERATION_WITH_DEFAULTS_INPUT",
    "OperationWithDefaultsOutput": "OPERATION_WITH_DEFAULTS_OUTPUT",
    "OperationWithNestedStructureInput": "OPERATION_WITH_NESTED_STRUCTURE_INPUT",
    "OperationWithNestedStructureOutput": "OPERATION_WITH_NESTED_STRUCTURE_OUTPUT",
    "OperationWithRequiredMembersOutput": "OPERATION_WITH_REQUIRED_MEMBERS_OUTPUT",
    "OperationWithRequiredMembersWithDefaultsOutput": "OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS_OUTPUT",
    "PutWithContentEncodingInput": "PUT_WITH_CONTENT_ENCODING_INPUT",
    "RequiredEnum": "REQUIRED_ENUM",
    "RequiredIntEnum": "REQUIRED_INT_ENUM",
    "SimpleScalarPropertiesInput": "SIMPLE_SCALAR_PROPERTIES_INPUT",
    "SimpleScalarPropertiesOutput": "SIMPLE_SCALAR_PROPERTIES_OUTPUT",
    "TestEnum": "TEST_ENUM",
    "TestIntEnum": "TEST_INT_ENUM",
    "TopLevel": "TOP_LEVEL",
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
            "ContentTypeParametersInput",
            "ContentTypeParametersOutput",
            "Defaults",
            "Dialog",
            "EmptyInputAndEmptyOutputInput",
            "EmptyInputAndEmptyOutputOutput",
            "EndpointWithHostLabelOperationInput",
            "Farewell",
            "FooEnum",
            "FooError",
            "GreetingStruct",
            "GreetingWithErrorsInput",
            "GreetingWithErrorsOutput",
            "IntegerEnum",
            "InvalidGreeting",
            "JsonUnionsInput",
            "JsonUnionsOutput",
            "MyUnion",
            "NoInputAndOutputOutput",
            "OperationWithDefaultsInput",
            "OperationWithDefaultsOutput",
            "OperationWithNestedStructureInput",
            "OperationWithNestedStructureOutput",
            "OperationWithRequiredMembersOutput",
            "OperationWithRequiredMembersWithDefaultsOutput",
            "PutWithContentEncodingInput",
            "RequiredEnum",
            "RequiredIntEnum",
            "SimpleScalarPropertiesInput",
            "SimpleScalarPropertiesOutput",
            "TestEnum",
            "TestIntEnum",
            "TopLevel",
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
