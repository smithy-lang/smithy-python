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
    "CONTENT_TYPE_PARAMETERS",
    "EMPTY_INPUT_AND_EMPTY_OUTPUT",
    "ENDPOINT_OPERATION",
    "ENDPOINT_WITH_HOST_LABEL_OPERATION",
    "GREETING_WITH_ERRORS",
    "HOST_WITH_PATH_OPERATION",
    "JSON_UNIONS",
    "NO_INPUT_AND_NO_OUTPUT",
    "NO_INPUT_AND_OUTPUT",
    "OPERATION_WITH_DEFAULTS",
    "OPERATION_WITH_NESTED_STRUCTURE",
    "OPERATION_WITH_REQUIRED_MEMBERS",
    "OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS",
    "PUT_WITH_CONTENT_ENCODING",
    "QUERY_INCOMPATIBLE_OPERATION",
    "SIMPLE_SCALAR_PROPERTIES",
    "ClientOptionalDefaults",
    "ComplexError",
    "ComplexNestedErrorData",
    "ContentTypeParametersInput",
    "ContentTypeParametersOutput",
    "Defaults",
    "Dialog",
    "EmptyInputAndEmptyOutputInput",
    "EmptyInputAndEmptyOutputOutput",
    "EndpointOperationInput",
    "EndpointOperationOutput",
    "EndpointWithHostLabelOperationInput",
    "EndpointWithHostLabelOperationOutput",
    "Farewell",
    "FooEnum",
    "FooError",
    "GreetingStruct",
    "GreetingWithErrorsInput",
    "GreetingWithErrorsOutput",
    "HostWithPathOperationInput",
    "HostWithPathOperationOutput",
    "IntegerEnum",
    "InvalidGreeting",
    "JsonUnionsInput",
    "JsonUnionsOutput",
    "MyUnion",
    "MyUnionBlobValue",
    "MyUnionBooleanValue",
    "MyUnionEnumValue",
    "MyUnionIntEnumValue",
    "MyUnionListValue",
    "MyUnionMapValue",
    "MyUnionNumberValue",
    "MyUnionStringValue",
    "MyUnionStructureValue",
    "MyUnionTimestampValue",
    "MyUnionUnknown",
    "NoInputAndNoOutputInput",
    "NoInputAndNoOutputOutput",
    "NoInputAndOutputInput",
    "NoInputAndOutputOutput",
    "OperationWithDefaultsInput",
    "OperationWithDefaultsOutput",
    "OperationWithNestedStructureInput",
    "OperationWithNestedStructureOutput",
    "OperationWithRequiredMembersInput",
    "OperationWithRequiredMembersOutput",
    "OperationWithRequiredMembersWithDefaultsInput",
    "OperationWithRequiredMembersWithDefaultsOutput",
    "PutWithContentEncodingInput",
    "PutWithContentEncodingOutput",
    "QueryIncompatibleOperationInput",
    "QueryIncompatibleOperationOutput",
    "RequiredEnum",
    "RequiredIntEnum",
    "ServiceError",
    "SimpleScalarPropertiesInput",
    "SimpleScalarPropertiesOutput",
    "TestEnum",
    "TestIntEnum",
    "TopLevel",
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
class ClientOptionalDefaults(_SerdeShape):
    "Dataclass for ClientOptionalDefaults structure."

    member: int | None = ...

class ClientOptionalDefaultsDict(TypedDict, total=False):
    "Dictionary form of `ClientOptionalDefaults`."

    member: int | None

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
class EndpointWithHostLabelOperationInput(_SerdeShape):
    "Dataclass for EndpointWithHostLabelOperationInput structure."

    label: str | None = ...

class EndpointWithHostLabelOperationInputDict(TypedDict, total=False):
    "Dictionary form of `EndpointWithHostLabelOperationInput`."

    label: Required[str]

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
class GreetingWithErrorsInput(_SerdeShape):
    "Dataclass for GreetingWithErrorsInput structure."

    greeting: str | None = ...

class GreetingWithErrorsInputDict(TypedDict, total=False):
    "Dictionary form of `GreetingWithErrorsInput`."

    greeting: str | None

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
class JsonUnionsInput(_SerdeShape):
    "Dataclass for JsonUnionsInput structure."

    contents: MyUnion | None = ...

class JsonUnionsInputDict(TypedDict, total=False):
    "Dictionary form of `JsonUnionsInput`."

    contents: MyUnion | MyUnionDict | None

@dataclass(kw_only=True)
class JsonUnionsOutput(_SerdeShape):
    "Dataclass for JsonUnionsOutput structure."

    contents: MyUnion | None = ...
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
class MyUnionIntEnumValue(_SerdeShape):
    value: int

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
    | MyUnionIntEnumValue
    | MyUnionListValue
    | MyUnionMapValue
    | MyUnionStructureValue
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

class MyUnionIntEnumValueDict(TypedDict):
    int_enum_value: int

class MyUnionListValueDict(TypedDict):
    list_value: Sequence[str]

class MyUnionMapValueDict(TypedDict):
    map_value: Mapping[str, str]

class MyUnionStructureValueDict(TypedDict):
    structure_value: GreetingStruct | GreetingStructDict

