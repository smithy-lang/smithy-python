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
    "AllQueryStringTypesInput",
    "BodyWithXmlNameInputOutput",
    "ComplexError",
    "ComplexNestedErrorData",
    "ConstantAndVariableQueryStringInput",
    "ConstantQueryStringInput",
    "ContentTypeParametersInput",
    "ContentTypeParametersOutput",
    "DatetimeOffsetsOutput",
    "EmptyInputAndEmptyOutputInput",
    "EmptyInputAndEmptyOutputOutput",
    "EndpointWithHostLabelOperationRequest",
    "EnumPayloadInput",
    "FlattenedXmlMapRequest",
    "FlattenedXmlMapResponse",
    "FlattenedXmlMapWithXmlNameRequest",
    "FlattenedXmlMapWithXmlNameResponse",
    "FlattenedXmlMapWithXmlNamespaceOutput",
    "FooEnum",
    "FractionalSecondsOutput",
    "GreetingStruct",
    "GreetingWithErrorsOutput",
    "HostLabelHeaderInput",
    "HttpEmptyPrefixHeadersInput",
    "HttpEmptyPrefixHeadersOutput",
    "HttpPayloadTraitsInputOutput",
    "HttpPayloadTraitsWithMediaTypeInputOutput",
    "HttpPayloadWithMemberXmlNameInputOutput",
    "HttpPayloadWithStructureInputOutput",
    "HttpPayloadWithUnionInputOutput",
    "HttpPayloadWithXmlNameInputOutput",
    "HttpPayloadWithXmlNamespaceAndPrefixInputOutput",
    "HttpPayloadWithXmlNamespaceInputOutput",
    "HttpPrefixHeadersInputOutput",
    "HttpRequestWithFloatLabelsInput",
    "HttpRequestWithGreedyLabelInPathInput",
    "HttpRequestWithLabelsAndTimestampFormatInput",
    "HttpRequestWithLabelsInput",
    "HttpResponseCodeOutput",
    "IgnoreQueryParamsInResponseOutput",
    "InputAndOutputWithHeadersIO",
    "IntegerEnum",
    "InvalidGreeting",
    "NestedPayload",
    "NestedXmlMapWithXmlNameRequest",
    "NestedXmlMapWithXmlNameResponse",
    "NestedXmlMapsRequest",
    "NestedXmlMapsResponse",
    "NoInputAndOutputOutput",
    "NullAndEmptyHeadersIO",
    "OmitsNullSerializesEmptyStringInput",
    "PayloadWithXmlName",
    "PayloadWithXmlNamespace",
    "PayloadWithXmlNamespaceAndPrefix",
    "PutWithContentEncodingInput",
    "QueryIdempotencyTokenAutoFillInput",
    "QueryParamsAsStringListMapInput",
    "QueryPrecedenceInput",
    "RecursiveShapesInputOutputNested1",
    "RecursiveShapesInputOutputNested2",
    "RecursiveShapesRequest",
    "RecursiveShapesResponse",
    "ServiceError",
    "SimpleScalarPropertiesRequest",
    "SimpleScalarPropertiesResponse",
    "StringEnum",
    "StringPayloadInput",
    "StructureListMember",
    "TimestampFormatHeadersIO",
    "UnionPayload",
    "UnionPayloadGreeting",
    "UnionPayloadUnknown",
    "XmlAttributesInMiddlePayloadRequest",
    "XmlAttributesInMiddlePayloadResponse",
    "XmlAttributesInMiddleRequest",
    "XmlAttributesInMiddleResponse",
    "XmlAttributesOnPayloadRequest",
    "XmlAttributesOnPayloadResponse",
    "XmlAttributesPayloadRequest",
    "XmlAttributesPayloadResponse",
    "XmlAttributesRequest",
    "XmlAttributesResponse",
    "XmlBlobsRequest",
    "XmlBlobsResponse",
    "XmlEmptyBlobsRequest",
    "XmlEmptyBlobsResponse",
    "XmlEmptyListsRequest",
    "XmlEmptyListsResponse",
    "XmlEmptyMapsRequest",
    "XmlEmptyMapsResponse",
    "XmlEmptyStringsRequest",
    "XmlEmptyStringsResponse",
    "XmlEnumsRequest",
    "XmlEnumsResponse",
    "XmlIntEnumsRequest",
    "XmlIntEnumsResponse",
    "XmlListsRequest",
    "XmlListsResponse",
    "XmlMapWithXmlNamespaceRequest",
    "XmlMapWithXmlNamespaceResponse",
    "XmlMapsRequest",
    "XmlMapsResponse",
    "XmlMapsXmlNameRequest",
    "XmlMapsXmlNameResponse",
    "XmlNamespaceNested",
    "XmlNamespacesRequest",
    "XmlNamespacesResponse",
    "XmlNestedUnionStruct",
    "XmlTimestampsRequest",
    "XmlTimestampsResponse",
    "XmlUnionShape",
    "XmlUnionShapeBooleanValue",
    "XmlUnionShapeByteValue",
    "XmlUnionShapeDoubleValue",
    "XmlUnionShapeFloatValue",
    "XmlUnionShapeIntegerValue",
    "XmlUnionShapeLongValue",
    "XmlUnionShapeShortValue",
    "XmlUnionShapeStringValue",
    "XmlUnionShapeStructValue",
    "XmlUnionShapeUnionValue",
    "XmlUnionShapeUnknown",
    "XmlUnionsRequest",
    "XmlUnionsResponse",
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
class AllQueryStringTypesInput(_SerdeShape):
    "Dataclass for AllQueryStringTypesInput structure."

    query_string: str | None = ...
    query_string_list: list[str] | None = ...
    query_string_set: list[str] | None = ...
    query_byte: int | None = ...
    query_short: int | None = ...
    query_integer: int | None = ...
    query_integer_list: list[int] | None = ...
    query_integer_set: list[int] | None = ...
    query_long: int | None = ...
    query_float: float | None = ...
    query_double: float | None = ...
    query_double_list: list[float] | None = ...
    query_boolean: bool | None = ...
    query_boolean_list: list[bool] | None = ...
    query_timestamp: datetime | None = ...
    query_timestamp_list: list[datetime] | None = ...
    query_enum: str | None = ...
    query_enum_list: list[str] | None = ...
    query_integer_enum: int | None = ...
    query_integer_enum_list: list[int] | None = ...
    query_params_map_of_strings: dict[str, str] | None = ...

