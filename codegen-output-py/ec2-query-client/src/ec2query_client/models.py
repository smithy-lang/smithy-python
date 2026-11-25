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
    "DatetimeOffsetsOutput": "DATETIME_OFFSETS_OUTPUT",
    "EmptyInputAndEmptyOutputInput": "EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT",
    "EmptyInputAndEmptyOutputOutput": "EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT",
    "FractionalSecondsOutput": "FRACTIONAL_SECONDS_OUTPUT",
    "GreetingWithErrorsOutput": "GREETING_WITH_ERRORS_OUTPUT",
    "IgnoresWrappingXmlNameOutput": "IGNORES_WRAPPING_XML_NAME_OUTPUT",
    "InvalidGreeting": "INVALID_GREETING",
    "NestedStructWithList": "NESTED_STRUCT_WITH_LIST",
    "NestedStructuresInput": "NESTED_STRUCTURES_INPUT",
    "NoInputAndOutputOutput": "NO_INPUT_AND_OUTPUT_OUTPUT",
    "PutWithContentEncodingInput": "PUT_WITH_CONTENT_ENCODING_INPUT",
    "QueryIdempotencyTokenAutoFillInput": "QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT",
    "QueryListsInput": "QUERY_LISTS_INPUT",
    "QueryTimestampsInput": "QUERY_TIMESTAMPS_INPUT",
    "RecursiveXmlShapesOutput": "RECURSIVE_XML_SHAPES_OUTPUT",
    "RecursiveXmlShapesOutputNested1": "RECURSIVE_XML_SHAPES_OUTPUT_NESTED1",
    "RecursiveXmlShapesOutputNested2": "RECURSIVE_XML_SHAPES_OUTPUT_NESTED2",
    "SimpleInputParamsInput": "SIMPLE_INPUT_PARAMS_INPUT",
    "SimpleScalarXmlPropertiesOutput": "SIMPLE_SCALAR_XML_PROPERTIES_OUTPUT",
    "StructArg": "STRUCT_ARG",
    "StructureListMember": "STRUCTURE_LIST_MEMBER",
    "XmlEnumsOutput": "XML_ENUMS_OUTPUT",
    "XmlIntEnumsOutput": "XML_INT_ENUMS_OUTPUT",
    "XmlNamespaceNested": "XML_NAMESPACE_NESTED",
    "XmlNamespacesOutput": "XML_NAMESPACES_OUTPUT",
    "XmlTimestampsOutput": "XML_TIMESTAMPS_OUTPUT",
    "FooEnum": "FOO_ENUM",
    "GreetingStruct": "GREETING_STRUCT",
    "IntegerEnum": "INTEGER_ENUM",
    "DatetimeOffsetsInput": "DATETIME_OFFSETS_INPUT",
    "EndpointOperationInput": "ENDPOINT_OPERATION_INPUT",
    "EndpointOperationOutput": "ENDPOINT_OPERATION_OUTPUT",
    "EndpointWithHostLabelOperationInput": "ENDPOINT_WITH_HOST_LABEL_OPERATION_INPUT",
    "EndpointWithHostLabelOperationOutput": "ENDPOINT_WITH_HOST_LABEL_OPERATION_OUTPUT",
    "FractionalSecondsInput": "FRACTIONAL_SECONDS_INPUT",
    "GreetingWithErrorsInput": "GREETING_WITH_ERRORS_INPUT",
    "HostWithPathOperationInput": "HOST_WITH_PATH_OPERATION_INPUT",
    "HostWithPathOperationOutput": "HOST_WITH_PATH_OPERATION_OUTPUT",
    "IgnoresWrappingXmlNameInput": "IGNORES_WRAPPING_XML_NAME_INPUT",
    "NestedStructuresOutput": "NESTED_STRUCTURES_OUTPUT",
    "NoInputAndOutputInput": "NO_INPUT_AND_OUTPUT_INPUT",
    "PutWithContentEncodingOutput": "PUT_WITH_CONTENT_ENCODING_OUTPUT",
    "QueryIdempotencyTokenAutoFillOutput": "QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_OUTPUT",
    "QueryListsOutput": "QUERY_LISTS_OUTPUT",
    "QueryTimestampsOutput": "QUERY_TIMESTAMPS_OUTPUT",
    "RecursiveXmlShapesInput": "RECURSIVE_XML_SHAPES_INPUT",
    "SimpleInputParamsOutput": "SIMPLE_INPUT_PARAMS_OUTPUT",
    "SimpleScalarXmlPropertiesInput": "SIMPLE_SCALAR_XML_PROPERTIES_INPUT",
    "XmlBlobsInput": "XML_BLOBS_INPUT",
    "XmlBlobsOutput2": "XML_BLOBS_OUTPUT2",
    "XmlEmptyBlobsInput": "XML_EMPTY_BLOBS_INPUT",
    "XmlEmptyBlobsOutput": "XML_EMPTY_BLOBS_OUTPUT",
    "XmlEmptyListsInput": "XML_EMPTY_LISTS_INPUT",
    "XmlEmptyListsOutput": "XML_EMPTY_LISTS_OUTPUT",
    "XmlEnumsInput": "XML_ENUMS_INPUT",
    "XmlIntEnumsInput": "XML_INT_ENUMS_INPUT",
    "XmlListsInput": "XML_LISTS_INPUT",
    "XmlListsOutput2": "XML_LISTS_OUTPUT2",
    "XmlNamespacesInput": "XML_NAMESPACES_INPUT",
    "XmlTimestampsInput": "XML_TIMESTAMPS_INPUT",
}

