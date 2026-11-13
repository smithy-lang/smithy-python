from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Self

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import ModeledError
from smithy_core.response import ResponseMetadata
from smithy_core.serializers import ShapeSerializer
from smithy_core.types import UnknownEnumMixin

__all__ = [
    "ComplexError",
    "ComplexNestedErrorData",
    "DatetimeOffsetsOutput",
    "EmptyInputAndEmptyOutputInput",
    "EmptyInputAndEmptyOutputOutput",
    "FooEnum",
    "FractionalSecondsOutput",
    "GreetingStruct",
    "GreetingWithErrorsOutput",
    "HostLabelInput",
    "IgnoresWrappingXmlNameOutput",
    "IntegerEnum",
    "InvalidGreeting",
    "NestedStructWithList",
    "NestedStructuresInput",
    "NoInputAndOutputOutput",
    "PutWithContentEncodingInput",
    "QueryIdempotencyTokenAutoFillInput",
    "QueryListsInput",
    "QueryTimestampsInput",
    "RecursiveXmlShapesOutput",
    "RecursiveXmlShapesOutputNested1",
    "RecursiveXmlShapesOutputNested2",
    "ServiceError",
    "SimpleInputParamsInput",
    "SimpleScalarXmlPropertiesOutput",
    "StructArg",
    "StructureListMember",
    "XmlBlobsOutput",
    "XmlEnumsOutput",
    "XmlIntEnumsOutput",
    "XmlListsOutput",
    "XmlNamespaceNested",
    "XmlNamespacesOutput",
    "XmlTimestampsOutput",
]

class _SerdeShape:
    def serialize(self, serializer: ShapeSerializer) -> None: ...
    def serialize_members(self, serializer: ShapeSerializer) -> None: ...
    @classmethod
    def deserialize(cls, deserializer: ShapeDeserializer) -> Self: ...

class ServiceError(ModeledError):
    """
    Base error for all errors in the service.

    Some exceptions do not extend from this class, including synthetic,
    implicit, and shared exception types.
    """

@dataclass(kw_only=True)
class ComplexError(ServiceError, _SerdeShape):
    "This error is thrown when a request is invalid."

    top_level: str | None = ...
    nested: ComplexNestedErrorData | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ComplexNestedErrorData(_SerdeShape):
    "Dataclass for ComplexNestedErrorData structure."

    foo: str | None = ...

@dataclass(kw_only=True)
class DatetimeOffsetsOutput(_SerdeShape):
    "Dataclass for DatetimeOffsetsOutput structure."

    datetime_: datetime | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class EmptyInputAndEmptyOutputInput(_SerdeShape):
    "Dataclass for EmptyInputAndEmptyOutputInput structure."

@dataclass(kw_only=True)
class EmptyInputAndEmptyOutputOutput(_SerdeShape):
    "Dataclass for EmptyInputAndEmptyOutputOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class FractionalSecondsOutput(_SerdeShape):
    "Dataclass for FractionalSecondsOutput structure."

    datetime_: datetime | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class GreetingWithErrorsOutput(_SerdeShape):
    "Dataclass for GreetingWithErrorsOutput structure."

    greeting: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HostLabelInput(_SerdeShape):
    "Dataclass for HostLabelInput structure."

    label: str | None = ...

@dataclass(kw_only=True)
class IgnoresWrappingXmlNameOutput(_SerdeShape):
    "Dataclass for IgnoresWrappingXmlNameOutput structure."

    foo: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class InvalidGreeting(ServiceError, _SerdeShape):
    "This error is thrown when an invalid greeting value is provided."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class NestedStructWithList(_SerdeShape):
    "Dataclass for NestedStructWithList structure."

    list_arg: list[str] | None = ...

@dataclass(kw_only=True)
class NestedStructuresInput(_SerdeShape):
    "Dataclass for NestedStructuresInput structure."

    nested: StructArg | None = ...

@dataclass(kw_only=True)
class NoInputAndOutputOutput(_SerdeShape):
    "Dataclass for NoInputAndOutputOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class PutWithContentEncodingInput(_SerdeShape):
    "Dataclass for PutWithContentEncodingInput structure."

    encoding: str | None = ...
    data: str | None = ...

@dataclass(kw_only=True)
class QueryIdempotencyTokenAutoFillInput(_SerdeShape):
    "Dataclass for QueryIdempotencyTokenAutoFillInput structure."

    token: str | None = ...
    "This field is autopopulated if not provided."

@dataclass(kw_only=True)
class QueryListsInput(_SerdeShape):
    "Dataclass for QueryListsInput structure."

    list_arg: list[str] | None = ...
    complex_list_arg: list[GreetingStruct] | None = ...
    list_arg_with_xml_name_member: list[str] | None = ...
    list_arg_with_xml_name: list[str] | None = ...
    nested_with_list: NestedStructWithList | None = ...

@dataclass(kw_only=True)
class QueryTimestampsInput(_SerdeShape):
    "Dataclass for QueryTimestampsInput structure."

    normal_format: datetime | None = ...
    epoch_member: datetime | None = ...
    epoch_target: datetime | None = ...