@dataclass(kw_only=True)
class BodyWithXmlNameInputOutput(_SerdeShape):
    "Dataclass for BodyWithXmlNameInputOutput structure."

    nested: PayloadWithXmlName | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ComplexError(ServiceError, _SerdeShape):
    "This error is thrown when a request is invalid."

    header: str | None = ...
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
class ConstantAndVariableQueryStringInput(_SerdeShape):
    "Dataclass for ConstantAndVariableQueryStringInput structure."

    baz: str | None = ...
    maybe_set: str | None = ...

@dataclass(kw_only=True)
class ConstantQueryStringInput(_SerdeShape):
    "Dataclass for ConstantQueryStringInput structure."

    hello: str | None = ...

@dataclass(kw_only=True)
class ContentTypeParametersInput(_SerdeShape):
    "Dataclass for ContentTypeParametersInput structure."

    value: int | None = ...

@dataclass(kw_only=True)
class ContentTypeParametersOutput(_SerdeShape):
    "Dataclass for ContentTypeParametersOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

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
class EndpointWithHostLabelOperationRequest(_SerdeShape):
    "Dataclass for EndpointWithHostLabelOperationRequest structure."

    label: str | None = ...

@dataclass(kw_only=True)
class EnumPayloadInput(_SerdeShape):
    "Dataclass for EnumPayloadInput structure."

    payload: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class FlattenedXmlMapRequest(_SerdeShape):
    "Dataclass for FlattenedXmlMapRequest structure."

    my_map: dict[str, str] | None = ...

@dataclass(kw_only=True)
class FlattenedXmlMapResponse(_SerdeShape):
    "Dataclass for FlattenedXmlMapResponse structure."

    my_map: dict[str, str] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class FlattenedXmlMapWithXmlNameRequest(_SerdeShape):
    "Dataclass for FlattenedXmlMapWithXmlNameRequest structure."

    my_map: dict[str, str] | None = ...