MyUnionDict = (
    MyUnionStringValueDict
    | MyUnionBooleanValueDict
    | MyUnionNumberValueDict
    | MyUnionBlobValueDict
    | MyUnionTimestampValueDict
    | MyUnionEnumValueDict
    | MyUnionIntEnumValueDict
    | MyUnionListValueDict
    | MyUnionMapValueDict
    | MyUnionStructureValueDict
)
"Dictionary form of `MyUnion`, setting exactly one variant."

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
class OperationWithRequiredMembersOutput(_SerdeShape):
    "Dataclass for OperationWithRequiredMembersOutput structure."

    required_string: str
    required_boolean: bool
    required_list: list[str]
    required_timestamp: datetime
    required_blob: bytes
    required_byte: int
    required_short: int
    required_integer: int
    required_long: int
    required_float: float
    required_double: float
    required_map: dict[str, str]
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class OperationWithRequiredMembersWithDefaultsOutput(_SerdeShape):
    "Dataclass for OperationWithRequiredMembersWithDefaultsOutput structure."

    required_string: str | None = ...
    required_boolean: bool | None = ...
    required_list: list[str] | None = ...
    required_timestamp: datetime | None = ...
    required_blob: bytes | None = ...
    required_byte: int | None = ...
    required_short: int | None = ...
    required_integer: int | None = ...
    required_long: int | None = ...
    required_float: float | None = ...
    required_double: float | None = ...
    required_map: dict[str, str] | None = ...
    required_enum: str | None = ...
    required_int_enum: int | None = ...
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

class RequiredEnum(UnknownEnumMixin, StrEnum):
    FOO = "FOO"
    BAR = "BAR"
    BAZ = "BAZ"

class RequiredIntEnum(UnknownEnumMixin, IntEnum):
    ONE = 1
    TWO = 2

@dataclass(kw_only=True)
class SimpleScalarPropertiesInput(_SerdeShape):
    "Dataclass for SimpleScalarPropertiesInput structure."

    float_value: float | None = ...
    double_value: float | None = ...

class SimpleScalarPropertiesInputDict(TypedDict, total=False):
    "Dictionary form of `SimpleScalarPropertiesInput`."

    float_value: float | None
    double_value: float | None

@dataclass(kw_only=True)
class SimpleScalarPropertiesOutput(_SerdeShape):
    "Dataclass for SimpleScalarPropertiesOutput structure."

    float_value: float | None = ...
    double_value: float | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

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
class OperationWithRequiredMembersInput(_SerdeShape):
    "Dataclass for OperationWithRequiredMembersInput structure."

class OperationWithRequiredMembersInputDict(TypedDict, total=False):
    "Dictionary form of `OperationWithRequiredMembersInput`."

@dataclass(kw_only=True)
class OperationWithRequiredMembersWithDefaultsInput(_SerdeShape):
    "Dataclass for OperationWithRequiredMembersWithDefaultsInput structure."

class OperationWithRequiredMembersWithDefaultsInputDict(TypedDict, total=False):
    "Dictionary form of `OperationWithRequiredMembersWithDefaultsInput`."

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
class QueryIncompatibleOperationInput(_SerdeShape):
    "Dataclass for QueryIncompatibleOperationInput structure."

class QueryIncompatibleOperationInputDict(TypedDict, total=False):
    "Dictionary form of `QueryIncompatibleOperationInput`."

@dataclass(kw_only=True)
class QueryIncompatibleOperationOutput(_SerdeShape):
    "Dataclass for QueryIncompatibleOperationOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

CONTENT_TYPE_PARAMETERS: APIOperation[
    ContentTypeParametersInput, ContentTypeParametersOutput
]
EMPTY_INPUT_AND_EMPTY_OUTPUT: APIOperation[
    EmptyInputAndEmptyOutputInput, EmptyInputAndEmptyOutputOutput
]
ENDPOINT_OPERATION: APIOperation[EndpointOperationInput, EndpointOperationOutput]
ENDPOINT_WITH_HOST_LABEL_OPERATION: APIOperation[
    EndpointWithHostLabelOperationInput, EndpointWithHostLabelOperationOutput
]
GREETING_WITH_ERRORS: APIOperation[GreetingWithErrorsInput, GreetingWithErrorsOutput]
HOST_WITH_PATH_OPERATION: APIOperation[
    HostWithPathOperationInput, HostWithPathOperationOutput
]
JSON_UNIONS: APIOperation[JsonUnionsInput, JsonUnionsOutput]
NO_INPUT_AND_NO_OUTPUT: APIOperation[NoInputAndNoOutputInput, NoInputAndNoOutputOutput]
NO_INPUT_AND_OUTPUT: APIOperation[NoInputAndOutputInput, NoInputAndOutputOutput]
OPERATION_WITH_DEFAULTS: APIOperation[
    OperationWithDefaultsInput, OperationWithDefaultsOutput
]
OPERATION_WITH_NESTED_STRUCTURE: APIOperation[
    OperationWithNestedStructureInput, OperationWithNestedStructureOutput
]
OPERATION_WITH_REQUIRED_MEMBERS: APIOperation[
    OperationWithRequiredMembersInput, OperationWithRequiredMembersOutput
]
OPERATION_WITH_REQUIRED_MEMBERS_WITH_DEFAULTS: APIOperation[
    OperationWithRequiredMembersWithDefaultsInput,
    OperationWithRequiredMembersWithDefaultsOutput,
]
PUT_WITH_CONTENT_ENCODING: APIOperation[
    PutWithContentEncodingInput, PutWithContentEncodingOutput
]
QUERY_INCOMPATIBLE_OPERATION: APIOperation[
    QueryIncompatibleOperationInput, QueryIncompatibleOperationOutput
]
SIMPLE_SCALAR_PROPERTIES: APIOperation[
    SimpleScalarPropertiesInput, SimpleScalarPropertiesOutput
]