@dataclass(kw_only=True)
class RecursiveXmlShapesOutput(_SerdeShape):
    "Dataclass for RecursiveXmlShapesOutput structure."

    nested: RecursiveXmlShapesOutputNested1 | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class RecursiveXmlShapesOutputNested1(_SerdeShape):
    "Dataclass for RecursiveXmlShapesOutputNested1 structure."

    foo: str | None = ...
    nested: RecursiveXmlShapesOutputNested2 | None = ...

@dataclass(kw_only=True)
class RecursiveXmlShapesOutputNested2(_SerdeShape):
    "Dataclass for RecursiveXmlShapesOutputNested2 structure."

    bar: str | None = ...
    recursive_member: RecursiveXmlShapesOutputNested1 | None = ...

@dataclass(kw_only=True)
class SimpleInputParamsInput(_SerdeShape):
    "Dataclass for SimpleInputParamsInput structure."

    foo: str | None = ...
    bar: str | None = ...
    baz: bool | None = ...
    bam: int | None = ...
    float_value: float | None = ...
    boo: float | None = ...
    qux: bytes | None = ...
    foo_enum: str | None = ...
    has_query_name: str | None = ...
    has_query_and_xml_name: str | None = ...
    uses_xml_name: str | None = ...
    distinct_query_name: str | None = ...
    distinct_query_and_xml_name: str | None = ...
    distinct_xml_name: str | None = ...

@dataclass(kw_only=True)
class SimpleScalarXmlPropertiesOutput(_SerdeShape):
    "Dataclass for SimpleScalarXmlPropertiesOutput structure."

    string_value: str | None = ...
    empty_string_value: str | None = ...
    true_boolean_value: bool | None = ...
    false_boolean_value: bool | None = ...
    byte_value: int | None = ...
    short_value: int | None = ...
    integer_value: int | None = ...
    long_value: int | None = ...
    float_value: float | None = ...
    double_value: float | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class StructArg(_SerdeShape):
    "Dataclass for StructArg structure."

    string_arg: str | None = ...
    other_arg: bool | None = ...
    recursive_arg: StructArg | None = ...

@dataclass(kw_only=True)
class StructureListMember(_SerdeShape):
    "Dataclass for StructureListMember structure."

    a: str | None = ...
    b: str | None = ...

@dataclass(kw_only=True)
class XmlBlobsOutput(_SerdeShape):
    "Dataclass for XmlBlobsOutput structure."

    data: bytes | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlEnumsOutput(_SerdeShape):
    "Dataclass for XmlEnumsOutput structure."

    foo_enum1: str | None = ...
    foo_enum2: str | None = ...
    foo_enum3: str | None = ...
    foo_enum_list: list[str] | None = ...
    foo_enum_set: list[str] | None = ...
    foo_enum_map: dict[str, str] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlIntEnumsOutput(_SerdeShape):
    "Dataclass for XmlIntEnumsOutput structure."

    int_enum1: int | None = ...
    int_enum2: int | None = ...
    int_enum3: int | None = ...
    int_enum_list: list[int] | None = ...
    int_enum_set: list[int] | None = ...
    int_enum_map: dict[str, int] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlListsOutput(_SerdeShape):
    "Dataclass for XmlListsOutput structure."

    string_list: list[str] | None = ...
    string_set: list[str] | None = ...
    integer_list: list[int] | None = ...
    boolean_list: list[bool] | None = ...
    timestamp_list: list[datetime] | None = ...
    enum_list: list[str] | None = ...
    int_enum_list: list[int] | None = ...
    nested_string_list: list[list[str]] | None = ...
    renamed_list_members: list[str] | None = ...
    flattened_list: list[str] | None = ...
    flattened_list2: list[str] | None = ...
    flattened_list_with_member_namespace: list[str] | None = ...
    flattened_list_with_namespace: list[str] | None = ...
    structure_list: list[StructureListMember] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlNamespaceNested(_SerdeShape):
    "Dataclass for XmlNamespaceNested structure."

    foo: str | None = ...
    values: list[str] | None = ...

@dataclass(kw_only=True)
class XmlNamespacesOutput(_SerdeShape):
    "Dataclass for XmlNamespacesOutput structure."

    nested: XmlNamespaceNested | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlTimestampsOutput(_SerdeShape):
    "Dataclass for XmlTimestampsOutput structure."

    normal: datetime | None = ...
    date_time: datetime | None = ...
    date_time_on_target: datetime | None = ...
    epoch_seconds: datetime | None = ...
    epoch_seconds_on_target: datetime | None = ...
    http_date: datetime | None = ...
    http_date_on_target: datetime | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

class FooEnum(UnknownEnumMixin, StrEnum):
    FOO = "Foo"
    BAZ = "Baz"
    BAR = "Bar"
    ONE = "1"
    ZERO = "0"

@dataclass(kw_only=True)
class GreetingStruct(_SerdeShape):
    "Dataclass for GreetingStruct structure."

    hi: str | None = ...

class IntegerEnum(UnknownEnumMixin, IntEnum):
    A = 1
    B = 2
    C = 3