@dataclass(kw_only=True)
class FlattenedXmlMapWithXmlNameResponse(_SerdeShape):
    "Dataclass for FlattenedXmlMapWithXmlNameResponse structure."

    my_map: dict[str, str] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class FlattenedXmlMapWithXmlNamespaceOutput(_SerdeShape):
    "Dataclass for FlattenedXmlMapWithXmlNamespaceOutput structure."

    my_map: dict[str, str] | None = ...
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
class HostLabelHeaderInput(_SerdeShape):
    "Dataclass for HostLabelHeaderInput structure."

    account_id: str | None = ...

@dataclass(kw_only=True)
class HttpEmptyPrefixHeadersInput(_SerdeShape):
    "Dataclass for HttpEmptyPrefixHeadersInput structure."

    prefix_headers: dict[str, str] | None = ...
    specific_header: str | None = ...

@dataclass(kw_only=True)
class HttpEmptyPrefixHeadersOutput(_SerdeShape):
    "Dataclass for HttpEmptyPrefixHeadersOutput structure."

    prefix_headers: dict[str, str] | None = ...
    specific_header: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPayloadTraitsInputOutput(_SerdeShape):
    "Dataclass for HttpPayloadTraitsInputOutput structure."

    foo: str | None = ...
    blob: bytes | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPayloadTraitsWithMediaTypeInputOutput(_SerdeShape):
    "Dataclass for HttpPayloadTraitsWithMediaTypeInputOutput structure."

    foo: str | None = ...
    blob: bytes | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPayloadWithMemberXmlNameInputOutput(_SerdeShape):
    "Dataclass for HttpPayloadWithMemberXmlNameInputOutput structure."

    nested: PayloadWithXmlName | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPayloadWithStructureInputOutput(_SerdeShape):
    "Dataclass for HttpPayloadWithStructureInputOutput structure."

    nested: NestedPayload | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPayloadWithUnionInputOutput(_SerdeShape):
    "Dataclass for HttpPayloadWithUnionInputOutput structure."

    nested: UnionPayload | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPayloadWithXmlNameInputOutput(_SerdeShape):
    "Dataclass for HttpPayloadWithXmlNameInputOutput structure."

    nested: PayloadWithXmlName | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPayloadWithXmlNamespaceAndPrefixInputOutput(_SerdeShape):
    "Dataclass for HttpPayloadWithXmlNamespaceAndPrefixInputOutput structure."

    nested: PayloadWithXmlNamespaceAndPrefix | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPayloadWithXmlNamespaceInputOutput(_SerdeShape):
    "Dataclass for HttpPayloadWithXmlNamespaceInputOutput structure."

    nested: PayloadWithXmlNamespace | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPrefixHeadersInputOutput(_SerdeShape):
    "Dataclass for HttpPrefixHeadersInputOutput structure."

    foo: str | None = ...
    foo_map: dict[str, str] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpRequestWithFloatLabelsInput(_SerdeShape):
    "Dataclass for HttpRequestWithFloatLabelsInput structure."

    float_: float | None = ...
    double: float | None = ...

@dataclass(kw_only=True)
class HttpRequestWithGreedyLabelInPathInput(_SerdeShape):
    "Dataclass for HttpRequestWithGreedyLabelInPathInput structure."

    foo: str | None = ...
    baz: str | None = ...

@dataclass(kw_only=True)
class HttpRequestWithLabelsAndTimestampFormatInput(_SerdeShape):
    "Dataclass for HttpRequestWithLabelsAndTimestampFormatInput structure."

    member_epoch_seconds: datetime | None = ...
    member_http_date: datetime | None = ...
    member_date_time: datetime | None = ...
    default_format: datetime | None = ...
    target_epoch_seconds: datetime | None = ...
    target_http_date: datetime | None = ...
    target_date_time: datetime | None = ...

