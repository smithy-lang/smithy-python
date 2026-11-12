from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Self

from smithy_core.aio.interfaces import StreamingBlob
from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import Document
from smithy_core.exceptions import ModeledError
from smithy_core.response import ResponseMetadata
from smithy_core.serializers import ShapeSerializer
from smithy_core.types import UnknownEnumMixin

__all__ = [
    "AllQueryStringTypesInput",
    "BlobPayloadEvent",
    "ClientOptionalDefaults",
    "ComplexError",
    "ComplexNestedErrorData",
    "ConstantAndVariableQueryStringInput",
    "ConstantQueryStringInput",
    "ContentTypeParametersInput",
    "ContentTypeParametersOutput",
    "DatetimeOffsetsOutput",
    "Defaults",
    "Dialog",
    "DocumentTypeAsMapValueInputOutput",
    "DocumentTypeAsPayloadInputOutput",
    "DocumentTypeInputOutput",
    "DuplexStreamInput",
    "DuplexStreamOutput",
    "DuplexStreamWithDistinctStreamsInput",
    "DuplexStreamWithDistinctStreamsOutput",
    "DuplexStreamWithInitialMessagesInput",
    "DuplexStreamWithInitialMessagesOutput",
    "EmptyInputAndEmptyOutputInput",
    "EmptyInputAndEmptyOutputOutput",
    "EnumPayloadInput",
    "ErrorEvent",
    "EventStream",
    "EventStreamBlobPayload",
    "EventStreamError",
    "EventStreamHeaders",
    "EventStreamHeadersAndExplicitPayload",
    "EventStreamHeadersAndImplicitPayload",
    "EventStreamStringPayload",
    "EventStreamStructurePayload",
    "EventStreamUnionPayload",
    "EventStreamUnknown",
    "Farewell",
    "FooEnum",
    "FooError",
    "FractionalSecondsOutput",
    "GreetingStruct",
    "GreetingWithErrorsOutput",
    "HeadersAndExplicitPayloadEvent",
    "HeadersAndImplicitPayloadEvent",
    "HeadersEvent",
    "HostLabelInput",
    "HttpChecksumRequiredInputOutput",
    "HttpEmptyPrefixHeadersInput",
    "HttpEmptyPrefixHeadersOutput",
    "HttpPayloadTraitsInputOutput",
    "HttpPayloadTraitsWithMediaTypeInputOutput",
    "HttpPayloadWithStructureInputOutput",
    "HttpPayloadWithUnionInputOutput",
    "HttpPrefixHeadersInResponseInput",
    "HttpPrefixHeadersInResponseOutput",
    "HttpPrefixHeadersInput",
    "HttpPrefixHeadersOutput",
    "HttpQueryParamsOnlyInput",
    "HttpRequestWithFloatLabelsInput",
    "HttpRequestWithGreedyLabelInPathInput",
    "HttpRequestWithLabelsAndTimestampFormatInput",
    "HttpRequestWithLabelsInput",
    "HttpRequestWithRegexLiteralInput",
    "HttpResponseCodeOutput",
    "IgnoreQueryParamsInResponseOutput",
    "InputAndOutputWithHeadersIO",
    "InputStreamInput",
    "InputStreamWithInitialRequestInput",
    "IntegerEnum",
    "InvalidGreeting",
    "JsonBlobsInputOutput",
    "JsonEnumsInputOutput",
    "JsonIntEnumsInputOutput",
    "JsonListsInputOutput",
    "JsonMapsInputOutput",
    "JsonTimestampsInputOutput",
    "MalformedAcceptWithGenericStringOutput",
    "MalformedAcceptWithPayloadOutput",
    "MalformedBlobInput",
    "MalformedBooleanInput",
    "MalformedByteInput",
    "MalformedContentTypeWithGenericStringInput",
    "MalformedContentTypeWithPayloadInput",
    "MalformedContentTypeWithoutBodyEmptyInputInput",
    "MalformedDoubleInput",
    "MalformedFloatInput",
    "MalformedIntegerInput",
    "MalformedListInput",
    "MalformedLongInput",
    "MalformedMapInput",
    "MalformedRequestBodyInput",
    "MalformedShortInput",
    "MalformedStringInput",
    "MalformedTimestampBodyDateTimeInput",
    "MalformedTimestampBodyDefaultInput",
    "MalformedTimestampBodyHttpDateInput",
    "MalformedTimestampHeaderDateTimeInput",
    "MalformedTimestampHeaderDefaultInput",
    "MalformedTimestampHeaderEpochInput",
    "MalformedTimestampPathDefaultInput",
    "MalformedTimestampPathEpochInput",
    "MalformedTimestampPathHttpDateInput",
    "MalformedTimestampQueryDefaultInput",
    "MalformedTimestampQueryEpochInput",
    "MalformedTimestampQueryHttpDateInput",
    "MalformedUnionInput",
    "MediaTypeHeaderInput",
    "MediaTypeHeaderOutput",
    "MyUnion",
    "MyUnionBlobValue",
    "MyUnionBooleanValue",
    "MyUnionEnumValue",
    "MyUnionListValue",
    "MyUnionMapValue",
    "MyUnionNumberValue",
    "MyUnionRenamedStructureValue",
    "MyUnionStringValue",
    "MyUnionStructureValue",
    "MyUnionTimestampValue",
    "MyUnionUnionValue",
    "MyUnionUnknown",
    "NestedPayload",
    "NestedUnion",
    "NestedUnionStringValue",
    "NestedUnionUnknown",
    "NoInputAndOutputOutput",
    "NullAndEmptyHeadersIO",
    "OmitsNullSerializesEmptyStringInput",
    "OmitsSerializingEmptyListsInput",
    "OperationWithDefaultsInput",
    "OperationWithDefaultsOutput",
    "OperationWithNestedStructureInput",
    "OperationWithNestedStructureOutput",
    "OutputStreamOutput",
    "OutputStreamWithInitialResponseOutput",
    "PayloadConfig",
    "PayloadStructure",
    "PayloadUnion",
    "PayloadUnionUnionMember",
    "PayloadUnionUnknown",
    "PlayerAction",
    "PlayerActionQuit",
    "PlayerActionUnknown",
    "PostPlayerActionInput",
    "PostPlayerActionOutput",
    "PostUnionWithJsonNameInput",
    "PostUnionWithJsonNameOutput",
    "PutWithContentEncodingInput",
    "QueryIdempotencyTokenAutoFillInput",
    "QueryParamsAsStringListMapInput",
    "QueryPrecedenceInput",
    "RecursiveShapesInputOutput",
    "RecursiveShapesInputOutputNested1",
    "RecursiveShapesInputOutputNested2",
    "RenamedGreeting",
    "ResponseCodeHttpFallbackInputOutput",
    "ResponseCodeRequiredOutput",
    "ServiceError",
    "ServiceUnavailableError",
    "SimpleScalarPropertiesInputOutput",
    "SimpleUnion",
    "SimpleUnionInt",
    "SimpleUnionString",
    "SimpleUnionUnknown",
    "SingletonEvent",
    "SingletonEventStream",
    "SingletonEventStreamSingleton",
    "SingletonEventStreamUnknown",
    "SparseJsonListsInputOutput",
    "SparseJsonMapsInputOutput",
    "StreamingTraitsInputOutput",
    "StreamingTraitsRequireLengthInput",
    "StreamingTraitsWithMediaTypeInputOutput",
    "StringEnum",
    "StringPayloadEvent",
    "StringPayloadInput",
    "StructureListMember",
    "StructurePayloadEvent",
    "TestBodyStructureInputOutput",
    "TestConfig",
    "TestEnum",
    "TestIntEnum",
    "TestNoPayloadInputOutput",
    "TestPayloadBlobInputOutput",
    "TestPayloadStructureInputOutput",
    "TimestampFormatHeadersIO",
    "TopLevel",
    "UnionInputOutput",
    "UnionPayload",
    "UnionPayloadEvent",
    "UnionPayloadGreeting",
    "UnionPayloadUnknown",
    "UnionWithJsonName",
    "UnionWithJsonNameBar",
    "UnionWithJsonNameBaz",
    "UnionWithJsonNameFoo",
    "UnionWithJsonNameUnknown",
    "Unit",
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
    query_params_map_of_string_list: dict[str, list[str]] | None = ...

@dataclass(kw_only=True)
class BlobPayloadEvent(_SerdeShape):
    "Dataclass for BlobPayloadEvent structure."

    payload: bytes | None = ...

@dataclass(kw_only=True)
class ClientOptionalDefaults(_SerdeShape):
    "Dataclass for ClientOptionalDefaults structure."

    member: int | None = ...

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
class Defaults(_SerdeShape):
    "Dataclass for Defaults structure."

    default_string: str | None = ...
    default_boolean: bool | None = ...
    default_list: list[str] | None = ...
    default_document_map: Document | None = ...
    default_document_string: Document | None = ...
    default_document_boolean: Document | None = ...
    default_document_list: Document | None = ...
    default_null_document: Document | None = ...
    default_timestamp: datetime | None = ...
    default_blob: bytes | None = ...
    default_byte: int | None = ...
    default_short: int | None = ...
    default_integer: int | None = ...
    default_long: int | None = ...
    default_float: float | None = ...
    default_double: float | None = ...
    default_map: dict[str, str] | None = ...
    default_enum: str | None = ...
    default_int_enum: int | None = ...
    empty_string: str | None = ...
    false_boolean: bool | None = ...
    empty_blob: bytes | None = ...
    zero_byte: int | None = ...
    zero_short: int | None = ...
    zero_integer: int | None = ...
    zero_long: int | None = ...
    zero_float: float | None = ...
    zero_double: float | None = ...

@dataclass(kw_only=True)
class Dialog(_SerdeShape):
    "Dataclass for Dialog structure."

    language: str | None = ...
    greeting: str | None = ...
    farewell: Farewell | None = ...

@dataclass(kw_only=True)
class DocumentTypeAsMapValueInputOutput(_SerdeShape):
    "Dataclass for DocumentTypeAsMapValueInputOutput structure."

    doc_valued_map: dict[str, Document] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class DocumentTypeAsPayloadInputOutput(_SerdeShape):
    "Dataclass for DocumentTypeAsPayloadInputOutput structure."

    document_value: Document | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class DocumentTypeInputOutput(_SerdeShape):
    "Dataclass for DocumentTypeInputOutput structure."

    string_value: str | None = ...
    document_value: Document | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class DuplexStreamInput(_SerdeShape):
    "Dataclass for DuplexStreamInput structure."

@dataclass(kw_only=True)
class DuplexStreamOutput(_SerdeShape):
    "Dataclass for DuplexStreamOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class DuplexStreamWithDistinctStreamsInput(_SerdeShape):
    "Dataclass for DuplexStreamWithDistinctStreamsInput structure."

@dataclass(kw_only=True)
class DuplexStreamWithDistinctStreamsOutput(_SerdeShape):
    "Dataclass for DuplexStreamWithDistinctStreamsOutput structure."

    stream: SingletonEventStream | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class DuplexStreamWithInitialMessagesInput(_SerdeShape):
    "Dataclass for DuplexStreamWithInitialMessagesInput structure."

    initial_request_member: str | None = ...

@dataclass(kw_only=True)
class DuplexStreamWithInitialMessagesOutput(_SerdeShape):
    "Dataclass for DuplexStreamWithInitialMessagesOutput structure."

    initial_response_member: str
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
class ErrorEvent(ServiceError, _SerdeShape):
    "Dataclass for ErrorEvent structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass
class EventStreamHeaders(_SerdeShape):
    value: HeadersEvent

@dataclass
class EventStreamBlobPayload(_SerdeShape):
    value: BlobPayloadEvent

@dataclass
class EventStreamStringPayload(_SerdeShape):
    value: StringPayloadEvent

@dataclass
class EventStreamStructurePayload(_SerdeShape):
    value: StructurePayloadEvent

@dataclass
class EventStreamUnionPayload(_SerdeShape):
    value: UnionPayloadEvent

@dataclass
class EventStreamHeadersAndExplicitPayload(_SerdeShape):
    value: HeadersAndExplicitPayloadEvent

@dataclass
class EventStreamHeadersAndImplicitPayload(_SerdeShape):
    value: HeadersAndImplicitPayloadEvent

@dataclass
class EventStreamError(_SerdeShape):
    value: ErrorEvent

@dataclass
class EventStreamUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

EventStream = (
    EventStreamHeaders
    | EventStreamBlobPayload
    | EventStreamStringPayload
    | EventStreamStructurePayload
    | EventStreamUnionPayload
    | EventStreamHeadersAndExplicitPayload
    | EventStreamHeadersAndImplicitPayload
    | EventStreamError
    | EventStreamUnknown
)

class _EventStreamDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> EventStream: ...

@dataclass(kw_only=True)
class Farewell(_SerdeShape):
    "Dataclass for Farewell structure."

    phrase: str | None = ...

@dataclass(kw_only=True)
class FooError(ServiceError, _SerdeShape):
    """
    This error has test cases that test some of the dark corners of Amazon
    service
    framework history. It should only be implemented by clients.
    """

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
class HeadersAndExplicitPayloadEvent(_SerdeShape):
    "Dataclass for HeadersAndExplicitPayloadEvent structure."

    header: str | None = ...
    payload: PayloadStructure | None = ...

@dataclass(kw_only=True)
class HeadersAndImplicitPayloadEvent(_SerdeShape):
    "Dataclass for HeadersAndImplicitPayloadEvent structure."

    header: str | None = ...
    payload: str | None = ...

@dataclass(kw_only=True)
class HeadersEvent(_SerdeShape):
    "Dataclass for HeadersEvent structure."

    boolean_header: bool | None = ...
    byte_header: int | None = ...
    short_header: int | None = ...
    int_header: int | None = ...
    long_header: int | None = ...
    blob_header: bytes | None = ...
    string_header: str | None = ...
    timestamp_header: datetime | None = ...

@dataclass(kw_only=True)
class HostLabelInput(_SerdeShape):
    "Dataclass for HostLabelInput structure."

    label: str | None = ...

@dataclass(kw_only=True)
class HttpChecksumRequiredInputOutput(_SerdeShape):
    "Dataclass for HttpChecksumRequiredInputOutput structure."

    foo: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

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
class HttpPrefixHeadersInResponseInput(_SerdeShape):
    "Dataclass for HttpPrefixHeadersInResponseInput structure."

@dataclass(kw_only=True)
class HttpPrefixHeadersInResponseOutput(_SerdeShape):
    "Dataclass for HttpPrefixHeadersInResponseOutput structure."

    prefix_headers: dict[str, str] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPrefixHeadersInput(_SerdeShape):
    "Dataclass for HttpPrefixHeadersInput structure."

    foo: str | None = ...
    foo_map: dict[str, str] | None = ...

@dataclass(kw_only=True)
class HttpPrefixHeadersOutput(_SerdeShape):
    "Dataclass for HttpPrefixHeadersOutput structure."

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
class HttpQueryParamsOnlyInput(_SerdeShape):
    "Dataclass for HttpQueryParamsOnlyInput structure."

    query_map: dict[str, str] | None = ...

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
class HttpRequestWithRegexLiteralInput(_SerdeShape):
    "Dataclass for HttpRequestWithRegexLiteralInput structure."

    str_: str | None = ...

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
    header_integer_enum: int | None = ...
    header_integer_enum_list: list[int] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class InputStreamInput(_SerdeShape):
    "Dataclass for InputStreamInput structure."

@dataclass(kw_only=True)
class InputStreamWithInitialRequestInput(_SerdeShape):
    "Dataclass for InputStreamWithInitialRequestInput structure."

    initial_request_member: str | None = ...

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
class JsonBlobsInputOutput(_SerdeShape):
    "Dataclass for JsonBlobsInputOutput structure."

    data: bytes | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class JsonEnumsInputOutput(_SerdeShape):
    "Dataclass for JsonEnumsInputOutput structure."

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
class JsonIntEnumsInputOutput(_SerdeShape):
    "Dataclass for JsonIntEnumsInputOutput structure."

    integer_enum1: int | None = ...
    integer_enum2: int | None = ...
    integer_enum3: int | None = ...
    integer_enum_list: list[int] | None = ...
    integer_enum_set: list[int] | None = ...
    integer_enum_map: dict[str, int] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class JsonListsInputOutput(_SerdeShape):
    "Dataclass for JsonListsInputOutput structure."

    string_list: list[str] | None = ...
    string_set: list[str] | None = ...
    integer_list: list[int] | None = ...
    boolean_list: list[bool] | None = ...
    timestamp_list: list[datetime] | None = ...
    enum_list: list[str] | None = ...
    int_enum_list: list[int] | None = ...
    nested_string_list: list[list[str]] | None = ...
    structure_list: list[StructureListMember] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class JsonMapsInputOutput(_SerdeShape):
    "Dataclass for JsonMapsInputOutput structure."

    dense_struct_map: dict[str, GreetingStruct] | None = ...
    dense_number_map: dict[str, int] | None = ...
    dense_boolean_map: dict[str, bool] | None = ...
    dense_string_map: dict[str, str] | None = ...
    dense_set_map: dict[str, list[str]] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class JsonTimestampsInputOutput(_SerdeShape):
    "Dataclass for JsonTimestampsInputOutput structure."

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

@dataclass(kw_only=True)
class MalformedAcceptWithGenericStringOutput(_SerdeShape):
    "Dataclass for MalformedAcceptWithGenericStringOutput structure."

    payload: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedAcceptWithPayloadOutput(_SerdeShape):
    "Dataclass for MalformedAcceptWithPayloadOutput structure."

    payload: bytes | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedBlobInput(_SerdeShape):
    "Dataclass for MalformedBlobInput structure."

    blob: bytes | None = ...

@dataclass(kw_only=True)
class MalformedBooleanInput(_SerdeShape):
    "Dataclass for MalformedBooleanInput structure."

    boolean_in_body: bool | None = ...
    boolean_in_path: bool | None = ...
    boolean_in_query: bool | None = ...
    boolean_in_header: bool | None = ...

@dataclass(kw_only=True)
class MalformedByteInput(_SerdeShape):
    "Dataclass for MalformedByteInput structure."

    byte_in_body: int | None = ...
    byte_in_path: int | None = ...
    byte_in_query: int | None = ...
    byte_in_header: int | None = ...

@dataclass(kw_only=True)
class MalformedContentTypeWithGenericStringInput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithGenericStringInput structure."

    payload: str | None = ...

@dataclass(kw_only=True)
class MalformedContentTypeWithPayloadInput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithPayloadInput structure."

    payload: bytes | None = ...

@dataclass(kw_only=True)
class MalformedContentTypeWithoutBodyEmptyInputInput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithoutBodyEmptyInputInput structure."

    header: str | None = ...

@dataclass(kw_only=True)
class MalformedDoubleInput(_SerdeShape):
    "Dataclass for MalformedDoubleInput structure."

    double_in_body: float | None = ...
    double_in_path: float | None = ...
    double_in_query: float | None = ...
    double_in_header: float | None = ...

@dataclass(kw_only=True)
class MalformedFloatInput(_SerdeShape):
    "Dataclass for MalformedFloatInput structure."

    float_in_body: float | None = ...
    float_in_path: float | None = ...
    float_in_query: float | None = ...
    float_in_header: float | None = ...

@dataclass(kw_only=True)
class MalformedIntegerInput(_SerdeShape):
    "Dataclass for MalformedIntegerInput structure."

    integer_in_body: int | None = ...
    integer_in_path: int | None = ...
    integer_in_query: int | None = ...
    integer_in_header: int | None = ...

@dataclass(kw_only=True)
class MalformedListInput(_SerdeShape):
    "Dataclass for MalformedListInput structure."

    body_list: list[str] | None = ...

@dataclass(kw_only=True)
class MalformedLongInput(_SerdeShape):
    "Dataclass for MalformedLongInput structure."

    long_in_body: int | None = ...
    long_in_path: int | None = ...
    long_in_query: int | None = ...
    long_in_header: int | None = ...

@dataclass(kw_only=True)
class MalformedMapInput(_SerdeShape):
    "Dataclass for MalformedMapInput structure."

    body_map: dict[str, str] | None = ...

@dataclass(kw_only=True)
class MalformedRequestBodyInput(_SerdeShape):
    "Dataclass for MalformedRequestBodyInput structure."

    int_: int | None = ...
    float_: float | None = ...

@dataclass(kw_only=True)
class MalformedShortInput(_SerdeShape):
    "Dataclass for MalformedShortInput structure."

    short_in_body: int | None = ...
    short_in_path: int | None = ...
    short_in_query: int | None = ...
    short_in_header: int | None = ...

@dataclass(kw_only=True)
class MalformedStringInput(_SerdeShape):
    "Dataclass for MalformedStringInput structure."

    blob: str | None = ...

@dataclass(kw_only=True)
class MalformedTimestampBodyDateTimeInput(_SerdeShape):
    "Dataclass for MalformedTimestampBodyDateTimeInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedTimestampBodyDefaultInput(_SerdeShape):
    "Dataclass for MalformedTimestampBodyDefaultInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedTimestampBodyHttpDateInput(_SerdeShape):
    "Dataclass for MalformedTimestampBodyHttpDateInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedTimestampHeaderDateTimeInput(_SerdeShape):
    "Dataclass for MalformedTimestampHeaderDateTimeInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedTimestampHeaderDefaultInput(_SerdeShape):
    "Dataclass for MalformedTimestampHeaderDefaultInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedTimestampHeaderEpochInput(_SerdeShape):
    "Dataclass for MalformedTimestampHeaderEpochInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedTimestampPathDefaultInput(_SerdeShape):
    "Dataclass for MalformedTimestampPathDefaultInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedTimestampPathEpochInput(_SerdeShape):
    "Dataclass for MalformedTimestampPathEpochInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedTimestampPathHttpDateInput(_SerdeShape):
    "Dataclass for MalformedTimestampPathHttpDateInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedTimestampQueryDefaultInput(_SerdeShape):
    "Dataclass for MalformedTimestampQueryDefaultInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedTimestampQueryEpochInput(_SerdeShape):
    "Dataclass for MalformedTimestampQueryEpochInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedTimestampQueryHttpDateInput(_SerdeShape):
    "Dataclass for MalformedTimestampQueryHttpDateInput structure."

    timestamp: datetime | None = ...

@dataclass(kw_only=True)
class MalformedUnionInput(_SerdeShape):
    "Dataclass for MalformedUnionInput structure."

    union: SimpleUnion | None = ...

@dataclass(kw_only=True)
class MediaTypeHeaderInput(_SerdeShape):
    "Dataclass for MediaTypeHeaderInput structure."

    json: str | None = ...

@dataclass(kw_only=True)
class MediaTypeHeaderOutput(_SerdeShape):
    "Dataclass for MediaTypeHeaderOutput structure."

    json: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass
class MyUnionStringValue(_SerdeShape):
    value: str

@dataclass
class MyUnionBooleanValue(_SerdeShape):
    value: bool

@dataclass
class MyUnionNumberValue(_SerdeShape):
    value: int

@dataclass
class MyUnionBlobValue(_SerdeShape):
    value: bytes

@dataclass
class MyUnionTimestampValue(_SerdeShape):
    value: datetime

@dataclass
class MyUnionEnumValue(_SerdeShape):
    value: str

@dataclass
class MyUnionListValue(_SerdeShape):
    value: list[str]

@dataclass
class MyUnionMapValue(_SerdeShape):
    value: dict[str, str]

@dataclass
class MyUnionStructureValue(_SerdeShape):
    value: GreetingStruct

@dataclass
class MyUnionRenamedStructureValue(_SerdeShape):
    value: RenamedGreeting

@dataclass
class MyUnionUnionValue(_SerdeShape):
    value: NestedUnion

@dataclass
class MyUnionUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

MyUnion = (
    MyUnionStringValue
    | MyUnionBooleanValue
    | MyUnionNumberValue
    | MyUnionBlobValue
    | MyUnionTimestampValue
    | MyUnionEnumValue
    | MyUnionListValue
    | MyUnionMapValue
    | MyUnionStructureValue
    | MyUnionRenamedStructureValue
    | MyUnionUnionValue
    | MyUnionUnknown
)
"A union with a representative set of types for members."

class _MyUnionDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> MyUnion: ...

@dataclass(kw_only=True)
class NestedPayload(_SerdeShape):
    "Dataclass for NestedPayload structure."

    greeting: str | None = ...
    name: str | None = ...

@dataclass
class NestedUnionStringValue(_SerdeShape):
    value: str

@dataclass
class NestedUnionUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

NestedUnion = NestedUnionStringValue | NestedUnionUnknown
"A union used to test unions nested inside unions."

class _NestedUnionDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> NestedUnion: ...

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
class OmitsSerializingEmptyListsInput(_SerdeShape):
    "Dataclass for OmitsSerializingEmptyListsInput structure."

    query_string_list: list[str] | None = ...
    query_integer_list: list[int] | None = ...
    query_double_list: list[float] | None = ...
    query_boolean_list: list[bool] | None = ...
    query_timestamp_list: list[datetime] | None = ...
    query_enum_list: list[str] | None = ...
    query_integer_enum_list: list[int] | None = ...

@dataclass(kw_only=True)
class OperationWithDefaultsInput(_SerdeShape):
    "Dataclass for OperationWithDefaultsInput structure."

    defaults: Defaults | None = ...
    client_optional_defaults: ClientOptionalDefaults | None = ...
    top_level_default: str | None = ...
    other_top_level_default: int | None = ...

@dataclass(kw_only=True)
class OperationWithDefaultsOutput(_SerdeShape):
    "Dataclass for OperationWithDefaultsOutput structure."

    default_string: str | None = ...
    default_boolean: bool | None = ...
    default_list: list[str] | None = ...
    default_document_map: Document | None = ...
    default_document_string: Document | None = ...
    default_document_boolean: Document | None = ...
    default_document_list: Document | None = ...
    default_null_document: Document | None = ...
    default_timestamp: datetime | None = ...
    default_blob: bytes | None = ...
    default_byte: int | None = ...
    default_short: int | None = ...
    default_integer: int | None = ...
    default_long: int | None = ...
    default_float: float | None = ...
    default_double: float | None = ...
    default_map: dict[str, str] | None = ...
    default_enum: str | None = ...
    default_int_enum: int | None = ...
    empty_string: str | None = ...
    false_boolean: bool | None = ...
    empty_blob: bytes | None = ...
    zero_byte: int | None = ...
    zero_short: int | None = ...
    zero_integer: int | None = ...
    zero_long: int | None = ...
    zero_float: float | None = ...
    zero_double: float | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class OperationWithNestedStructureInput(_SerdeShape):
    "Dataclass for OperationWithNestedStructureInput structure."

    top_level: TopLevel | None = ...

@dataclass(kw_only=True)
class OperationWithNestedStructureOutput(_SerdeShape):
    "Dataclass for OperationWithNestedStructureOutput structure."

    dialog: Dialog
    dialog_list: list[Dialog] | None = ...
    dialog_map: dict[str, Dialog] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class OutputStreamOutput(_SerdeShape):
    "Dataclass for OutputStreamOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class OutputStreamWithInitialResponseOutput(_SerdeShape):
    "Dataclass for OutputStreamWithInitialResponseOutput structure."

    initial_response_member: str
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class PayloadConfig(_SerdeShape):
    "Dataclass for PayloadConfig structure."

    data: int | None = ...

@dataclass(kw_only=True)
class PayloadStructure(_SerdeShape):
    "Dataclass for PayloadStructure structure."

    structure_member: str | None = ...

@dataclass
class PayloadUnionUnionMember(_SerdeShape):
    value: str

@dataclass
class PayloadUnionUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

PayloadUnion = PayloadUnionUnionMember | PayloadUnionUnknown

class _PayloadUnionDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> PayloadUnion: ...

@dataclass
class PlayerActionQuit(_SerdeShape):
    "Quit the game."

    value: Unit

@dataclass
class PlayerActionUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

PlayerAction = PlayerActionQuit | PlayerActionUnknown

class _PlayerActionDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> PlayerAction: ...

@dataclass(kw_only=True)
class PostPlayerActionInput(_SerdeShape):
    "Dataclass for PostPlayerActionInput structure."

    action: PlayerAction | None = ...

@dataclass(kw_only=True)
class PostPlayerActionOutput(_SerdeShape):
    "Dataclass for PostPlayerActionOutput structure."

    action: PlayerAction
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class PostUnionWithJsonNameInput(_SerdeShape):
    "Dataclass for PostUnionWithJsonNameInput structure."

    value: UnionWithJsonName | None = ...

@dataclass(kw_only=True)
class PostUnionWithJsonNameOutput(_SerdeShape):
    "Dataclass for PostUnionWithJsonNameOutput structure."

    value: UnionWithJsonName
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
class RecursiveShapesInputOutput(_SerdeShape):
    "Dataclass for RecursiveShapesInputOutput structure."

    nested: RecursiveShapesInputOutputNested1 | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

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
class ResponseCodeHttpFallbackInputOutput(_SerdeShape):
    "Dataclass for ResponseCodeHttpFallbackInputOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ResponseCodeRequiredOutput(_SerdeShape):
    "Dataclass for ResponseCodeRequiredOutput structure."

    response_code: int
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ServiceUnavailableError(ServiceError, _SerdeShape):
    "Dataclass for ServiceUnavailableError structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class SimpleScalarPropertiesInputOutput(_SerdeShape):
    "Dataclass for SimpleScalarPropertiesInputOutput structure."

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

@dataclass
class SimpleUnionInt(_SerdeShape):
    value: int

@dataclass
class SimpleUnionString(_SerdeShape):
    value: str

@dataclass
class SimpleUnionUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

SimpleUnion = SimpleUnionInt | SimpleUnionString | SimpleUnionUnknown

class _SimpleUnionDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> SimpleUnion: ...

@dataclass(kw_only=True)
class SingletonEvent(_SerdeShape):
    "Dataclass for SingletonEvent structure."

    value: str | None = ...

@dataclass
class SingletonEventStreamSingleton(_SerdeShape):
    value: SingletonEvent

@dataclass
class SingletonEventStreamUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

SingletonEventStream = SingletonEventStreamSingleton | SingletonEventStreamUnknown

class _SingletonEventStreamDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> SingletonEventStream: ...

@dataclass(kw_only=True)
class SparseJsonListsInputOutput(_SerdeShape):
    "Dataclass for SparseJsonListsInputOutput structure."

    sparse_string_list: list[str | None] | None = ...
    sparse_short_list: list[int | None] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class SparseJsonMapsInputOutput(_SerdeShape):
    "Dataclass for SparseJsonMapsInputOutput structure."

    sparse_struct_map: dict[str, GreetingStruct | None] | None = ...
    sparse_number_map: dict[str, int | None] | None = ...
    sparse_boolean_map: dict[str, bool | None] | None = ...
    sparse_string_map: dict[str, str | None] | None = ...
    sparse_set_map: dict[str, list[str] | None] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class StreamingTraitsInputOutput(_SerdeShape):
    "Dataclass for StreamingTraitsInputOutput structure."

    foo: str | None = ...
    blob: StreamingBlob | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class StreamingTraitsRequireLengthInput(_SerdeShape):
    "Dataclass for StreamingTraitsRequireLengthInput structure."

    foo: str | None = ...
    blob: StreamingBlob | None = ...

@dataclass(kw_only=True)
class StreamingTraitsWithMediaTypeInputOutput(_SerdeShape):
    "Dataclass for StreamingTraitsWithMediaTypeInputOutput structure."

    foo: str | None = ...
    blob: StreamingBlob | None = ...
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
class StringPayloadEvent(_SerdeShape):
    "Dataclass for StringPayloadEvent structure."

    payload: str | None = ...

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
class StructurePayloadEvent(_SerdeShape):
    "Dataclass for StructurePayloadEvent structure."

    payload: PayloadStructure | None = ...

@dataclass(kw_only=True)
class TestBodyStructureInputOutput(_SerdeShape):
    "Dataclass for TestBodyStructureInputOutput structure."

    test_id: str | None = ...
    test_config: TestConfig | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class TestConfig(_SerdeShape):
    "Dataclass for TestConfig structure."

    timeout: int | None = ...

class TestEnum(UnknownEnumMixin, StrEnum):
    FOO = "FOO"
    BAR = "BAR"
    BAZ = "BAZ"

class TestIntEnum(UnknownEnumMixin, IntEnum):
    ONE = 1
    TWO = 2

@dataclass(kw_only=True)
class TestNoPayloadInputOutput(_SerdeShape):
    "Dataclass for TestNoPayloadInputOutput structure."

    test_id: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class TestPayloadBlobInputOutput(_SerdeShape):
    "Dataclass for TestPayloadBlobInputOutput structure."

    content_type: str | None = ...
    data: bytes | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class TestPayloadStructureInputOutput(_SerdeShape):
    "Dataclass for TestPayloadStructureInputOutput structure."

    test_id: str | None = ...
    payload_config: PayloadConfig | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

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

@dataclass(kw_only=True)
class TopLevel(_SerdeShape):
    "Dataclass for TopLevel structure."

    dialog: Dialog
    dialog_list: list[Dialog] | None = ...
    dialog_map: dict[str, Dialog] | None = ...

@dataclass(kw_only=True)
class UnionInputOutput(_SerdeShape):
    "A shared structure that contains a single union member."

    contents: MyUnion | None = ...
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
class UnionPayloadEvent(_SerdeShape):
    "Dataclass for UnionPayloadEvent structure."

    payload: PayloadUnion | None = ...

@dataclass
class UnionWithJsonNameFoo(_SerdeShape):
    value: str

@dataclass
class UnionWithJsonNameBar(_SerdeShape):
    value: str

@dataclass
class UnionWithJsonNameBaz(_SerdeShape):
    value: str

@dataclass
class UnionWithJsonNameUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

UnionWithJsonName = (
    UnionWithJsonNameFoo
    | UnionWithJsonNameBar
    | UnionWithJsonNameBaz
    | UnionWithJsonNameUnknown
)

class _UnionWithJsonNameDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> UnionWithJsonName: ...

@dataclass(kw_only=True)
class RenamedGreeting(_SerdeShape):
    "Dataclass for GreetingStruct structure."

    salutation: str | None = ...

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
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

class IntegerEnum(UnknownEnumMixin, IntEnum):
    A = 1
    B = 2
    C = 3

@dataclass(kw_only=True)
class Unit(_SerdeShape):
    pass
