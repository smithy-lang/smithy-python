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
    "CustomCodeError": "CUSTOM_CODE_ERROR",
    "DatetimeOffsetsOutput": "DATETIME_OFFSETS_OUTPUT",
    "EmptyInputAndEmptyOutputInput": "EMPTY_INPUT_AND_EMPTY_OUTPUT_INPUT",
    "EmptyInputAndEmptyOutputOutput": "EMPTY_INPUT_AND_EMPTY_OUTPUT_OUTPUT",
    "FlattenedXmlMapOutput": "FLATTENED_XML_MAP_OUTPUT",
    "FlattenedXmlMapWithXmlNameOutput": "FLATTENED_XML_MAP_WITH_XML_NAME_OUTPUT",
    "FlattenedXmlMapWithXmlNamespaceOutput": "FLATTENED_XML_MAP_WITH_XML_NAMESPACE_OUTPUT",
    "FractionalSecondsOutput": "FRACTIONAL_SECONDS_OUTPUT",
    "GreetingWithErrorsOutput": "GREETING_WITH_ERRORS_OUTPUT",
    "HostLabelInput": "HOST_LABEL_INPUT",
    "IgnoresWrappingXmlNameOutput": "IGNORES_WRAPPING_XML_NAME_OUTPUT",
    "InvalidGreeting": "INVALID_GREETING",
    "NestedStructWithList": "NESTED_STRUCT_WITH_LIST",
    "NestedStructWithMap": "NESTED_STRUCT_WITH_MAP",
    "NestedStructuresInput": "NESTED_STRUCTURES_INPUT",
    "NoInputAndOutputInput": "NO_INPUT_AND_OUTPUT_INPUT",
    "NoInputAndOutputOutput": "NO_INPUT_AND_OUTPUT_OUTPUT",
    "PutWithContentEncodingInput": "PUT_WITH_CONTENT_ENCODING_INPUT",
    "QueryIdempotencyTokenAutoFillInput": "QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL_INPUT",
    "QueryListsInput": "QUERY_LISTS_INPUT",
    "QueryMapsInput": "QUERY_MAPS_INPUT",
    "QueryTimestampsInput": "QUERY_TIMESTAMPS_INPUT",
    "RecursiveXmlShapesOutput": "RECURSIVE_XML_SHAPES_OUTPUT",
    "RecursiveXmlShapesOutputNested1": "RECURSIVE_XML_SHAPES_OUTPUT_NESTED1",
    "RecursiveXmlShapesOutputNested2": "RECURSIVE_XML_SHAPES_OUTPUT_NESTED2",
    "SimpleInputParamsInput": "SIMPLE_INPUT_PARAMS_INPUT",
    "SimpleScalarXmlPropertiesOutput": "SIMPLE_SCALAR_XML_PROPERTIES_OUTPUT",
    "StructArg": "STRUCT_ARG",
    "StructureListMember": "STRUCTURE_LIST_MEMBER",
    "XmlBlobsOutput": "XML_BLOBS_OUTPUT",
    "XmlEnumsOutput": "XML_ENUMS_OUTPUT",
    "XmlIntEnumsOutput": "XML_INT_ENUMS_OUTPUT",
    "XmlListsOutput": "XML_LISTS_OUTPUT",
    "XmlMapsOutput": "XML_MAPS_OUTPUT",
    "XmlMapsXmlNameOutput": "XML_MAPS_XML_NAME_OUTPUT",
    "XmlNamespaceNested": "XML_NAMESPACE_NESTED",
    "XmlNamespacesOutput": "XML_NAMESPACES_OUTPUT",
    "XmlTimestampsOutput": "XML_TIMESTAMPS_OUTPUT",
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
            "CustomCodeError",
            "DatetimeOffsetsOutput",
            "EmptyInputAndEmptyOutputInput",
            "EmptyInputAndEmptyOutputOutput",
            "FlattenedXmlMapOutput",
            "FlattenedXmlMapWithXmlNameOutput",
            "FlattenedXmlMapWithXmlNamespaceOutput",
            "FooEnum",
            "FractionalSecondsOutput",
            "GreetingStruct",
            "GreetingWithErrorsOutput",
            "HostLabelInput",
            "IgnoresWrappingXmlNameOutput",
            "IntegerEnum",
            "InvalidGreeting",
            "NestedStructWithList",
            "NestedStructWithMap",
            "NestedStructuresInput",
            "NoInputAndOutputInput",
            "NoInputAndOutputOutput",
            "PutWithContentEncodingInput",
            "QueryIdempotencyTokenAutoFillInput",
            "QueryListsInput",
            "QueryMapsInput",
            "QueryTimestampsInput",
            "RecursiveXmlShapesOutput",
            "RecursiveXmlShapesOutputNested1",
            "RecursiveXmlShapesOutputNested2",
            "SimpleInputParamsInput",
            "SimpleScalarXmlPropertiesOutput",
            "StructArg",
            "StructureListMember",
            "XmlBlobsOutput",
            "XmlEnumsOutput",
            "XmlIntEnumsOutput",
            "XmlListsOutput",
            "XmlMapsOutput",
            "XmlMapsXmlNameOutput",
            "XmlNamespaceNested",
            "XmlNamespacesOutput",
            "XmlTimestampsOutput",
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