@dataclass(kw_only=True)
class HttpRequestWithLabelsInput(_SerdeShape):
    "Dataclass for HttpRequestWithLabelsInput structure."

    string: str | None = ...
    short: int | None = ...
    integer: int | None = ...
    long: int | None = ...
    float_: float | None = ...
    double: float | None = ...
    boolean: bool | None = ...
    "Serialized in the path as true or false."
    timestamp: datetime | None = ...
    """
    Note that this member has no format, so it's serialized as an RFC 3399
    date-time.
    """

@dataclass(kw_only=True)
class HttpResponseCodeOutput(_SerdeShape):
    "Dataclass for HttpResponseCodeOutput structure."

    status: int | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class IgnoreQueryParamsInResponseOutput(_SerdeShape):
    "Dataclass for IgnoreQueryParamsInResponseOutput structure."

    baz: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class InputAndOutputWithHeadersIO(_SerdeShape):
    "Dataclass for InputAndOutputWithHeadersIO structure."

    header_string: str | None = ...
    header_byte: int | None = ...
    header_short: int | None = ...
    header_integer: int | None = ...
    header_long: int | None = ...
    header_float: float | None = ...
    header_double: float | None = ...
    header_true_bool: bool | None = ...
    header_false_bool: bool | None = ...
    header_string_list: list[str] | None = ...
    header_string_set: list[str] | None = ...
    header_integer_list: list[int] | None = ...
    header_boolean_list: list[bool] | None = ...
    header_timestamp_list: list[datetime] | None = ...
    header_enum: str | None = ...
    header_enum_list: list[str] | None = ...
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
class NestedPayload(_SerdeShape):
    "Dataclass for NestedPayload structure."

    greeting: str | None = ...
    name: str | None = ...

@dataclass(kw_only=True)
class NestedXmlMapWithXmlNameRequest(_SerdeShape):
    "Dataclass for NestedXmlMapWithXmlNameRequest structure."

    nested_xml_map_with_xml_name_map: dict[str, dict[str, str]] | None = ...

@dataclass(kw_only=True)
class NestedXmlMapWithXmlNameResponse(_SerdeShape):
    "Dataclass for NestedXmlMapWithXmlNameResponse structure."

    nested_xml_map_with_xml_name_map: dict[str, dict[str, str]] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class NestedXmlMapsRequest(_SerdeShape):
    "Dataclass for NestedXmlMapsRequest structure."

    nested_map: dict[str, dict[str, str]] | None = ...
    flat_nested_map: dict[str, dict[str, str]] | None = ...

@dataclass(kw_only=True)
class NestedXmlMapsResponse(_SerdeShape):
    "Dataclass for NestedXmlMapsResponse structure."

    nested_map: dict[str, dict[str, str]] | None = ...
    flat_nested_map: dict[str, dict[str, str]] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

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
class NullAndEmptyHeadersIO(_SerdeShape):
    "Dataclass for NullAndEmptyHeadersIO structure."

    a: str | None = ...
    b: str | None = ...
    c: list[str] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class OmitsNullSerializesEmptyStringInput(_SerdeShape):
    "Dataclass for OmitsNullSerializesEmptyStringInput structure."

    null_value: str | None = ...
    empty_string: str | None = ...

@dataclass(kw_only=True)
class PayloadWithXmlName(_SerdeShape):
    "Dataclass for PayloadWithXmlName structure."

    name: str | None = ...

@dataclass(kw_only=True)
class PayloadWithXmlNamespace(_SerdeShape):
    "Dataclass for PayloadWithXmlNamespace structure."

    name: str | None = ...

@dataclass(kw_only=True)
class PayloadWithXmlNamespaceAndPrefix(_SerdeShape):
    "Dataclass for PayloadWithXmlNamespaceAndPrefix structure."

    name: str | None = ...

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
class QueryParamsAsStringListMapInput(_SerdeShape):
    "Dataclass for QueryParamsAsStringListMapInput structure."

    qux: str | None = ...
    foo: dict[str, list[str]] | None = ...

@dataclass(kw_only=True)
class QueryPrecedenceInput(_SerdeShape):
    "Dataclass for QueryPrecedenceInput structure."

    foo: str | None = ...
    baz: dict[str, str] | None = ...

