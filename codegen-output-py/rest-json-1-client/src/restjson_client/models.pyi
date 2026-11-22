from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Required, Self, TypedDict

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import Document
from smithy_core.exceptions import ModeledError
from smithy_core.response import ResponseMetadata
from smithy_core.schemas import APIOperation
from smithy_core.serializers import ShapeSerializer
from smithy_core.types import UnknownEnumMixin

__all__ = [
    "ALL_QUERY_STRING_TYPES",
    "CONSTANT_AND_VARIABLE_QUERY_STRING",
    "CONSTANT_QUERY_STRING",
    "CONTENT_TYPE_PARAMETERS",
    "DATETIME_OFFSETS",
    "DOCUMENT_TYPE",
    "DOCUMENT_TYPE_AS_MAP_VALUE",
    "DOCUMENT_TYPE_AS_PAYLOAD",
    "EMPTY_INPUT_AND_EMPTY_OUTPUT",
    "ENDPOINT_OPERATION",
    "ENDPOINT_WITH_HOST_LABEL_OPERATION",
    "FRACTIONAL_SECONDS",
    "GREETING_WITH_ERRORS",
    "HOST_WITH_PATH_OPERATION",
    "HTTP_CHECKSUM_REQUIRED",
    "HTTP_EMPTY_PREFIX_HEADERS",
    "HTTP_ENUM_PAYLOAD",
    "HTTP_PAYLOAD_TRAITS",
    "HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE",
    "HTTP_PAYLOAD_WITH_STRUCTURE",
    "HTTP_PAYLOAD_WITH_UNION",
    "HTTP_PREFIX_HEADERS",
    "HTTP_PREFIX_HEADERS_IN_RESPONSE",
    "HTTP_QUERY_PARAMS_ONLY_OPERATION",
    "HTTP_REQUEST_WITH_FLOAT_LABELS",
    "HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH",
    "HTTP_REQUEST_WITH_LABELS",
    "HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT",
    "HTTP_REQUEST_WITH_REGEX_LITERAL",
    "HTTP_RESPONSE_CODE",
    "HTTP_STRING_PAYLOAD",
    "IGNORE_QUERY_PARAMS_IN_RESPONSE",
    "INPUT_AND_OUTPUT_WITH_HEADERS",
    "JSON_BLOBS",
    "JSON_ENUMS",
    "JSON_INT_ENUMS",
    "JSON_LISTS",
    "JSON_MAPS",
    "JSON_TIMESTAMPS",
    "JSON_UNIONS",
    "MALFORMED_ACCEPT_WITH_BODY",
    "MALFORMED_ACCEPT_WITH_GENERIC_STRING",
    "MALFORMED_ACCEPT_WITH_PAYLOAD",
    "MALFORMED_BLOB",
    "MALFORMED_BOOLEAN",
    "MALFORMED_BYTE",
    "MALFORMED_CONTENT_TYPE_WITHOUT_BODY",
    "MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT",
    "MALFORMED_CONTENT_TYPE_WITH_BODY",
    "MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING",
    "MALFORMED_CONTENT_TYPE_WITH_PAYLOAD",
    "MALFORMED_DOUBLE",
    "MALFORMED_FLOAT",
    "MALFORMED_INTEGER",
    "MALFORMED_LIST",
    "MALFORMED_LONG",
    "MALFORMED_MAP",
    "MALFORMED_REQUEST_BODY",
    "MALFORMED_SHORT",
    "MALFORMED_STRING",
    "MALFORMED_TIMESTAMP_BODY_DATE_TIME",
    "MALFORMED_TIMESTAMP_BODY_DEFAULT",
    "MALFORMED_TIMESTAMP_BODY_HTTP_DATE",
    "MALFORMED_TIMESTAMP_HEADER_DATE_TIME",
    "MALFORMED_TIMESTAMP_HEADER_DEFAULT",
    "MALFORMED_TIMESTAMP_HEADER_EPOCH",
    "MALFORMED_TIMESTAMP_PATH_DEFAULT",
    "MALFORMED_TIMESTAMP_PATH_EPOCH",
    "MALFORMED_TIMESTAMP_PATH_HTTP_DATE",
    "MALFORMED_TIMESTAMP_QUERY_DEFAULT",
    "MALFORMED_TIMESTAMP_QUERY_EPOCH",
    "MALFORMED_TIMESTAMP_QUERY_HTTP_DATE",
    "MALFORMED_UNION",
    "MEDIA_TYPE_HEADER",
    "NO_INPUT_AND_NO_OUTPUT",
    "NO_INPUT_AND_OUTPUT",
    "NULL_AND_EMPTY_HEADERS_CLIENT",
    "NULL_AND_EMPTY_HEADERS_SERVER",
    "OMITS_NULL_SERIALIZES_EMPTY_STRING",
    "OMITS_SERIALIZING_EMPTY_LISTS",
    "OPERATION_WITH_DEFAULTS",
    "OPERATION_WITH_NESTED_STRUCTURE",
    "POST_PLAYER_ACTION",
    "POST_UNION_WITH_JSON_NAME",
    "PUT_WITH_CONTENT_ENCODING",
    "QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL",
    "QUERY_PARAMS_AS_STRING_LIST_MAP",
    "QUERY_PRECEDENCE",
    "RECURSIVE_SHAPES",
    "RESPONSE_CODE_HTTP_FALLBACK",
    "RESPONSE_CODE_REQUIRED",
    "SIMPLE_SCALAR_PROPERTIES",
    "SPARSE_JSON_LISTS",
    "SPARSE_JSON_MAPS",
    "TEST_BODY_STRUCTURE",
    "TEST_GET_NO_INPUT_NO_PAYLOAD",
    "TEST_GET_NO_PAYLOAD",
    "TEST_PAYLOAD_BLOB",
    "TEST_PAYLOAD_STRUCTURE",
    "TEST_POST_NO_INPUT_NO_PAYLOAD",
    "TEST_POST_NO_PAYLOAD",
    "TIMESTAMP_FORMAT_HEADERS",
    "UNIT_INPUT_AND_OUTPUT",
    "AllQueryStringTypesInput",
    "AllQueryStringTypesOutput",
    "ClientOptionalDefaults",
    "ComplexError",
    "ComplexNestedErrorData",
    "ConstantAndVariableQueryStringInput",
    "ConstantAndVariableQueryStringOutput",
    "ConstantQueryStringInput",
    "ConstantQueryStringOutput",
    "ContentTypeParametersInput",
    "ContentTypeParametersOutput",
    "DatetimeOffsetsInput",
    "DatetimeOffsetsOutput",
    "Defaults",
    "Dialog",
    "DocumentTypeAsMapValueInput",
    "DocumentTypeAsMapValueOutput",
    "DocumentTypeAsPayloadInput",
    "DocumentTypeAsPayloadOutput",
    "DocumentTypeInput",
    "DocumentTypeOutput",
    "EmptyInputAndEmptyOutputInput",
    "EmptyInputAndEmptyOutputOutput",
    "EndpointOperationInput",
    "EndpointOperationOutput",
    "EndpointWithHostLabelOperationInput",
    "EndpointWithHostLabelOperationOutput",
    "Farewell",
    "FooEnum",
    "FooError",
    "FractionalSecondsInput",
    "FractionalSecondsOutput",
    "GreetingStruct",
    "GreetingWithErrorsInput",
    "GreetingWithErrorsOutput",
    "HostWithPathOperationInput",
    "HostWithPathOperationOutput",
    "HttpChecksumRequiredInput",
    "HttpChecksumRequiredOutput",
    "HttpEmptyPrefixHeadersInput",
    "HttpEmptyPrefixHeadersOutput",
    "HttpEnumPayloadInput",
    "HttpEnumPayloadOutput",
    "HttpPayloadTraitsInput",
    "HttpPayloadTraitsOutput",
    "HttpPayloadTraitsWithMediaTypeInput",
    "HttpPayloadTraitsWithMediaTypeOutput",
    "HttpPayloadWithStructureInput",
    "HttpPayloadWithStructureOutput",
    "HttpPayloadWithUnionInput",
    "HttpPayloadWithUnionOutput",
    "HttpPrefixHeadersInResponseInput",
    "HttpPrefixHeadersInResponseOutput",
    "HttpPrefixHeadersInput",
    "HttpPrefixHeadersOutput",
    "HttpQueryParamsOnlyOperationInput",
    "HttpQueryParamsOnlyOperationOutput",
    "HttpRequestWithFloatLabelsInput",
    "HttpRequestWithFloatLabelsOutput",
    "HttpRequestWithGreedyLabelInPathInput",
    "HttpRequestWithGreedyLabelInPathOutput",
    "HttpRequestWithLabelsAndTimestampFormatInput",
    "HttpRequestWithLabelsAndTimestampFormatOutput",
    "HttpRequestWithLabelsInput",
    "HttpRequestWithLabelsOutput",
    "HttpRequestWithRegexLiteralInput",
    "HttpRequestWithRegexLiteralOutput",
    "HttpResponseCodeInput",
    "HttpResponseCodeOutput",
    "HttpStringPayloadInput",
    "HttpStringPayloadOutput",
    "IgnoreQueryParamsInResponseInput",
    "IgnoreQueryParamsInResponseOutput",
    "InputAndOutputWithHeadersInput",
    "InputAndOutputWithHeadersOutput",
    "IntegerEnum",
    "InvalidGreeting",
    "JsonBlobsInput",
    "JsonBlobsOutput",
    "JsonEnumsInput",
    "JsonEnumsOutput",
    "JsonIntEnumsInput",
    "JsonIntEnumsOutput",
    "JsonListsInput",
    "JsonListsOutput",
    "JsonMapsInput",
    "JsonMapsOutput",
    "JsonTimestampsInput",
    "JsonTimestampsOutput",
    "JsonUnionsInput",
    "JsonUnionsOutput",
    "MalformedAcceptWithBodyInput",
    "MalformedAcceptWithBodyOutput",
    "MalformedAcceptWithGenericStringInput",
    "MalformedAcceptWithGenericStringOutput",
    "MalformedAcceptWithPayloadInput",
    "MalformedAcceptWithPayloadOutput",
    "MalformedBlobInput",
    "MalformedBlobOutput",
    "MalformedBooleanInput",
    "MalformedBooleanOutput",
    "MalformedByteInput",
    "MalformedByteOutput",
    "MalformedContentTypeWithBodyInput",
    "MalformedContentTypeWithBodyOutput",
    "MalformedContentTypeWithGenericStringInput",
    "MalformedContentTypeWithGenericStringOutput",
    "MalformedContentTypeWithPayloadInput",
    "MalformedContentTypeWithPayloadOutput",
    "MalformedContentTypeWithoutBodyEmptyInputInput",
    "MalformedContentTypeWithoutBodyEmptyInputOutput",
    "MalformedContentTypeWithoutBodyInput",
    "MalformedContentTypeWithoutBodyOutput",
    "MalformedDoubleInput",
    "MalformedDoubleOutput",
    "MalformedFloatInput",
    "MalformedFloatOutput",
    "MalformedIntegerInput",
    "MalformedIntegerOutput",
    "MalformedListInput",
    "MalformedListOutput",
    "MalformedLongInput",
    "MalformedLongOutput",
    "MalformedMapInput",
    "MalformedMapOutput",
    "MalformedRequestBodyInput",
    "MalformedRequestBodyOutput",
    "MalformedShortInput",
    "MalformedShortOutput",
    "MalformedStringInput",
    "MalformedStringOutput",
    "MalformedTimestampBodyDateTimeInput",
    "MalformedTimestampBodyDateTimeOutput",
    "MalformedTimestampBodyDefaultInput",
    "MalformedTimestampBodyDefaultOutput",
    "MalformedTimestampBodyHttpDateInput",
    "MalformedTimestampBodyHttpDateOutput",
    "MalformedTimestampHeaderDateTimeInput",
    "MalformedTimestampHeaderDateTimeOutput",
    "MalformedTimestampHeaderDefaultInput",
    "MalformedTimestampHeaderDefaultOutput",
    "MalformedTimestampHeaderEpochInput",
    "MalformedTimestampHeaderEpochOutput",
    "MalformedTimestampPathDefaultInput",
    "MalformedTimestampPathDefaultOutput",
    "MalformedTimestampPathEpochInput",
    "MalformedTimestampPathEpochOutput",
    "MalformedTimestampPathHttpDateInput",
    "MalformedTimestampPathHttpDateOutput",
    "MalformedTimestampQueryDefaultInput",
    "MalformedTimestampQueryDefaultOutput",
    "MalformedTimestampQueryEpochInput",
    "MalformedTimestampQueryEpochOutput",
    "MalformedTimestampQueryHttpDateInput",
    "MalformedTimestampQueryHttpDateOutput",
    "MalformedUnionInput",
    "MalformedUnionOutput",
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
    "NoInputAndNoOutputInput",
    "NoInputAndNoOutputOutput",
    "NoInputAndOutputInput",
    "NoInputAndOutputOutput",
    "NullAndEmptyHeadersClientInput",
    "NullAndEmptyHeadersClientOutput",
    "NullAndEmptyHeadersServerInput",
    "NullAndEmptyHeadersServerOutput",
    "OmitsNullSerializesEmptyStringInput",
    "OmitsNullSerializesEmptyStringOutput",
    "OmitsSerializingEmptyListsInput",
    "OmitsSerializingEmptyListsOutput",
    "OperationWithDefaultsInput",
    "OperationWithDefaultsOutput",
    "OperationWithNestedStructureInput",
    "OperationWithNestedStructureOutput",
    "PayloadConfig",
    "PlayerAction",
    "PlayerActionQuit",
    "PlayerActionUnknown",
    "PostPlayerActionInput",
    "PostPlayerActionOutput",
    "PostUnionWithJsonNameInput",
    "PostUnionWithJsonNameOutput",
    "PutWithContentEncodingInput",
    "PutWithContentEncodingOutput",
    "QueryIdempotencyTokenAutoFillInput",
    "QueryIdempotencyTokenAutoFillOutput",
    "QueryParamsAsStringListMapInput",
    "QueryParamsAsStringListMapOutput",
    "QueryPrecedenceInput",
    "QueryPrecedenceOutput",
    "RecursiveShapesInput",
    "RecursiveShapesInputOutputNested1",
    "RecursiveShapesInputOutputNested2",
    "RecursiveShapesOutput",
    "RenamedGreeting",
    "ResponseCodeHttpFallbackInput",
    "ResponseCodeHttpFallbackOutput",
    "ResponseCodeRequiredInput",
    "ResponseCodeRequiredOutput",
    "ServiceError",
    "SimpleScalarPropertiesInput",
    "SimpleScalarPropertiesOutput",
    "SimpleUnion",
    "SimpleUnionInt",
    "SimpleUnionString",
    "SimpleUnionUnknown",
    "SparseJsonListsInput",
    "SparseJsonListsOutput",
    "SparseJsonMapsInput",
    "SparseJsonMapsOutput",
    "StringEnum",
    "StructureListMember",
    "TestBodyStructureInput",
    "TestBodyStructureOutput",
    "TestConfig",
    "TestEnum",
    "TestGetNoInputNoPayloadInput",
    "TestGetNoInputNoPayloadOutput",
    "TestGetNoPayloadInput",
    "TestGetNoPayloadOutput",
    "TestIntEnum",
    "TestPayloadBlobInput",
    "TestPayloadBlobOutput",
    "TestPayloadStructureInput",
    "TestPayloadStructureOutput",
    "TestPostNoInputNoPayloadInput",
    "TestPostNoInputNoPayloadOutput",
    "TestPostNoPayloadInput",
    "TestPostNoPayloadOutput",
    "TimestampFormatHeadersInput",
    "TimestampFormatHeadersOutput",
    "TopLevel",
    "UnionPayload",
    "UnionPayloadGreeting",
    "UnionPayloadUnknown",
    "UnionWithJsonName",
    "UnionWithJsonNameBar",
    "UnionWithJsonNameBaz",
    "UnionWithJsonNameFoo",
    "UnionWithJsonNameUnknown",
    "Unit",
    "UnitInputAndOutputInput",
    "UnitInputAndOutputOutput",
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

class AllQueryStringTypesInputDict(TypedDict, total=False):
    "Dictionary form of `AllQueryStringTypesInput`."

    query_string: str | None
    query_string_list: Sequence[str] | None
    query_string_set: Sequence[str] | None
    query_byte: int | None
    query_short: int | None
    query_integer: int | None
    query_integer_list: Sequence[int] | None
    query_integer_set: Sequence[int] | None
    query_long: int | None
    query_float: float | None
    query_double: float | None
    query_double_list: Sequence[float] | None
    query_boolean: bool | None
    query_boolean_list: Sequence[bool] | None
    query_timestamp: datetime | None
    query_timestamp_list: Sequence[datetime] | None
    query_enum: str | None
    query_enum_list: Sequence[str] | None
    query_integer_enum: int | None
    query_integer_enum_list: Sequence[int] | None
    query_params_map_of_string_list: Mapping[str, Sequence[str]] | None

@dataclass(kw_only=True)
class ClientOptionalDefaults(_SerdeShape):
    "Dataclass for ClientOptionalDefaults structure."

    member: int | None = ...

class ClientOptionalDefaultsDict(TypedDict, total=False):
    "Dictionary form of `ClientOptionalDefaults`."

    member: int | None

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

class ConstantAndVariableQueryStringInputDict(TypedDict, total=False):
    "Dictionary form of `ConstantAndVariableQueryStringInput`."

    baz: str | None
    maybe_set: str | None

@dataclass(kw_only=True)
class ConstantQueryStringInput(_SerdeShape):
    "Dataclass for ConstantQueryStringInput structure."

    hello: str | None = ...

class ConstantQueryStringInputDict(TypedDict, total=False):
    "Dictionary form of `ConstantQueryStringInput`."

    hello: Required[str]

@dataclass(kw_only=True)
class ContentTypeParametersInput(_SerdeShape):
    "Dataclass for ContentTypeParametersInput structure."

    value: int | None = ...

class ContentTypeParametersInputDict(TypedDict, total=False):
    "Dictionary form of `ContentTypeParametersInput`."

    value: int | None

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

class DefaultsDict(TypedDict, total=False):
    "Dictionary form of `Defaults`."

    default_string: str | None
    default_boolean: bool | None
    default_list: Sequence[str] | None
    default_document_map: Document | None
    default_document_string: Document | None
    default_document_boolean: Document | None
    default_document_list: Document | None
    default_null_document: Document | None
    default_timestamp: datetime | None
    default_blob: bytes | None
    default_byte: int | None
    default_short: int | None
    default_integer: int | None
    default_long: int | None
    default_float: float | None
    default_double: float | None
    default_map: Mapping[str, str] | None
    default_enum: str | None
    default_int_enum: int | None
    empty_string: str | None
    false_boolean: bool | None
    empty_blob: bytes | None
    zero_byte: int | None
    zero_short: int | None
    zero_integer: int | None
    zero_long: int | None
    zero_float: float | None
    zero_double: float | None

@dataclass(kw_only=True)
class Dialog(_SerdeShape):
    "Dataclass for Dialog structure."

    language: str | None = ...
    greeting: str | None = ...
    farewell: Farewell | None = ...

class DialogDict(TypedDict, total=False):
    "Dictionary form of `Dialog`."

    language: str | None
    greeting: str | None
    farewell: Farewell | FarewellDict | None

@dataclass(kw_only=True)
class EmptyInputAndEmptyOutputInput(_SerdeShape):
    "Dataclass for EmptyInputAndEmptyOutputInput structure."

class EmptyInputAndEmptyOutputInputDict(TypedDict, total=False):
    "Dictionary form of `EmptyInputAndEmptyOutputInput`."

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
class Farewell(_SerdeShape):
    "Dataclass for Farewell structure."

    phrase: str | None = ...

class FarewellDict(TypedDict, total=False):
    "Dictionary form of `Farewell`."

    phrase: str | None

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
class HttpEmptyPrefixHeadersInput(_SerdeShape):
    "Dataclass for HttpEmptyPrefixHeadersInput structure."

    prefix_headers: dict[str, str] | None = ...
    specific_header: str | None = ...

class HttpEmptyPrefixHeadersInputDict(TypedDict, total=False):
    "Dictionary form of `HttpEmptyPrefixHeadersInput`."

    prefix_headers: Mapping[str, str] | None
    specific_header: str | None

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
class HttpPrefixHeadersInResponseInput(_SerdeShape):
    "Dataclass for HttpPrefixHeadersInResponseInput structure."

class HttpPrefixHeadersInResponseInputDict(TypedDict, total=False):
    "Dictionary form of `HttpPrefixHeadersInResponseInput`."

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

class HttpPrefixHeadersInputDict(TypedDict, total=False):
    "Dictionary form of `HttpPrefixHeadersInput`."

    foo: str | None
    foo_map: Mapping[str, str] | None

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
class HttpRequestWithFloatLabelsInput(_SerdeShape):
    "Dataclass for HttpRequestWithFloatLabelsInput structure."

    float_: float | None = ...
    double: float | None = ...

class HttpRequestWithFloatLabelsInputDict(TypedDict, total=False):
    "Dictionary form of `HttpRequestWithFloatLabelsInput`."

    float_: Required[float]
    double: Required[float]

@dataclass(kw_only=True)
class HttpRequestWithGreedyLabelInPathInput(_SerdeShape):
    "Dataclass for HttpRequestWithGreedyLabelInPathInput structure."

    foo: str | None = ...
    baz: str | None = ...

class HttpRequestWithGreedyLabelInPathInputDict(TypedDict, total=False):
    "Dictionary form of `HttpRequestWithGreedyLabelInPathInput`."

    foo: Required[str]
    baz: Required[str]

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

class HttpRequestWithLabelsAndTimestampFormatInputDict(TypedDict, total=False):
    "Dictionary form of `HttpRequestWithLabelsAndTimestampFormatInput`."

    member_epoch_seconds: Required[datetime]
    member_http_date: Required[datetime]
    member_date_time: Required[datetime]
    default_format: Required[datetime]
    target_epoch_seconds: Required[datetime]
    target_http_date: Required[datetime]
    target_date_time: Required[datetime]

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

class HttpRequestWithLabelsInputDict(TypedDict, total=False):
    "Dictionary form of `HttpRequestWithLabelsInput`."

    string: Required[str]
    short: Required[int]
    integer: Required[int]
    long: Required[int]
    float_: Required[float]
    double: Required[float]
    boolean: Required[bool]
    "Serialized in the path as true or false."
    timestamp: Required[datetime]
    """
    Note that this member has no format, so it's serialized as an RFC 3399
    date-time.
    """

@dataclass(kw_only=True)
class HttpRequestWithRegexLiteralInput(_SerdeShape):
    "Dataclass for HttpRequestWithRegexLiteralInput structure."

    str_: str | None = ...

class HttpRequestWithRegexLiteralInputDict(TypedDict, total=False):
    "Dictionary form of `HttpRequestWithRegexLiteralInput`."

    str_: Required[str]

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

class MalformedBlobInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedBlobInput`."

    blob: bytes | None

@dataclass(kw_only=True)
class MalformedBooleanInput(_SerdeShape):
    "Dataclass for MalformedBooleanInput structure."

    boolean_in_body: bool | None = ...
    boolean_in_path: bool | None = ...
    boolean_in_query: bool | None = ...
    boolean_in_header: bool | None = ...

class MalformedBooleanInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedBooleanInput`."

    boolean_in_body: bool | None
    boolean_in_path: Required[bool]
    boolean_in_query: bool | None
    boolean_in_header: bool | None

@dataclass(kw_only=True)
class MalformedByteInput(_SerdeShape):
    "Dataclass for MalformedByteInput structure."

    byte_in_body: int | None = ...
    byte_in_path: int | None = ...
    byte_in_query: int | None = ...
    byte_in_header: int | None = ...

class MalformedByteInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedByteInput`."

    byte_in_body: int | None
    byte_in_path: Required[int]
    byte_in_query: int | None
    byte_in_header: int | None

@dataclass(kw_only=True)
class MalformedContentTypeWithGenericStringInput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithGenericStringInput structure."

    payload: str | None = ...

class MalformedContentTypeWithGenericStringInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedContentTypeWithGenericStringInput`."

    payload: str | None

@dataclass(kw_only=True)
class MalformedContentTypeWithPayloadInput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithPayloadInput structure."

    payload: bytes | None = ...

class MalformedContentTypeWithPayloadInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedContentTypeWithPayloadInput`."

    payload: bytes | None

@dataclass(kw_only=True)
class MalformedContentTypeWithoutBodyEmptyInputInput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithoutBodyEmptyInputInput structure."

    header: str | None = ...

class MalformedContentTypeWithoutBodyEmptyInputInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedContentTypeWithoutBodyEmptyInputInput`."

    header: str | None

@dataclass(kw_only=True)
class MalformedDoubleInput(_SerdeShape):
    "Dataclass for MalformedDoubleInput structure."

    double_in_body: float | None = ...
    double_in_path: float | None = ...
    double_in_query: float | None = ...
    double_in_header: float | None = ...

class MalformedDoubleInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedDoubleInput`."

    double_in_body: float | None
    double_in_path: Required[float]
    double_in_query: float | None
    double_in_header: float | None

@dataclass(kw_only=True)
class MalformedFloatInput(_SerdeShape):
    "Dataclass for MalformedFloatInput structure."

    float_in_body: float | None = ...
    float_in_path: float | None = ...
    float_in_query: float | None = ...
    float_in_header: float | None = ...

class MalformedFloatInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedFloatInput`."

    float_in_body: float | None
    float_in_path: Required[float]
    float_in_query: float | None
    float_in_header: float | None

@dataclass(kw_only=True)
class MalformedIntegerInput(_SerdeShape):
    "Dataclass for MalformedIntegerInput structure."

    integer_in_body: int | None = ...
    integer_in_path: int | None = ...
    integer_in_query: int | None = ...
    integer_in_header: int | None = ...

class MalformedIntegerInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedIntegerInput`."

    integer_in_body: int | None
    integer_in_path: Required[int]
    integer_in_query: int | None
    integer_in_header: int | None

@dataclass(kw_only=True)
class MalformedListInput(_SerdeShape):
    "Dataclass for MalformedListInput structure."

    body_list: list[str] | None = ...

class MalformedListInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedListInput`."

    body_list: Sequence[str] | None

@dataclass(kw_only=True)
class MalformedLongInput(_SerdeShape):
    "Dataclass for MalformedLongInput structure."

    long_in_body: int | None = ...
    long_in_path: int | None = ...
    long_in_query: int | None = ...
    long_in_header: int | None = ...

class MalformedLongInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedLongInput`."

    long_in_body: int | None
    long_in_path: Required[int]
    long_in_query: int | None
    long_in_header: int | None

@dataclass(kw_only=True)
class MalformedMapInput(_SerdeShape):
    "Dataclass for MalformedMapInput structure."

    body_map: dict[str, str] | None = ...

class MalformedMapInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedMapInput`."

    body_map: Mapping[str, str] | None

@dataclass(kw_only=True)
class MalformedRequestBodyInput(_SerdeShape):
    "Dataclass for MalformedRequestBodyInput structure."

    int_: int | None = ...
    float_: float | None = ...

class MalformedRequestBodyInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedRequestBodyInput`."

    int_: int | None
    float_: float | None

@dataclass(kw_only=True)
class MalformedShortInput(_SerdeShape):
    "Dataclass for MalformedShortInput structure."

    short_in_body: int | None = ...
    short_in_path: int | None = ...
    short_in_query: int | None = ...
    short_in_header: int | None = ...

class MalformedShortInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedShortInput`."

    short_in_body: int | None
    short_in_path: Required[int]
    short_in_query: int | None
    short_in_header: int | None

@dataclass(kw_only=True)
class MalformedStringInput(_SerdeShape):
    "Dataclass for MalformedStringInput structure."

    blob: str | None = ...

class MalformedStringInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedStringInput`."

    blob: str | None

@dataclass(kw_only=True)
class MalformedTimestampBodyDateTimeInput(_SerdeShape):
    "Dataclass for MalformedTimestampBodyDateTimeInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampBodyDateTimeInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampBodyDateTimeInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedTimestampBodyDefaultInput(_SerdeShape):
    "Dataclass for MalformedTimestampBodyDefaultInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampBodyDefaultInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampBodyDefaultInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedTimestampBodyHttpDateInput(_SerdeShape):
    "Dataclass for MalformedTimestampBodyHttpDateInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampBodyHttpDateInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampBodyHttpDateInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedTimestampHeaderDateTimeInput(_SerdeShape):
    "Dataclass for MalformedTimestampHeaderDateTimeInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampHeaderDateTimeInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampHeaderDateTimeInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedTimestampHeaderDefaultInput(_SerdeShape):
    "Dataclass for MalformedTimestampHeaderDefaultInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampHeaderDefaultInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampHeaderDefaultInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedTimestampHeaderEpochInput(_SerdeShape):
    "Dataclass for MalformedTimestampHeaderEpochInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampHeaderEpochInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampHeaderEpochInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedTimestampPathDefaultInput(_SerdeShape):
    "Dataclass for MalformedTimestampPathDefaultInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampPathDefaultInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampPathDefaultInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedTimestampPathEpochInput(_SerdeShape):
    "Dataclass for MalformedTimestampPathEpochInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampPathEpochInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampPathEpochInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedTimestampPathHttpDateInput(_SerdeShape):
    "Dataclass for MalformedTimestampPathHttpDateInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampPathHttpDateInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampPathHttpDateInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedTimestampQueryDefaultInput(_SerdeShape):
    "Dataclass for MalformedTimestampQueryDefaultInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampQueryDefaultInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampQueryDefaultInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedTimestampQueryEpochInput(_SerdeShape):
    "Dataclass for MalformedTimestampQueryEpochInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampQueryEpochInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampQueryEpochInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedTimestampQueryHttpDateInput(_SerdeShape):
    "Dataclass for MalformedTimestampQueryHttpDateInput structure."

    timestamp: datetime | None = ...

class MalformedTimestampQueryHttpDateInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedTimestampQueryHttpDateInput`."

    timestamp: Required[datetime]

@dataclass(kw_only=True)
class MalformedUnionInput(_SerdeShape):
    "Dataclass for MalformedUnionInput structure."

    union: SimpleUnion | None = ...

class MalformedUnionInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedUnionInput`."

    union: SimpleUnion | SimpleUnionDict | None

@dataclass(kw_only=True)
class MediaTypeHeaderInput(_SerdeShape):
    "Dataclass for MediaTypeHeaderInput structure."

    json: str | None = ...

class MediaTypeHeaderInputDict(TypedDict, total=False):
    "Dictionary form of `MediaTypeHeaderInput`."

    json: str | None

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

class MyUnionStringValueDict(TypedDict):
    string_value: str

class MyUnionBooleanValueDict(TypedDict):
    boolean_value: bool

class MyUnionNumberValueDict(TypedDict):
    number_value: int

class MyUnionBlobValueDict(TypedDict):
    blob_value: bytes

class MyUnionTimestampValueDict(TypedDict):
    timestamp_value: datetime

class MyUnionEnumValueDict(TypedDict):
    enum_value: str

class MyUnionListValueDict(TypedDict):
    list_value: Sequence[str]

class MyUnionMapValueDict(TypedDict):
    map_value: Mapping[str, str]

class MyUnionStructureValueDict(TypedDict):
    structure_value: GreetingStruct | GreetingStructDict

class MyUnionRenamedStructureValueDict(TypedDict):
    renamed_structure_value: RenamedGreeting | RenamedGreetingDict

class MyUnionUnionValueDict(TypedDict):
    union_value: NestedUnion | NestedUnionDict

MyUnionDict = (
    MyUnionStringValueDict
    | MyUnionBooleanValueDict
    | MyUnionNumberValueDict
    | MyUnionBlobValueDict
    | MyUnionTimestampValueDict
    | MyUnionEnumValueDict
    | MyUnionListValueDict
    | MyUnionMapValueDict
    | MyUnionStructureValueDict
    | MyUnionRenamedStructureValueDict
    | MyUnionUnionValueDict
)
"Dictionary form of `MyUnion`, setting exactly one variant."

@dataclass(kw_only=True)
class NestedPayload(_SerdeShape):
    "Dataclass for NestedPayload structure."

    greeting: str | None = ...
    name: str | None = ...

class NestedPayloadDict(TypedDict, total=False):
    "Dictionary form of `NestedPayload`."

    greeting: str | None
    name: str | None

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

class NestedUnionStringValueDict(TypedDict):
    string_value: str

NestedUnionDict = NestedUnionStringValueDict
"Dictionary form of `NestedUnion`, setting exactly one variant."

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
class OmitsNullSerializesEmptyStringInput(_SerdeShape):
    "Dataclass for OmitsNullSerializesEmptyStringInput structure."

    null_value: str | None = ...
    empty_string: str | None = ...

class OmitsNullSerializesEmptyStringInputDict(TypedDict, total=False):
    "Dictionary form of `OmitsNullSerializesEmptyStringInput`."

    null_value: str | None
    empty_string: str | None

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

class OmitsSerializingEmptyListsInputDict(TypedDict, total=False):
    "Dictionary form of `OmitsSerializingEmptyListsInput`."

    query_string_list: Sequence[str] | None
    query_integer_list: Sequence[int] | None
    query_double_list: Sequence[float] | None
    query_boolean_list: Sequence[bool] | None
    query_timestamp_list: Sequence[datetime] | None
    query_enum_list: Sequence[str] | None
    query_integer_enum_list: Sequence[int] | None

@dataclass(kw_only=True)
class OperationWithDefaultsInput(_SerdeShape):
    "Dataclass for OperationWithDefaultsInput structure."

    defaults: Defaults | None = ...
    client_optional_defaults: ClientOptionalDefaults | None = ...
    top_level_default: str | None = ...
    other_top_level_default: int | None = ...

class OperationWithDefaultsInputDict(TypedDict, total=False):
    "Dictionary form of `OperationWithDefaultsInput`."

    defaults: Defaults | DefaultsDict | None
    client_optional_defaults: ClientOptionalDefaults | ClientOptionalDefaultsDict | None
    top_level_default: str | None
    other_top_level_default: int | None

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

class OperationWithNestedStructureInputDict(TypedDict, total=False):
    "Dictionary form of `OperationWithNestedStructureInput`."

    top_level: Required[TopLevel | TopLevelDict]

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
class PayloadConfig(_SerdeShape):
    "Dataclass for PayloadConfig structure."

    data: int | None = ...

class PayloadConfigDict(TypedDict, total=False):
    "Dictionary form of `PayloadConfig`."

    data: int | None

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

class PlayerActionQuitDict(TypedDict):
    quit: Unit | UnitDict
    "Quit the game."

PlayerActionDict = PlayerActionQuitDict
"Dictionary form of `PlayerAction`, setting exactly one variant."

@dataclass(kw_only=True)
class PostPlayerActionInput(_SerdeShape):
    "Dataclass for PostPlayerActionInput structure."

    action: PlayerAction | None = ...

class PostPlayerActionInputDict(TypedDict, total=False):
    "Dictionary form of `PostPlayerActionInput`."

    action: PlayerAction | PlayerActionDict | None

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

class PostUnionWithJsonNameInputDict(TypedDict, total=False):
    "Dictionary form of `PostUnionWithJsonNameInput`."

    value: UnionWithJsonName | UnionWithJsonNameDict | None

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

class PutWithContentEncodingInputDict(TypedDict, total=False):
    "Dictionary form of `PutWithContentEncodingInput`."

    encoding: str | None
    data: str | None

@dataclass(kw_only=True)
class QueryIdempotencyTokenAutoFillInput(_SerdeShape):
    "Dataclass for QueryIdempotencyTokenAutoFillInput structure."

    token: str | None = ...
    "This field is autopopulated if not provided."

class QueryIdempotencyTokenAutoFillInputDict(TypedDict, total=False):
    "Dictionary form of `QueryIdempotencyTokenAutoFillInput`."

    token: str | None
    "This field is autopopulated if not provided."

@dataclass(kw_only=True)
class QueryParamsAsStringListMapInput(_SerdeShape):
    "Dataclass for QueryParamsAsStringListMapInput structure."

    qux: str | None = ...
    foo: dict[str, list[str]] | None = ...

class QueryParamsAsStringListMapInputDict(TypedDict, total=False):
    "Dictionary form of `QueryParamsAsStringListMapInput`."

    qux: str | None
    foo: Mapping[str, Sequence[str]] | None

@dataclass(kw_only=True)
class QueryPrecedenceInput(_SerdeShape):
    "Dataclass for QueryPrecedenceInput structure."

    foo: str | None = ...
    baz: dict[str, str] | None = ...

class QueryPrecedenceInputDict(TypedDict, total=False):
    "Dictionary form of `QueryPrecedenceInput`."

    foo: str | None
    baz: Mapping[str, str] | None

@dataclass(kw_only=True)
class RecursiveShapesInputOutputNested1(_SerdeShape):
    "Dataclass for RecursiveShapesInputOutputNested1 structure."

    foo: str | None = ...
    nested: RecursiveShapesInputOutputNested2 | None = ...

class RecursiveShapesInputOutputNested1Dict(TypedDict, total=False):
    "Dictionary form of `RecursiveShapesInputOutputNested1`."

    foo: str | None
    nested: (
        RecursiveShapesInputOutputNested2 | RecursiveShapesInputOutputNested2Dict | None
    )

@dataclass(kw_only=True)
class RecursiveShapesInputOutputNested2(_SerdeShape):
    "Dataclass for RecursiveShapesInputOutputNested2 structure."

    bar: str | None = ...
    recursive_member: RecursiveShapesInputOutputNested1 | None = ...

class RecursiveShapesInputOutputNested2Dict(TypedDict, total=False):
    "Dictionary form of `RecursiveShapesInputOutputNested2`."

    bar: str | None
    recursive_member: (
        RecursiveShapesInputOutputNested1 | RecursiveShapesInputOutputNested1Dict | None
    )

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

class SimpleUnionIntDict(TypedDict):
    int_: int

class SimpleUnionStringDict(TypedDict):
    string: str

SimpleUnionDict = SimpleUnionIntDict | SimpleUnionStringDict
"Dictionary form of `SimpleUnion`, setting exactly one variant."

class StringEnum(UnknownEnumMixin, StrEnum):
    V = "enumvalue"

@dataclass(kw_only=True)
class StructureListMember(_SerdeShape):
    "Dataclass for StructureListMember structure."

    a: str | None = ...
    b: str | None = ...

class StructureListMemberDict(TypedDict, total=False):
    "Dictionary form of `StructureListMember`."

    a: str | None
    b: str | None

@dataclass(kw_only=True)
class TestConfig(_SerdeShape):
    "Dataclass for TestConfig structure."

    timeout: int | None = ...

class TestConfigDict(TypedDict, total=False):
    "Dictionary form of `TestConfig`."

    timeout: int | None

class TestEnum(UnknownEnumMixin, StrEnum):
    FOO = "FOO"
    BAR = "BAR"
    BAZ = "BAZ"

class TestIntEnum(UnknownEnumMixin, IntEnum):
    ONE = 1
    TWO = 2

@dataclass(kw_only=True)
class TopLevel(_SerdeShape):
    "Dataclass for TopLevel structure."

    dialog: Dialog
    dialog_list: list[Dialog] | None = ...
    dialog_map: dict[str, Dialog] | None = ...

class TopLevelDict(TypedDict, total=False):
    "Dictionary form of `TopLevel`."

    dialog: Required[Dialog | DialogDict]
    dialog_list: Sequence[Dialog | DialogDict] | None
    dialog_map: Mapping[str, Dialog | DialogDict] | None

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

class UnionPayloadGreetingDict(TypedDict):
    greeting: str

UnionPayloadDict = UnionPayloadGreetingDict
"Dictionary form of `UnionPayload`, setting exactly one variant."

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

class UnionWithJsonNameFooDict(TypedDict):
    foo: str

class UnionWithJsonNameBarDict(TypedDict):
    bar: str

class UnionWithJsonNameBazDict(TypedDict):
    baz: str

UnionWithJsonNameDict = (
    UnionWithJsonNameFooDict | UnionWithJsonNameBarDict | UnionWithJsonNameBazDict
)
"Dictionary form of `UnionWithJsonName`, setting exactly one variant."

@dataclass(kw_only=True)
class RenamedGreeting(_SerdeShape):
    "Dataclass for GreetingStruct structure."

    salutation: str | None = ...

class RenamedGreetingDict(TypedDict, total=False):
    "Dictionary form of `RenamedGreeting`."

    salutation: str | None

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

class GreetingStructDict(TypedDict, total=False):
    "Dictionary form of `GreetingStruct`."

    hi: str | None

class IntegerEnum(UnknownEnumMixin, IntEnum):
    A = 1
    B = 2
    C = 3

@dataclass(kw_only=True)
class AllQueryStringTypesOutput(_SerdeShape):
    "Dataclass for AllQueryStringTypesOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ConstantAndVariableQueryStringOutput(_SerdeShape):
    "Dataclass for ConstantAndVariableQueryStringOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ConstantQueryStringOutput(_SerdeShape):
    "Dataclass for ConstantQueryStringOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class DatetimeOffsetsInput(_SerdeShape):
    "Dataclass for DatetimeOffsetsInput structure."

class DatetimeOffsetsInputDict(TypedDict, total=False):
    "Dictionary form of `DatetimeOffsetsInput`."

@dataclass(kw_only=True)
class DocumentTypeInput(_SerdeShape):
    "Dataclass for DocumentTypeInput structure."

    string_value: str | None = ...
    document_value: Document | None = ...

class DocumentTypeInputDict(TypedDict, total=False):
    "Dictionary form of `DocumentTypeInput`."

    string_value: str | None
    document_value: Document | None

@dataclass(kw_only=True)
class DocumentTypeOutput(_SerdeShape):
    "Dataclass for DocumentTypeOutput structure."

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
class DocumentTypeAsMapValueInput(_SerdeShape):
    "Dataclass for DocumentTypeAsMapValueInput structure."

    doc_valued_map: dict[str, Document] | None = ...

class DocumentTypeAsMapValueInputDict(TypedDict, total=False):
    "Dictionary form of `DocumentTypeAsMapValueInput`."

    doc_valued_map: Mapping[str, Document] | None

@dataclass(kw_only=True)
class DocumentTypeAsMapValueOutput(_SerdeShape):
    "Dataclass for DocumentTypeAsMapValueOutput structure."

    doc_valued_map: dict[str, Document] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class DocumentTypeAsPayloadInput(_SerdeShape):
    "Dataclass for DocumentTypeAsPayloadInput structure."

    document_value: Document | None = ...

class DocumentTypeAsPayloadInputDict(TypedDict, total=False):
    "Dictionary form of `DocumentTypeAsPayloadInput`."

    document_value: Document | None

@dataclass(kw_only=True)
class DocumentTypeAsPayloadOutput(_SerdeShape):
    "Dataclass for DocumentTypeAsPayloadOutput structure."

    document_value: Document | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class EndpointOperationInput(_SerdeShape):
    "Dataclass for EndpointOperationInput structure."

class EndpointOperationInputDict(TypedDict, total=False):
    "Dictionary form of `EndpointOperationInput`."

@dataclass(kw_only=True)
class EndpointOperationOutput(_SerdeShape):
    "Dataclass for EndpointOperationOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class EndpointWithHostLabelOperationInput(_SerdeShape):
    "Dataclass for EndpointWithHostLabelOperationInput structure."

    label: str | None = ...

class EndpointWithHostLabelOperationInputDict(TypedDict, total=False):
    "Dictionary form of `EndpointWithHostLabelOperationInput`."

    label: Required[str]

@dataclass(kw_only=True)
class EndpointWithHostLabelOperationOutput(_SerdeShape):
    "Dataclass for EndpointWithHostLabelOperationOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class FractionalSecondsInput(_SerdeShape):
    "Dataclass for FractionalSecondsInput structure."

class FractionalSecondsInputDict(TypedDict, total=False):
    "Dictionary form of `FractionalSecondsInput`."

@dataclass(kw_only=True)
class GreetingWithErrorsInput(_SerdeShape):
    "Dataclass for GreetingWithErrorsInput structure."

class GreetingWithErrorsInputDict(TypedDict, total=False):
    "Dictionary form of `GreetingWithErrorsInput`."

@dataclass(kw_only=True)
class HostWithPathOperationInput(_SerdeShape):
    "Dataclass for HostWithPathOperationInput structure."

class HostWithPathOperationInputDict(TypedDict, total=False):
    "Dictionary form of `HostWithPathOperationInput`."

@dataclass(kw_only=True)
class HostWithPathOperationOutput(_SerdeShape):
    "Dataclass for HostWithPathOperationOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpChecksumRequiredInput(_SerdeShape):
    "Dataclass for HttpChecksumRequiredInput structure."

    foo: str | None = ...

class HttpChecksumRequiredInputDict(TypedDict, total=False):
    "Dictionary form of `HttpChecksumRequiredInput`."

    foo: str | None

@dataclass(kw_only=True)
class HttpChecksumRequiredOutput(_SerdeShape):
    "Dataclass for HttpChecksumRequiredOutput structure."

    foo: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpEnumPayloadInput(_SerdeShape):
    "Dataclass for HttpEnumPayloadInput structure."

    payload: str | None = ...

class HttpEnumPayloadInputDict(TypedDict, total=False):
    "Dictionary form of `HttpEnumPayloadInput`."

    payload: str | None

@dataclass(kw_only=True)
class HttpEnumPayloadOutput(_SerdeShape):
    "Dataclass for HttpEnumPayloadOutput structure."

    payload: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPayloadTraitsInput(_SerdeShape):
    "Dataclass for HttpPayloadTraitsInput structure."

    foo: str | None = ...
    blob: bytes | None = ...

class HttpPayloadTraitsInputDict(TypedDict, total=False):
    "Dictionary form of `HttpPayloadTraitsInput`."

    foo: str | None
    blob: bytes | None

@dataclass(kw_only=True)
class HttpPayloadTraitsOutput(_SerdeShape):
    "Dataclass for HttpPayloadTraitsOutput structure."

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
class HttpPayloadTraitsWithMediaTypeInput(_SerdeShape):
    "Dataclass for HttpPayloadTraitsWithMediaTypeInput structure."

    foo: str | None = ...
    blob: bytes | None = ...

class HttpPayloadTraitsWithMediaTypeInputDict(TypedDict, total=False):
    "Dictionary form of `HttpPayloadTraitsWithMediaTypeInput`."

    foo: str | None
    blob: bytes | None

@dataclass(kw_only=True)
class HttpPayloadTraitsWithMediaTypeOutput(_SerdeShape):
    "Dataclass for HttpPayloadTraitsWithMediaTypeOutput structure."

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
class HttpPayloadWithStructureInput(_SerdeShape):
    "Dataclass for HttpPayloadWithStructureInput structure."

    nested: NestedPayload | None = ...

class HttpPayloadWithStructureInputDict(TypedDict, total=False):
    "Dictionary form of `HttpPayloadWithStructureInput`."

    nested: NestedPayload | NestedPayloadDict | None

@dataclass(kw_only=True)
class HttpPayloadWithStructureOutput(_SerdeShape):
    "Dataclass for HttpPayloadWithStructureOutput structure."

    nested: NestedPayload | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpPayloadWithUnionInput(_SerdeShape):
    "Dataclass for HttpPayloadWithUnionInput structure."

    nested: UnionPayload | None = ...

class HttpPayloadWithUnionInputDict(TypedDict, total=False):
    "Dictionary form of `HttpPayloadWithUnionInput`."

    nested: UnionPayload | UnionPayloadDict | None

@dataclass(kw_only=True)
class HttpPayloadWithUnionOutput(_SerdeShape):
    "Dataclass for HttpPayloadWithUnionOutput structure."

    nested: UnionPayload | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpQueryParamsOnlyOperationInput(_SerdeShape):
    "Dataclass for HttpQueryParamsOnlyOperationInput structure."

    query_map: dict[str, str] | None = ...

class HttpQueryParamsOnlyOperationInputDict(TypedDict, total=False):
    "Dictionary form of `HttpQueryParamsOnlyOperationInput`."

    query_map: Mapping[str, str] | None

@dataclass(kw_only=True)
class HttpQueryParamsOnlyOperationOutput(_SerdeShape):
    "Dataclass for HttpQueryParamsOnlyOperationOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpRequestWithFloatLabelsOutput(_SerdeShape):
    "Dataclass for HttpRequestWithFloatLabelsOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpRequestWithGreedyLabelInPathOutput(_SerdeShape):
    "Dataclass for HttpRequestWithGreedyLabelInPathOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpRequestWithLabelsOutput(_SerdeShape):
    "Dataclass for HttpRequestWithLabelsOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpRequestWithLabelsAndTimestampFormatOutput(_SerdeShape):
    "Dataclass for HttpRequestWithLabelsAndTimestampFormatOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpRequestWithRegexLiteralOutput(_SerdeShape):
    "Dataclass for HttpRequestWithRegexLiteralOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HttpResponseCodeInput(_SerdeShape):
    "Dataclass for HttpResponseCodeInput structure."

class HttpResponseCodeInputDict(TypedDict, total=False):
    "Dictionary form of `HttpResponseCodeInput`."

@dataclass(kw_only=True)
class HttpStringPayloadInput(_SerdeShape):
    "Dataclass for HttpStringPayloadInput structure."

    payload: str | None = ...

class HttpStringPayloadInputDict(TypedDict, total=False):
    "Dictionary form of `HttpStringPayloadInput`."

    payload: str | None

@dataclass(kw_only=True)
class HttpStringPayloadOutput(_SerdeShape):
    "Dataclass for HttpStringPayloadOutput structure."

    payload: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class IgnoreQueryParamsInResponseInput(_SerdeShape):
    "Dataclass for IgnoreQueryParamsInResponseInput structure."

class IgnoreQueryParamsInResponseInputDict(TypedDict, total=False):
    "Dictionary form of `IgnoreQueryParamsInResponseInput`."

@dataclass(kw_only=True)
class InputAndOutputWithHeadersInput(_SerdeShape):
    "Dataclass for InputAndOutputWithHeadersInput structure."

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

class InputAndOutputWithHeadersInputDict(TypedDict, total=False):
    "Dictionary form of `InputAndOutputWithHeadersInput`."

    header_string: str | None
    header_byte: int | None
    header_short: int | None
    header_integer: int | None
    header_long: int | None
    header_float: float | None
    header_double: float | None
    header_true_bool: bool | None
    header_false_bool: bool | None
    header_string_list: Sequence[str] | None
    header_string_set: Sequence[str] | None
    header_integer_list: Sequence[int] | None
    header_boolean_list: Sequence[bool] | None
    header_timestamp_list: Sequence[datetime] | None
    header_enum: str | None
    header_enum_list: Sequence[str] | None
    header_integer_enum: int | None
    header_integer_enum_list: Sequence[int] | None

@dataclass(kw_only=True)
class InputAndOutputWithHeadersOutput(_SerdeShape):
    "Dataclass for InputAndOutputWithHeadersOutput structure."

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
class JsonBlobsInput(_SerdeShape):
    "Dataclass for JsonBlobsInput structure."

    data: bytes | None = ...

class JsonBlobsInputDict(TypedDict, total=False):
    "Dictionary form of `JsonBlobsInput`."

    data: bytes | None

@dataclass(kw_only=True)
class JsonBlobsOutput(_SerdeShape):
    "Dataclass for JsonBlobsOutput structure."

    data: bytes | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class JsonEnumsInput(_SerdeShape):
    "Dataclass for JsonEnumsInput structure."

    foo_enum1: str | None = ...
    foo_enum2: str | None = ...
    foo_enum3: str | None = ...
    foo_enum_list: list[str] | None = ...
    foo_enum_set: list[str] | None = ...
    foo_enum_map: dict[str, str] | None = ...

class JsonEnumsInputDict(TypedDict, total=False):
    "Dictionary form of `JsonEnumsInput`."

    foo_enum1: str | None
    foo_enum2: str | None
    foo_enum3: str | None
    foo_enum_list: Sequence[str] | None
    foo_enum_set: Sequence[str] | None
    foo_enum_map: Mapping[str, str] | None

@dataclass(kw_only=True)
class JsonEnumsOutput(_SerdeShape):
    "Dataclass for JsonEnumsOutput structure."

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
class JsonIntEnumsInput(_SerdeShape):
    "Dataclass for JsonIntEnumsInput structure."

    integer_enum1: int | None = ...
    integer_enum2: int | None = ...
    integer_enum3: int | None = ...
    integer_enum_list: list[int] | None = ...
    integer_enum_set: list[int] | None = ...
    integer_enum_map: dict[str, int] | None = ...

class JsonIntEnumsInputDict(TypedDict, total=False):
    "Dictionary form of `JsonIntEnumsInput`."

    integer_enum1: int | None
    integer_enum2: int | None
    integer_enum3: int | None
    integer_enum_list: Sequence[int] | None
    integer_enum_set: Sequence[int] | None
    integer_enum_map: Mapping[str, int] | None

@dataclass(kw_only=True)
class JsonIntEnumsOutput(_SerdeShape):
    "Dataclass for JsonIntEnumsOutput structure."

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
class JsonListsInput(_SerdeShape):
    "Dataclass for JsonListsInput structure."

    string_list: list[str] | None = ...
    string_set: list[str] | None = ...
    integer_list: list[int] | None = ...
    boolean_list: list[bool] | None = ...
    timestamp_list: list[datetime] | None = ...
    enum_list: list[str] | None = ...
    int_enum_list: list[int] | None = ...
    nested_string_list: list[list[str]] | None = ...
    structure_list: list[StructureListMember] | None = ...

class JsonListsInputDict(TypedDict, total=False):
    "Dictionary form of `JsonListsInput`."

    string_list: Sequence[str] | None
    string_set: Sequence[str] | None
    integer_list: Sequence[int] | None
    boolean_list: Sequence[bool] | None
    timestamp_list: Sequence[datetime] | None
    enum_list: Sequence[str] | None
    int_enum_list: Sequence[int] | None
    nested_string_list: Sequence[Sequence[str]] | None
    structure_list: Sequence[StructureListMember | StructureListMemberDict] | None

@dataclass(kw_only=True)
class JsonListsOutput(_SerdeShape):
    "Dataclass for JsonListsOutput structure."

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
class JsonMapsInput(_SerdeShape):
    "Dataclass for JsonMapsInput structure."

    dense_struct_map: dict[str, GreetingStruct] | None = ...
    dense_number_map: dict[str, int] | None = ...
    dense_boolean_map: dict[str, bool] | None = ...
    dense_string_map: dict[str, str] | None = ...
    dense_set_map: dict[str, list[str]] | None = ...

class JsonMapsInputDict(TypedDict, total=False):
    "Dictionary form of `JsonMapsInput`."

    dense_struct_map: Mapping[str, GreetingStruct | GreetingStructDict] | None
    dense_number_map: Mapping[str, int] | None
    dense_boolean_map: Mapping[str, bool] | None
    dense_string_map: Mapping[str, str] | None
    dense_set_map: Mapping[str, Sequence[str]] | None

@dataclass(kw_only=True)
class JsonMapsOutput(_SerdeShape):
    "Dataclass for JsonMapsOutput structure."

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
class JsonTimestampsInput(_SerdeShape):
    "Dataclass for JsonTimestampsInput structure."

    normal: datetime | None = ...
    date_time: datetime | None = ...
    date_time_on_target: datetime | None = ...
    epoch_seconds: datetime | None = ...
    epoch_seconds_on_target: datetime | None = ...
    http_date: datetime | None = ...
    http_date_on_target: datetime | None = ...

class JsonTimestampsInputDict(TypedDict, total=False):
    "Dictionary form of `JsonTimestampsInput`."

    normal: datetime | None
    date_time: datetime | None
    date_time_on_target: datetime | None
    epoch_seconds: datetime | None
    epoch_seconds_on_target: datetime | None
    http_date: datetime | None
    http_date_on_target: datetime | None

@dataclass(kw_only=True)
class JsonTimestampsOutput(_SerdeShape):
    "Dataclass for JsonTimestampsOutput structure."

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
class JsonUnionsInput(_SerdeShape):
    "A shared structure that contains a single union member."

    contents: MyUnion | None = ...

class JsonUnionsInputDict(TypedDict, total=False):
    "Dictionary form of `JsonUnionsInput`."

    contents: MyUnion | MyUnionDict | None

@dataclass(kw_only=True)
class JsonUnionsOutput(_SerdeShape):
    "A shared structure that contains a single union member."

    contents: MyUnion | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedAcceptWithBodyInput(_SerdeShape):
    "Dataclass for MalformedAcceptWithBodyInput structure."

class MalformedAcceptWithBodyInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedAcceptWithBodyInput`."

@dataclass(kw_only=True)
class MalformedAcceptWithBodyOutput(_SerdeShape):
    "Dataclass for MalformedAcceptWithBodyOutput structure."

    hi: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedAcceptWithGenericStringInput(_SerdeShape):
    "Dataclass for MalformedAcceptWithGenericStringInput structure."

class MalformedAcceptWithGenericStringInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedAcceptWithGenericStringInput`."

@dataclass(kw_only=True)
class MalformedAcceptWithPayloadInput(_SerdeShape):
    "Dataclass for MalformedAcceptWithPayloadInput structure."

class MalformedAcceptWithPayloadInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedAcceptWithPayloadInput`."

@dataclass(kw_only=True)
class MalformedBlobOutput(_SerdeShape):
    "Dataclass for MalformedBlobOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedBooleanOutput(_SerdeShape):
    "Dataclass for MalformedBooleanOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedByteOutput(_SerdeShape):
    "Dataclass for MalformedByteOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedContentTypeWithBodyInput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithBodyInput structure."

    hi: str | None = ...

class MalformedContentTypeWithBodyInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedContentTypeWithBodyInput`."

    hi: str | None

@dataclass(kw_only=True)
class MalformedContentTypeWithBodyOutput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithBodyOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedContentTypeWithGenericStringOutput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithGenericStringOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedContentTypeWithPayloadOutput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithPayloadOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedContentTypeWithoutBodyInput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithoutBodyInput structure."

class MalformedContentTypeWithoutBodyInputDict(TypedDict, total=False):
    "Dictionary form of `MalformedContentTypeWithoutBodyInput`."

@dataclass(kw_only=True)
class MalformedContentTypeWithoutBodyOutput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithoutBodyOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedContentTypeWithoutBodyEmptyInputOutput(_SerdeShape):
    "Dataclass for MalformedContentTypeWithoutBodyEmptyInputOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedDoubleOutput(_SerdeShape):
    "Dataclass for MalformedDoubleOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedFloatOutput(_SerdeShape):
    "Dataclass for MalformedFloatOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedIntegerOutput(_SerdeShape):
    "Dataclass for MalformedIntegerOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedListOutput(_SerdeShape):
    "Dataclass for MalformedListOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedLongOutput(_SerdeShape):
    "Dataclass for MalformedLongOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedMapOutput(_SerdeShape):
    "Dataclass for MalformedMapOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedRequestBodyOutput(_SerdeShape):
    "Dataclass for MalformedRequestBodyOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedShortOutput(_SerdeShape):
    "Dataclass for MalformedShortOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedStringOutput(_SerdeShape):
    "Dataclass for MalformedStringOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampBodyDateTimeOutput(_SerdeShape):
    "Dataclass for MalformedTimestampBodyDateTimeOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampBodyDefaultOutput(_SerdeShape):
    "Dataclass for MalformedTimestampBodyDefaultOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampBodyHttpDateOutput(_SerdeShape):
    "Dataclass for MalformedTimestampBodyHttpDateOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampHeaderDateTimeOutput(_SerdeShape):
    "Dataclass for MalformedTimestampHeaderDateTimeOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampHeaderDefaultOutput(_SerdeShape):
    "Dataclass for MalformedTimestampHeaderDefaultOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampHeaderEpochOutput(_SerdeShape):
    "Dataclass for MalformedTimestampHeaderEpochOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampPathDefaultOutput(_SerdeShape):
    "Dataclass for MalformedTimestampPathDefaultOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampPathEpochOutput(_SerdeShape):
    "Dataclass for MalformedTimestampPathEpochOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampPathHttpDateOutput(_SerdeShape):
    "Dataclass for MalformedTimestampPathHttpDateOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampQueryDefaultOutput(_SerdeShape):
    "Dataclass for MalformedTimestampQueryDefaultOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampQueryEpochOutput(_SerdeShape):
    "Dataclass for MalformedTimestampQueryEpochOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedTimestampQueryHttpDateOutput(_SerdeShape):
    "Dataclass for MalformedTimestampQueryHttpDateOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class MalformedUnionOutput(_SerdeShape):
    "Dataclass for MalformedUnionOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class NoInputAndNoOutputInput(_SerdeShape):
    "Dataclass for NoInputAndNoOutputInput structure."

class NoInputAndNoOutputInputDict(TypedDict, total=False):
    "Dictionary form of `NoInputAndNoOutputInput`."

@dataclass(kw_only=True)
class NoInputAndNoOutputOutput(_SerdeShape):
    "Dataclass for NoInputAndNoOutputOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class NoInputAndOutputInput(_SerdeShape):
    "Dataclass for NoInputAndOutputInput structure."

class NoInputAndOutputInputDict(TypedDict, total=False):
    "Dictionary form of `NoInputAndOutputInput`."

@dataclass(kw_only=True)
class NullAndEmptyHeadersClientInput(_SerdeShape):
    "Dataclass for NullAndEmptyHeadersClientInput structure."

    a: str | None = ...
    b: str | None = ...
    c: list[str] | None = ...

class NullAndEmptyHeadersClientInputDict(TypedDict, total=False):
    "Dictionary form of `NullAndEmptyHeadersClientInput`."

    a: str | None
    b: str | None
    c: Sequence[str] | None

@dataclass(kw_only=True)
class NullAndEmptyHeadersClientOutput(_SerdeShape):
    "Dataclass for NullAndEmptyHeadersClientOutput structure."

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
class NullAndEmptyHeadersServerInput(_SerdeShape):
    "Dataclass for NullAndEmptyHeadersServerInput structure."

    a: str | None = ...
    b: str | None = ...
    c: list[str] | None = ...

class NullAndEmptyHeadersServerInputDict(TypedDict, total=False):
    "Dictionary form of `NullAndEmptyHeadersServerInput`."

    a: str | None
    b: str | None
    c: Sequence[str] | None

@dataclass(kw_only=True)
class NullAndEmptyHeadersServerOutput(_SerdeShape):
    "Dataclass for NullAndEmptyHeadersServerOutput structure."

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
class OmitsNullSerializesEmptyStringOutput(_SerdeShape):
    "Dataclass for OmitsNullSerializesEmptyStringOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class OmitsSerializingEmptyListsOutput(_SerdeShape):
    "Dataclass for OmitsSerializingEmptyListsOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class PutWithContentEncodingOutput(_SerdeShape):
    "Dataclass for PutWithContentEncodingOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class QueryIdempotencyTokenAutoFillOutput(_SerdeShape):
    "Dataclass for QueryIdempotencyTokenAutoFillOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class QueryParamsAsStringListMapOutput(_SerdeShape):
    "Dataclass for QueryParamsAsStringListMapOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class QueryPrecedenceOutput(_SerdeShape):
    "Dataclass for QueryPrecedenceOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class RecursiveShapesInput(_SerdeShape):
    "Dataclass for RecursiveShapesInput structure."

    nested: RecursiveShapesInputOutputNested1 | None = ...

class RecursiveShapesInputDict(TypedDict, total=False):
    "Dictionary form of `RecursiveShapesInput`."

    nested: (
        RecursiveShapesInputOutputNested1 | RecursiveShapesInputOutputNested1Dict | None
    )

@dataclass(kw_only=True)
class RecursiveShapesOutput(_SerdeShape):
    "Dataclass for RecursiveShapesOutput structure."

    nested: RecursiveShapesInputOutputNested1 | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ResponseCodeHttpFallbackInput(_SerdeShape):
    "Dataclass for ResponseCodeHttpFallbackInput structure."

class ResponseCodeHttpFallbackInputDict(TypedDict, total=False):
    "Dictionary form of `ResponseCodeHttpFallbackInput`."

@dataclass(kw_only=True)
class ResponseCodeHttpFallbackOutput(_SerdeShape):
    "Dataclass for ResponseCodeHttpFallbackOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ResponseCodeRequiredInput(_SerdeShape):
    "Dataclass for ResponseCodeRequiredInput structure."

class ResponseCodeRequiredInputDict(TypedDict, total=False):
    "Dictionary form of `ResponseCodeRequiredInput`."

@dataclass(kw_only=True)
class SimpleScalarPropertiesInput(_SerdeShape):
    "Dataclass for SimpleScalarPropertiesInput structure."

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

class SimpleScalarPropertiesInputDict(TypedDict, total=False):
    "Dictionary form of `SimpleScalarPropertiesInput`."

    foo: str | None
    string_value: str | None
    true_boolean_value: bool | None
    false_boolean_value: bool | None
    byte_value: int | None
    short_value: int | None
    integer_value: int | None
    long_value: int | None
    float_value: float | None
    double_value: float | None

@dataclass(kw_only=True)
class SimpleScalarPropertiesOutput(_SerdeShape):
    "Dataclass for SimpleScalarPropertiesOutput structure."

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

@dataclass(kw_only=True)
class SparseJsonListsInput(_SerdeShape):
    "Dataclass for SparseJsonListsInput structure."

    sparse_string_list: list[str | None] | None = ...
    sparse_short_list: list[int | None] | None = ...

class SparseJsonListsInputDict(TypedDict, total=False):
    "Dictionary form of `SparseJsonListsInput`."

    sparse_string_list: Sequence[str | None] | None
    sparse_short_list: Sequence[int | None] | None

@dataclass(kw_only=True)
class SparseJsonListsOutput(_SerdeShape):
    "Dataclass for SparseJsonListsOutput structure."

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
class SparseJsonMapsInput(_SerdeShape):
    "Dataclass for SparseJsonMapsInput structure."

    sparse_struct_map: dict[str, GreetingStruct | None] | None = ...
    sparse_number_map: dict[str, int | None] | None = ...
    sparse_boolean_map: dict[str, bool | None] | None = ...
    sparse_string_map: dict[str, str | None] | None = ...
    sparse_set_map: dict[str, list[str] | None] | None = ...

class SparseJsonMapsInputDict(TypedDict, total=False):
    "Dictionary form of `SparseJsonMapsInput`."

    sparse_struct_map: Mapping[str, GreetingStruct | GreetingStructDict | None] | None
    sparse_number_map: Mapping[str, int | None] | None
    sparse_boolean_map: Mapping[str, bool | None] | None
    sparse_string_map: Mapping[str, str | None] | None
    sparse_set_map: Mapping[str, Sequence[str] | None] | None

@dataclass(kw_only=True)
class SparseJsonMapsOutput(_SerdeShape):
    "Dataclass for SparseJsonMapsOutput structure."

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
class TestBodyStructureInput(_SerdeShape):
    "Dataclass for TestBodyStructureInput structure."

    test_id: str | None = ...
    test_config: TestConfig | None = ...

class TestBodyStructureInputDict(TypedDict, total=False):
    "Dictionary form of `TestBodyStructureInput`."

    test_id: str | None
    test_config: TestConfig | TestConfigDict | None

@dataclass(kw_only=True)
class TestBodyStructureOutput(_SerdeShape):
    "Dataclass for TestBodyStructureOutput structure."

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
class TestGetNoInputNoPayloadInput(_SerdeShape):
    "Dataclass for TestGetNoInputNoPayloadInput structure."

class TestGetNoInputNoPayloadInputDict(TypedDict, total=False):
    "Dictionary form of `TestGetNoInputNoPayloadInput`."

@dataclass(kw_only=True)
class TestGetNoInputNoPayloadOutput(_SerdeShape):
    "Dataclass for TestGetNoInputNoPayloadOutput structure."

    test_id: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class TestGetNoPayloadInput(_SerdeShape):
    "Dataclass for TestGetNoPayloadInput structure."

    test_id: str | None = ...

class TestGetNoPayloadInputDict(TypedDict, total=False):
    "Dictionary form of `TestGetNoPayloadInput`."

    test_id: str | None

@dataclass(kw_only=True)
class TestGetNoPayloadOutput(_SerdeShape):
    "Dataclass for TestGetNoPayloadOutput structure."

    test_id: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class TestPayloadBlobInput(_SerdeShape):
    "Dataclass for TestPayloadBlobInput structure."

    content_type: str | None = ...
    data: bytes | None = ...

class TestPayloadBlobInputDict(TypedDict, total=False):
    "Dictionary form of `TestPayloadBlobInput`."

    content_type: str | None
    data: bytes | None

@dataclass(kw_only=True)
class TestPayloadBlobOutput(_SerdeShape):
    "Dataclass for TestPayloadBlobOutput structure."

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
class TestPayloadStructureInput(_SerdeShape):
    "Dataclass for TestPayloadStructureInput structure."

    test_id: str | None = ...
    payload_config: PayloadConfig | None = ...

class TestPayloadStructureInputDict(TypedDict, total=False):
    "Dictionary form of `TestPayloadStructureInput`."

    test_id: str | None
    payload_config: PayloadConfig | PayloadConfigDict | None

@dataclass(kw_only=True)
class TestPayloadStructureOutput(_SerdeShape):
    "Dataclass for TestPayloadStructureOutput structure."

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
class TestPostNoInputNoPayloadInput(_SerdeShape):
    "Dataclass for TestPostNoInputNoPayloadInput structure."

class TestPostNoInputNoPayloadInputDict(TypedDict, total=False):
    "Dictionary form of `TestPostNoInputNoPayloadInput`."

@dataclass(kw_only=True)
class TestPostNoInputNoPayloadOutput(_SerdeShape):
    "Dataclass for TestPostNoInputNoPayloadOutput structure."

    test_id: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class TestPostNoPayloadInput(_SerdeShape):
    "Dataclass for TestPostNoPayloadInput structure."

    test_id: str | None = ...

class TestPostNoPayloadInputDict(TypedDict, total=False):
    "Dictionary form of `TestPostNoPayloadInput`."

    test_id: str | None

@dataclass(kw_only=True)
class TestPostNoPayloadOutput(_SerdeShape):
    "Dataclass for TestPostNoPayloadOutput structure."

    test_id: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class TimestampFormatHeadersInput(_SerdeShape):
    "Dataclass for TimestampFormatHeadersInput structure."

    member_epoch_seconds: datetime | None = ...
    member_http_date: datetime | None = ...
    member_date_time: datetime | None = ...
    default_format: datetime | None = ...
    target_epoch_seconds: datetime | None = ...
    target_http_date: datetime | None = ...
    target_date_time: datetime | None = ...

class TimestampFormatHeadersInputDict(TypedDict, total=False):
    "Dictionary form of `TimestampFormatHeadersInput`."

    member_epoch_seconds: datetime | None
    member_http_date: datetime | None
    member_date_time: datetime | None
    default_format: datetime | None
    target_epoch_seconds: datetime | None
    target_http_date: datetime | None
    target_date_time: datetime | None

@dataclass(kw_only=True)
class TimestampFormatHeadersOutput(_SerdeShape):
    "Dataclass for TimestampFormatHeadersOutput structure."

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
class UnitInputAndOutputInput(_SerdeShape):
    "Dataclass for UnitInputAndOutputInput structure."

class UnitInputAndOutputInputDict(TypedDict, total=False):
    "Dictionary form of `UnitInputAndOutputInput`."

@dataclass(kw_only=True)
class UnitInputAndOutputOutput(_SerdeShape):
    "Dataclass for UnitInputAndOutputOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class Unit(_SerdeShape):
    pass

class UnitDict(TypedDict, total=False):
    "Dictionary form of `Unit`."

ALL_QUERY_STRING_TYPES: APIOperation[
    AllQueryStringTypesInput, AllQueryStringTypesOutput
]
CONSTANT_AND_VARIABLE_QUERY_STRING: APIOperation[
    ConstantAndVariableQueryStringInput, ConstantAndVariableQueryStringOutput
]
CONSTANT_QUERY_STRING: APIOperation[ConstantQueryStringInput, ConstantQueryStringOutput]
CONTENT_TYPE_PARAMETERS: APIOperation[
    ContentTypeParametersInput, ContentTypeParametersOutput
]
DATETIME_OFFSETS: APIOperation[DatetimeOffsetsInput, DatetimeOffsetsOutput]
DOCUMENT_TYPE: APIOperation[DocumentTypeInput, DocumentTypeOutput]
DOCUMENT_TYPE_AS_MAP_VALUE: APIOperation[
    DocumentTypeAsMapValueInput, DocumentTypeAsMapValueOutput
]
DOCUMENT_TYPE_AS_PAYLOAD: APIOperation[
    DocumentTypeAsPayloadInput, DocumentTypeAsPayloadOutput
]
EMPTY_INPUT_AND_EMPTY_OUTPUT: APIOperation[
    EmptyInputAndEmptyOutputInput, EmptyInputAndEmptyOutputOutput
]
ENDPOINT_OPERATION: APIOperation[EndpointOperationInput, EndpointOperationOutput]
ENDPOINT_WITH_HOST_LABEL_OPERATION: APIOperation[
    EndpointWithHostLabelOperationInput, EndpointWithHostLabelOperationOutput
]
FRACTIONAL_SECONDS: APIOperation[FractionalSecondsInput, FractionalSecondsOutput]
GREETING_WITH_ERRORS: APIOperation[GreetingWithErrorsInput, GreetingWithErrorsOutput]
HOST_WITH_PATH_OPERATION: APIOperation[
    HostWithPathOperationInput, HostWithPathOperationOutput
]
HTTP_CHECKSUM_REQUIRED: APIOperation[
    HttpChecksumRequiredInput, HttpChecksumRequiredOutput
]
HTTP_EMPTY_PREFIX_HEADERS: APIOperation[
    HttpEmptyPrefixHeadersInput, HttpEmptyPrefixHeadersOutput
]
HTTP_ENUM_PAYLOAD: APIOperation[HttpEnumPayloadInput, HttpEnumPayloadOutput]
HTTP_PAYLOAD_TRAITS: APIOperation[HttpPayloadTraitsInput, HttpPayloadTraitsOutput]
HTTP_PAYLOAD_TRAITS_WITH_MEDIA_TYPE: APIOperation[
    HttpPayloadTraitsWithMediaTypeInput, HttpPayloadTraitsWithMediaTypeOutput
]
HTTP_PAYLOAD_WITH_STRUCTURE: APIOperation[
    HttpPayloadWithStructureInput, HttpPayloadWithStructureOutput
]
HTTP_PAYLOAD_WITH_UNION: APIOperation[
    HttpPayloadWithUnionInput, HttpPayloadWithUnionOutput
]
HTTP_PREFIX_HEADERS: APIOperation[HttpPrefixHeadersInput, HttpPrefixHeadersOutput]
HTTP_PREFIX_HEADERS_IN_RESPONSE: APIOperation[
    HttpPrefixHeadersInResponseInput, HttpPrefixHeadersInResponseOutput
]
HTTP_QUERY_PARAMS_ONLY_OPERATION: APIOperation[
    HttpQueryParamsOnlyOperationInput, HttpQueryParamsOnlyOperationOutput
]
HTTP_REQUEST_WITH_FLOAT_LABELS: APIOperation[
    HttpRequestWithFloatLabelsInput, HttpRequestWithFloatLabelsOutput
]
HTTP_REQUEST_WITH_GREEDY_LABEL_IN_PATH: APIOperation[
    HttpRequestWithGreedyLabelInPathInput, HttpRequestWithGreedyLabelInPathOutput
]
HTTP_REQUEST_WITH_LABELS: APIOperation[
    HttpRequestWithLabelsInput, HttpRequestWithLabelsOutput
]
HTTP_REQUEST_WITH_LABELS_AND_TIMESTAMP_FORMAT: APIOperation[
    HttpRequestWithLabelsAndTimestampFormatInput,
    HttpRequestWithLabelsAndTimestampFormatOutput,
]
HTTP_REQUEST_WITH_REGEX_LITERAL: APIOperation[
    HttpRequestWithRegexLiteralInput, HttpRequestWithRegexLiteralOutput
]
HTTP_RESPONSE_CODE: APIOperation[HttpResponseCodeInput, HttpResponseCodeOutput]
HTTP_STRING_PAYLOAD: APIOperation[HttpStringPayloadInput, HttpStringPayloadOutput]
IGNORE_QUERY_PARAMS_IN_RESPONSE: APIOperation[
    IgnoreQueryParamsInResponseInput, IgnoreQueryParamsInResponseOutput
]
INPUT_AND_OUTPUT_WITH_HEADERS: APIOperation[
    InputAndOutputWithHeadersInput, InputAndOutputWithHeadersOutput
]
JSON_BLOBS: APIOperation[JsonBlobsInput, JsonBlobsOutput]
JSON_ENUMS: APIOperation[JsonEnumsInput, JsonEnumsOutput]
JSON_INT_ENUMS: APIOperation[JsonIntEnumsInput, JsonIntEnumsOutput]
JSON_LISTS: APIOperation[JsonListsInput, JsonListsOutput]
JSON_MAPS: APIOperation[JsonMapsInput, JsonMapsOutput]
JSON_TIMESTAMPS: APIOperation[JsonTimestampsInput, JsonTimestampsOutput]
JSON_UNIONS: APIOperation[JsonUnionsInput, JsonUnionsOutput]
MALFORMED_ACCEPT_WITH_BODY: APIOperation[
    MalformedAcceptWithBodyInput, MalformedAcceptWithBodyOutput
]
MALFORMED_ACCEPT_WITH_GENERIC_STRING: APIOperation[
    MalformedAcceptWithGenericStringInput, MalformedAcceptWithGenericStringOutput
]
MALFORMED_ACCEPT_WITH_PAYLOAD: APIOperation[
    MalformedAcceptWithPayloadInput, MalformedAcceptWithPayloadOutput
]
MALFORMED_BLOB: APIOperation[MalformedBlobInput, MalformedBlobOutput]
MALFORMED_BOOLEAN: APIOperation[MalformedBooleanInput, MalformedBooleanOutput]
MALFORMED_BYTE: APIOperation[MalformedByteInput, MalformedByteOutput]
MALFORMED_CONTENT_TYPE_WITH_BODY: APIOperation[
    MalformedContentTypeWithBodyInput, MalformedContentTypeWithBodyOutput
]
MALFORMED_CONTENT_TYPE_WITH_GENERIC_STRING: APIOperation[
    MalformedContentTypeWithGenericStringInput,
    MalformedContentTypeWithGenericStringOutput,
]
MALFORMED_CONTENT_TYPE_WITH_PAYLOAD: APIOperation[
    MalformedContentTypeWithPayloadInput, MalformedContentTypeWithPayloadOutput
]
MALFORMED_CONTENT_TYPE_WITHOUT_BODY: APIOperation[
    MalformedContentTypeWithoutBodyInput, MalformedContentTypeWithoutBodyOutput
]
MALFORMED_CONTENT_TYPE_WITHOUT_BODY_EMPTY_INPUT: APIOperation[
    MalformedContentTypeWithoutBodyEmptyInputInput,
    MalformedContentTypeWithoutBodyEmptyInputOutput,
]
MALFORMED_DOUBLE: APIOperation[MalformedDoubleInput, MalformedDoubleOutput]
MALFORMED_FLOAT: APIOperation[MalformedFloatInput, MalformedFloatOutput]
MALFORMED_INTEGER: APIOperation[MalformedIntegerInput, MalformedIntegerOutput]
MALFORMED_LIST: APIOperation[MalformedListInput, MalformedListOutput]
MALFORMED_LONG: APIOperation[MalformedLongInput, MalformedLongOutput]
MALFORMED_MAP: APIOperation[MalformedMapInput, MalformedMapOutput]
MALFORMED_REQUEST_BODY: APIOperation[
    MalformedRequestBodyInput, MalformedRequestBodyOutput
]
MALFORMED_SHORT: APIOperation[MalformedShortInput, MalformedShortOutput]
MALFORMED_STRING: APIOperation[MalformedStringInput, MalformedStringOutput]
MALFORMED_TIMESTAMP_BODY_DATE_TIME: APIOperation[
    MalformedTimestampBodyDateTimeInput, MalformedTimestampBodyDateTimeOutput
]
MALFORMED_TIMESTAMP_BODY_DEFAULT: APIOperation[
    MalformedTimestampBodyDefaultInput, MalformedTimestampBodyDefaultOutput
]
MALFORMED_TIMESTAMP_BODY_HTTP_DATE: APIOperation[
    MalformedTimestampBodyHttpDateInput, MalformedTimestampBodyHttpDateOutput
]
MALFORMED_TIMESTAMP_HEADER_DATE_TIME: APIOperation[
    MalformedTimestampHeaderDateTimeInput, MalformedTimestampHeaderDateTimeOutput
]
MALFORMED_TIMESTAMP_HEADER_DEFAULT: APIOperation[
    MalformedTimestampHeaderDefaultInput, MalformedTimestampHeaderDefaultOutput
]
MALFORMED_TIMESTAMP_HEADER_EPOCH: APIOperation[
    MalformedTimestampHeaderEpochInput, MalformedTimestampHeaderEpochOutput
]
MALFORMED_TIMESTAMP_PATH_DEFAULT: APIOperation[
    MalformedTimestampPathDefaultInput, MalformedTimestampPathDefaultOutput
]
MALFORMED_TIMESTAMP_PATH_EPOCH: APIOperation[
    MalformedTimestampPathEpochInput, MalformedTimestampPathEpochOutput
]
MALFORMED_TIMESTAMP_PATH_HTTP_DATE: APIOperation[
    MalformedTimestampPathHttpDateInput, MalformedTimestampPathHttpDateOutput
]
MALFORMED_TIMESTAMP_QUERY_DEFAULT: APIOperation[
    MalformedTimestampQueryDefaultInput, MalformedTimestampQueryDefaultOutput
]
MALFORMED_TIMESTAMP_QUERY_EPOCH: APIOperation[
    MalformedTimestampQueryEpochInput, MalformedTimestampQueryEpochOutput
]
MALFORMED_TIMESTAMP_QUERY_HTTP_DATE: APIOperation[
    MalformedTimestampQueryHttpDateInput, MalformedTimestampQueryHttpDateOutput
]
MALFORMED_UNION: APIOperation[MalformedUnionInput, MalformedUnionOutput]
MEDIA_TYPE_HEADER: APIOperation[MediaTypeHeaderInput, MediaTypeHeaderOutput]
NO_INPUT_AND_NO_OUTPUT: APIOperation[NoInputAndNoOutputInput, NoInputAndNoOutputOutput]
NO_INPUT_AND_OUTPUT: APIOperation[NoInputAndOutputInput, NoInputAndOutputOutput]
NULL_AND_EMPTY_HEADERS_CLIENT: APIOperation[
    NullAndEmptyHeadersClientInput, NullAndEmptyHeadersClientOutput
]
NULL_AND_EMPTY_HEADERS_SERVER: APIOperation[
    NullAndEmptyHeadersServerInput, NullAndEmptyHeadersServerOutput
]
OMITS_NULL_SERIALIZES_EMPTY_STRING: APIOperation[
    OmitsNullSerializesEmptyStringInput, OmitsNullSerializesEmptyStringOutput
]
OMITS_SERIALIZING_EMPTY_LISTS: APIOperation[
    OmitsSerializingEmptyListsInput, OmitsSerializingEmptyListsOutput
]
OPERATION_WITH_DEFAULTS: APIOperation[
    OperationWithDefaultsInput, OperationWithDefaultsOutput
]
OPERATION_WITH_NESTED_STRUCTURE: APIOperation[
    OperationWithNestedStructureInput, OperationWithNestedStructureOutput
]
POST_PLAYER_ACTION: APIOperation[PostPlayerActionInput, PostPlayerActionOutput]
POST_UNION_WITH_JSON_NAME: APIOperation[
    PostUnionWithJsonNameInput, PostUnionWithJsonNameOutput
]
PUT_WITH_CONTENT_ENCODING: APIOperation[
    PutWithContentEncodingInput, PutWithContentEncodingOutput
]
QUERY_IDEMPOTENCY_TOKEN_AUTO_FILL: APIOperation[
    QueryIdempotencyTokenAutoFillInput, QueryIdempotencyTokenAutoFillOutput
]
QUERY_PARAMS_AS_STRING_LIST_MAP: APIOperation[
    QueryParamsAsStringListMapInput, QueryParamsAsStringListMapOutput
]
QUERY_PRECEDENCE: APIOperation[QueryPrecedenceInput, QueryPrecedenceOutput]
RECURSIVE_SHAPES: APIOperation[RecursiveShapesInput, RecursiveShapesOutput]
RESPONSE_CODE_HTTP_FALLBACK: APIOperation[
    ResponseCodeHttpFallbackInput, ResponseCodeHttpFallbackOutput
]
RESPONSE_CODE_REQUIRED: APIOperation[
    ResponseCodeRequiredInput, ResponseCodeRequiredOutput
]
SIMPLE_SCALAR_PROPERTIES: APIOperation[
    SimpleScalarPropertiesInput, SimpleScalarPropertiesOutput
]
SPARSE_JSON_LISTS: APIOperation[SparseJsonListsInput, SparseJsonListsOutput]
SPARSE_JSON_MAPS: APIOperation[SparseJsonMapsInput, SparseJsonMapsOutput]
TEST_BODY_STRUCTURE: APIOperation[TestBodyStructureInput, TestBodyStructureOutput]
TEST_GET_NO_INPUT_NO_PAYLOAD: APIOperation[
    TestGetNoInputNoPayloadInput, TestGetNoInputNoPayloadOutput
]
TEST_GET_NO_PAYLOAD: APIOperation[TestGetNoPayloadInput, TestGetNoPayloadOutput]
TEST_PAYLOAD_BLOB: APIOperation[TestPayloadBlobInput, TestPayloadBlobOutput]
TEST_PAYLOAD_STRUCTURE: APIOperation[
    TestPayloadStructureInput, TestPayloadStructureOutput
]
TEST_POST_NO_INPUT_NO_PAYLOAD: APIOperation[
    TestPostNoInputNoPayloadInput, TestPostNoInputNoPayloadOutput
]
TEST_POST_NO_PAYLOAD: APIOperation[TestPostNoPayloadInput, TestPostNoPayloadOutput]
TIMESTAMP_FORMAT_HEADERS: APIOperation[
    TimestampFormatHeadersInput, TimestampFormatHeadersOutput
]
UNIT_INPUT_AND_OUTPUT: APIOperation[UnitInputAndOutputInput, UnitInputAndOutputOutput]