_RENAMES: dict[str, str] = {}

_TARGET_NAMES: dict[str, str] = {}

_OPERATIONS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "DATETIME_OFFSETS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "EMPTY_INPUT_AND_EMPTY_OUTPUT": (
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
        ("aws.protocoltests.ec2#ComplexError", "aws.protocoltests.ec2#InvalidGreeting"),
        ("aws.auth#sigv4",),
    ),
    "HOST_WITH_PATH_OPERATION": (
        (),
        ("aws.auth#sigv4",),
    ),
    "IGNORES_WRAPPING_XML_NAME": (
        (),
        ("aws.auth#sigv4",),
    ),
    "NESTED_STRUCTURES": (
        (),
        ("aws.auth#sigv4",),
    ),
    "NO_INPUT_AND_OUTPUT": (
        (),
        ("aws.auth#sigv4",),
    ),
    "PUT_WITH_CONTENT_ENCODING": (
        (),
        ("aws.auth#sigv4",),
    ),
    "QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL": (
        (),
        ("aws.auth#sigv4",),
    ),
    "QUERY_LISTS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "QUERY_TIMESTAMPS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "RECURSIVE_XML_SHAPES": (
        (),
        ("aws.auth#sigv4",),
    ),
    "SIMPLE_INPUT_PARAMS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "SIMPLE_SCALAR_XML_PROPERTIES": (
        (),
        ("aws.auth#sigv4",),
    ),
    "XML_BLOBS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "XML_EMPTY_BLOBS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "XML_EMPTY_LISTS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "XML_ENUMS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "XML_INT_ENUMS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "XML_LISTS": (
        (),
        ("aws.auth#sigv4",),
    ),
    "XML_NAMESPACES": (
        (),
        ("aws.auth#sigv4",),
    ),
    "XML_TIMESTAMPS": (
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
            "DatetimeOffsetsInput",
            "DatetimeOffsetsOutput",
            "EmptyInputAndEmptyOutputInput",
            "EmptyInputAndEmptyOutputOutput",
            "EndpointOperationInput",
            "EndpointOperationOutput",
            "EndpointWithHostLabelOperationInput",
            "EndpointWithHostLabelOperationOutput",
            "FooEnum",
            "FractionalSecondsInput",
            "FractionalSecondsOutput",
            "GreetingStruct",
            "GreetingWithErrorsInput",
            "GreetingWithErrorsOutput",
            "HostWithPathOperationInput",
            "HostWithPathOperationOutput",
            "IgnoresWrappingXmlNameInput",
            "IgnoresWrappingXmlNameOutput",
            "IntegerEnum",
            "InvalidGreeting",
            "NestedStructWithList",
            "NestedStructuresInput",
            "NestedStructuresOutput",
            "NoInputAndOutputInput",
            "NoInputAndOutputOutput",
            "PutWithContentEncodingInput",
            "PutWithContentEncodingOutput",
            "QueryIdempotencyTokenAutoFillInput",
            "QueryIdempotencyTokenAutoFillOutput",
            "QueryListsInput",
            "QueryListsOutput",
            "QueryTimestampsInput",
            "QueryTimestampsOutput",
            "RecursiveXmlShapesInput",
            "RecursiveXmlShapesOutput",
            "RecursiveXmlShapesOutputNested1",
            "RecursiveXmlShapesOutputNested2",
            "SimpleInputParamsInput",
            "SimpleInputParamsOutput",
            "SimpleScalarXmlPropertiesInput",
            "SimpleScalarXmlPropertiesOutput",
            "StructArg",
            "StructureListMember",
            "XmlBlobsInput",
            "XmlBlobsOutput2",
            "XmlEmptyBlobsInput",
            "XmlEmptyBlobsOutput",
            "XmlEmptyListsInput",
            "XmlEmptyListsOutput",
            "XmlEnumsInput",
            "XmlEnumsOutput",
            "XmlIntEnumsInput",
            "XmlIntEnumsOutput",
            "XmlListsInput",
            "XmlListsOutput2",
            "XmlNamespaceNested",
            "XmlNamespacesInput",
            "XmlNamespacesOutput",
            "XmlTimestampsInput",
            "XmlTimestampsOutput",
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