@dataclass(kw_only=True)
class RecursiveShapesInputOutputNested1(_SerdeShape):
    "Dataclass for RecursiveShapesInputOutputNested1 structure."

    foo: str | None = ...
    nested: RecursiveShapesInputOutputNested2 | None = ...

@dataclass(kw_only=True)
class RecursiveShapesInputOutputNested2(_SerdeShape):
    "Dataclass for RecursiveShapesInputOutputNested2 structure."

    bar: str | None = ...
    recursive_member: RecursiveShapesInputOutputNested1 | None = ...

@dataclass(kw_only=True)
class RecursiveShapesRequest(_SerdeShape):
    "Dataclass for RecursiveShapesRequest structure."

    nested: RecursiveShapesInputOutputNested1 | None = ...

@dataclass(kw_only=True)
class RecursiveShapesResponse(_SerdeShape):
    "Dataclass for RecursiveShapesResponse structure."

    nested: RecursiveShapesInputOutputNested1 | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class SimpleScalarPropertiesRequest(_SerdeShape):
    "Dataclass for SimpleScalarPropertiesRequest structure."

    foo: str | None = ...
    string_value: str | None = ...
    true_boolean_value: bool | None = ...
    false_boolean_value: bool | None = ...
    byte_value: int | None = ...
    short_value: int | None = ...
    integer_value: int | None = ...
    long_value: int | None = ...
    float_value: float | None = ...
    double_value: float | None = ...

@dataclass(kw_only=True)
class SimpleScalarPropertiesResponse(_SerdeShape):
    "Dataclass for SimpleScalarPropertiesResponse structure."

    foo: str | None = ...
    string_value: str | None = ...
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

class StringEnum(UnknownEnumMixin, StrEnum):
    V = "enumvalue"

@dataclass(kw_only=True)
class StringPayloadInput(_SerdeShape):
    "Dataclass for StringPayloadInput structure."

    payload: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class StructureListMember(_SerdeShape):
    "Dataclass for StructureListMember structure."

    a: str | None = ...
    b: str | None = ...

@dataclass(kw_only=True)
class TimestampFormatHeadersIO(_SerdeShape):
    "Dataclass for TimestampFormatHeadersIO structure."

    member_epoch_seconds: datetime | None = ...
    member_http_date: datetime | None = ...
    member_date_time: datetime | None = ...
    default_format: datetime | None = ...
    target_epoch_seconds: datetime | None = ...
    target_http_date: datetime | None = ...
    target_date_time: datetime | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass
class UnionPayloadGreeting(_SerdeShape):
    value: str

@dataclass
class UnionPayloadUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

UnionPayload = UnionPayloadGreeting | UnionPayloadUnknown

class _UnionPayloadDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> UnionPayload: ...

@dataclass(kw_only=True)
class XmlAttributesInMiddlePayloadRequest(_SerdeShape):
    "Dataclass for XmlAttributesInMiddlePayloadRequest structure."

    foo: str | None = ...
    attr: str | None = ...
    baz: str | None = ...

@dataclass(kw_only=True)
class XmlAttributesInMiddlePayloadResponse(_SerdeShape):
    "Dataclass for XmlAttributesInMiddlePayloadResponse structure."

    foo: str | None = ...
    attr: str | None = ...
    baz: str | None = ...

@dataclass(kw_only=True)
class XmlAttributesInMiddleRequest(_SerdeShape):
    "Dataclass for XmlAttributesInMiddleRequest structure."

    payload: XmlAttributesInMiddlePayloadRequest | None = ...

@dataclass(kw_only=True)
class XmlAttributesInMiddleResponse(_SerdeShape):
    "Dataclass for XmlAttributesInMiddleResponse structure."

    payload: XmlAttributesInMiddlePayloadResponse | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlAttributesOnPayloadRequest(_SerdeShape):
    "Dataclass for XmlAttributesOnPayloadRequest structure."

    payload: XmlAttributesPayloadRequest | None = ...

@dataclass(kw_only=True)
class XmlAttributesOnPayloadResponse(_SerdeShape):
    "Dataclass for XmlAttributesOnPayloadResponse structure."

    payload: XmlAttributesPayloadResponse | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlAttributesPayloadRequest(_SerdeShape):
    "Dataclass for XmlAttributesPayloadRequest structure."

    foo: str | None = ...
    attr: str | None = ...

@dataclass(kw_only=True)
class XmlAttributesPayloadResponse(_SerdeShape):
    "Dataclass for XmlAttributesPayloadResponse structure."

    foo: str | None = ...
    attr: str | None = ...

@dataclass(kw_only=True)
class XmlAttributesRequest(_SerdeShape):
    "Dataclass for XmlAttributesRequest structure."

    foo: str | None = ...
    attr: str | None = ...

@dataclass(kw_only=True)
class XmlAttributesResponse(_SerdeShape):
    "Dataclass for XmlAttributesResponse structure."

    foo: str | None = ...
    attr: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlBlobsRequest(_SerdeShape):
    "Dataclass for XmlBlobsRequest structure."

    data: bytes | None = ...

@dataclass(kw_only=True)
class XmlBlobsResponse(_SerdeShape):
    "Dataclass for XmlBlobsResponse structure."

    data: bytes | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlEmptyBlobsRequest(_SerdeShape):
    "Dataclass for XmlEmptyBlobsRequest structure."

    data: bytes | None = ...

@dataclass(kw_only=True)
class XmlEmptyBlobsResponse(_SerdeShape):
    "Dataclass for XmlEmptyBlobsResponse structure."

    data: bytes | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlEmptyListsRequest(_SerdeShape):
    "Dataclass for XmlEmptyListsRequest structure."

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
    flattened_structure_list: list[StructureListMember] | None = ...

@dataclass(kw_only=True)
class XmlEmptyListsResponse(_SerdeShape):
    "Dataclass for XmlEmptyListsResponse structure."

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
    flattened_structure_list: list[StructureListMember] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlEmptyMapsRequest(_SerdeShape):
    "Dataclass for XmlEmptyMapsRequest structure."

    my_map: dict[str, GreetingStruct] | None = ...

@dataclass(kw_only=True)
class XmlEmptyMapsResponse(_SerdeShape):
    "Dataclass for XmlEmptyMapsResponse structure."

    my_map: dict[str, GreetingStruct] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlEmptyStringsRequest(_SerdeShape):
    "Dataclass for XmlEmptyStringsRequest structure."

    empty_string: str | None = ...

@dataclass(kw_only=True)
class XmlEmptyStringsResponse(_SerdeShape):
    "Dataclass for XmlEmptyStringsResponse structure."

    empty_string: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlEnumsRequest(_SerdeShape):
    "Dataclass for XmlEnumsRequest structure."

    foo_enum1: str | None = ...
    foo_enum2: str | None = ...
    foo_enum3: str | None = ...
    foo_enum_list: list[str] | None = ...
    foo_enum_set: list[str] | None = ...
    foo_enum_map: dict[str, str] | None = ...

@dataclass(kw_only=True)
class XmlEnumsResponse(_SerdeShape):
    "Dataclass for XmlEnumsResponse structure."

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
class XmlIntEnumsRequest(_SerdeShape):
    "Dataclass for XmlIntEnumsRequest structure."

    int_enum1: int | None = ...
    int_enum2: int | None = ...
    int_enum3: int | None = ...
    int_enum_list: list[int] | None = ...
    int_enum_set: list[int] | None = ...
    int_enum_map: dict[str, int] | None = ...

@dataclass(kw_only=True)
class XmlIntEnumsResponse(_SerdeShape):
    "Dataclass for XmlIntEnumsResponse structure."

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
class XmlListsRequest(_SerdeShape):
    "Dataclass for XmlListsRequest structure."

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
    flattened_structure_list: list[StructureListMember] | None = ...

@dataclass(kw_only=True)
class XmlListsResponse(_SerdeShape):
    "Dataclass for XmlListsResponse structure."

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
    flattened_structure_list: list[StructureListMember] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlMapWithXmlNamespaceRequest(_SerdeShape):
    "Dataclass for XmlMapWithXmlNamespaceRequest structure."

    my_map: dict[str, str] | None = ...

@dataclass(kw_only=True)
class XmlMapWithXmlNamespaceResponse(_SerdeShape):
    "Dataclass for XmlMapWithXmlNamespaceResponse structure."

    my_map: dict[str, str] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlMapsRequest(_SerdeShape):
    "Dataclass for XmlMapsRequest structure."

    my_map: dict[str, GreetingStruct] | None = ...

@dataclass(kw_only=True)
class XmlMapsResponse(_SerdeShape):
    "Dataclass for XmlMapsResponse structure."

    my_map: dict[str, GreetingStruct] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlMapsXmlNameRequest(_SerdeShape):
    "Dataclass for XmlMapsXmlNameRequest structure."

    my_map: dict[str, GreetingStruct] | None = ...

@dataclass(kw_only=True)
class XmlMapsXmlNameResponse(_SerdeShape):
    "Dataclass for XmlMapsXmlNameResponse structure."

    my_map: dict[str, GreetingStruct] | None = ...
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
class XmlNamespacesRequest(_SerdeShape):
    "Dataclass for XmlNamespacesRequest structure."

    nested: XmlNamespaceNested | None = ...

@dataclass(kw_only=True)
class XmlNamespacesResponse(_SerdeShape):
    "Dataclass for XmlNamespacesResponse structure."

    nested: XmlNamespaceNested | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class XmlNestedUnionStruct(_SerdeShape):
    "Dataclass for XmlNestedUnionStruct structure."

    string_value: str | None = ...
    boolean_value: bool | None = ...
    byte_value: int | None = ...
    short_value: int | None = ...
    integer_value: int | None = ...
    long_value: int | None = ...
    float_value: float | None = ...
    double_value: float | None = ...

@dataclass(kw_only=True)
class XmlTimestampsRequest(_SerdeShape):
    "Dataclass for XmlTimestampsRequest structure."

    normal: datetime | None = ...
    date_time: datetime | None = ...
    date_time_on_target: datetime | None = ...
    epoch_seconds: datetime | None = ...
    epoch_seconds_on_target: datetime | None = ...
    http_date: datetime | None = ...
    http_date_on_target: datetime | None = ...

@dataclass(kw_only=True)
class XmlTimestampsResponse(_SerdeShape):
    "Dataclass for XmlTimestampsResponse structure."

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

@dataclass
class XmlUnionShapeStringValue(_SerdeShape):
    value: str

@dataclass
class XmlUnionShapeBooleanValue(_SerdeShape):
    value: bool

@dataclass
class XmlUnionShapeByteValue(_SerdeShape):
    value: int

@dataclass
class XmlUnionShapeShortValue(_SerdeShape):
    value: int

@dataclass
class XmlUnionShapeIntegerValue(_SerdeShape):
    value: int

@dataclass
class XmlUnionShapeLongValue(_SerdeShape):
    value: int

@dataclass
class XmlUnionShapeFloatValue(_SerdeShape):
    value: float

@dataclass
class XmlUnionShapeDoubleValue(_SerdeShape):
    value: float

@dataclass
class XmlUnionShapeUnionValue(_SerdeShape):
    value: XmlUnionShape

@dataclass
class XmlUnionShapeStructValue(_SerdeShape):
    value: XmlNestedUnionStruct

@dataclass
class XmlUnionShapeUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

XmlUnionShape = (
    XmlUnionShapeStringValue
    | XmlUnionShapeBooleanValue
    | XmlUnionShapeByteValue
    | XmlUnionShapeShortValue
    | XmlUnionShapeIntegerValue
    | XmlUnionShapeLongValue
    | XmlUnionShapeFloatValue
    | XmlUnionShapeDoubleValue
    | XmlUnionShapeUnionValue
    | XmlUnionShapeStructValue
    | XmlUnionShapeUnknown
)

class _XmlUnionShapeDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> XmlUnionShape: ...

@dataclass(kw_only=True)
class XmlUnionsRequest(_SerdeShape):
    "Dataclass for XmlUnionsRequest structure."

    union_value: XmlUnionShape | None = ...

@dataclass(kw_only=True)
class XmlUnionsResponse(_SerdeShape):
    "Dataclass for XmlUnionsResponse structure."

    union_value: XmlUnionShape | None = ...
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
