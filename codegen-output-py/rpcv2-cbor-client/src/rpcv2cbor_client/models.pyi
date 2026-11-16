from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Self, TypedDict

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import ModeledError
from smithy_core.response import ResponseMetadata
from smithy_core.schemas import APIOperation
from smithy_core.serializers import ShapeSerializer
from smithy_core.types import UnknownEnumMixin

__all__ = [
    "EMPTY_INPUT_OUTPUT",
    "FLOAT16",
    "FRACTIONAL_SECONDS",
    "GREETING_WITH_ERRORS",
    "NO_INPUT_OUTPUT",
    "OPERATION_WITH_DEFAULTS",
    "OPTIONAL_INPUT_OUTPUT",
    "RECURSIVE_SHAPES",
    "RPC_V2_CBOR_DENSE_MAPS",
    "RPC_V2_CBOR_LISTS",
    "RPC_V2_CBOR_SPARSE_MAPS",
    "RPC_V2_CBOR_UNIONS",
    "SIMPLE_SCALAR_PROPERTIES",
    "SPARSE_NULLS_OPERATION",
    "ClientOptionalDefaults",
    "ComplexError",
    "ComplexNestedErrorData",
    "Defaults",
    "EmptyInputOutputInput",
    "EmptyInputOutputOutput",
    "Float16Input",
    "Float16Output",
    "FooEnum",
    "FractionalSecondsInput",
    "FractionalSecondsOutput",
    "GreetingStruct",
    "GreetingWithErrorsInput",
    "GreetingWithErrorsOutput",
    "IntegerEnum",
    "InvalidGreeting",
    "NoInputOutputInput",
    "NoInputOutputOutput",
    "OperationWithDefaultsInput",
    "OperationWithDefaultsOutput",
    "OptionalInputOutputInput",
    "OptionalInputOutputOutput",
    "RecursiveShapesInput",
    "RecursiveShapesInputOutputNested1",
    "RecursiveShapesInputOutputNested2",
    "RecursiveShapesOutput",
    "RpcV2CborDenseMapsInput",
    "RpcV2CborDenseMapsOutput",
    "RpcV2CborListsInput",
    "RpcV2CborListsOutput",
    "RpcV2CborNestedUnion",
    "RpcV2CborNestedUnionStringValue",
    "RpcV2CborNestedUnionUnknown",
    "RpcV2CborSparseMapsInput",
    "RpcV2CborSparseMapsOutput",
    "RpcV2CborUnion",
    "RpcV2CborUnionStringValue",
    "RpcV2CborUnionUnionValue",
    "RpcV2CborUnionUnknown",
    "RpcV2CborUnionsInput",
    "RpcV2CborUnionsOutput",
    "ServiceError",
    "SimpleScalarPropertiesInput",
    "SimpleScalarPropertiesOutput",
    "SparseNullsOperationInput",
    "SparseNullsOperationOutput",
    "StructureListMember",
    "TestEnum",
    "TestIntEnum",
    "ValidationException",
    "ValidationExceptionField",
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
class ValidationException(ServiceError, _SerdeShape):
    """
    A standard error for input validation failures.
    This should be thrown by services when a member of the input structure
    falls outside of the modeled or documented constraints.
    """

    field_list: list[ValidationExceptionField] | None = ...
    """
    A list of specific failures encountered while validating the input.
    A member can appear in this list more than once if it failed to satisfy
    multiple constraints.
    """
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ValidationExceptionField(_SerdeShape):
    "Describes one specific validation failure for an input member."

    path: str
    """
    A JSONPointer expression to the structure member whose value failed to
    satisfy the modeled constraints.
    """
    message: str
    "A detailed description of the validation failure."

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
class Defaults(_SerdeShape):
    "Dataclass for Defaults structure."

    default_string: str | None = ...
    default_boolean: bool | None = ...
    default_list: list[str] | None = ...
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
class Float16Output(_SerdeShape):
    "Dataclass for Float16Output structure."

    value: float | None = ...
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

@dataclass
class RpcV2CborNestedUnionStringValue(_SerdeShape):
    value: str

@dataclass
class RpcV2CborNestedUnionUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

RpcV2CborNestedUnion = RpcV2CborNestedUnionStringValue | RpcV2CborNestedUnionUnknown

class _RpcV2CborNestedUnionDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> RpcV2CborNestedUnion: ...

class RpcV2CborNestedUnionStringValueDict(TypedDict):
    string_value: str

RpcV2CborNestedUnionDict = RpcV2CborNestedUnionStringValueDict
"Dictionary form of `RpcV2CborNestedUnion`, setting exactly one variant."

@dataclass
class RpcV2CborUnionStringValue(_SerdeShape):
    value: str

@dataclass
class RpcV2CborUnionUnionValue(_SerdeShape):
    value: RpcV2CborNestedUnion

@dataclass
class RpcV2CborUnionUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

RpcV2CborUnion = (
    RpcV2CborUnionStringValue | RpcV2CborUnionUnionValue | RpcV2CborUnionUnknown
)

class _RpcV2CborUnionDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> RpcV2CborUnion: ...

class RpcV2CborUnionStringValueDict(TypedDict):
    string_value: str

class RpcV2CborUnionUnionValueDict(TypedDict):
    union_value: RpcV2CborNestedUnion | RpcV2CborNestedUnionDict

RpcV2CborUnionDict = RpcV2CborUnionStringValueDict | RpcV2CborUnionUnionValueDict
"Dictionary form of `RpcV2CborUnion`, setting exactly one variant."

@dataclass(kw_only=True)
class StructureListMember(_SerdeShape):
    "Dataclass for StructureListMember structure."

    a: str | None = ...
    b: str | None = ...

class StructureListMemberDict(TypedDict, total=False):
    "Dictionary form of `StructureListMember`."

    a: str | None
    b: str | None

class TestEnum(UnknownEnumMixin, StrEnum):
    FOO = "FOO"
    BAR = "BAR"
    BAZ = "BAZ"

class TestIntEnum(UnknownEnumMixin, IntEnum):
    ONE = 1
    TWO = 2

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
class EmptyInputOutputInput(_SerdeShape):
    "Dataclass for EmptyInputOutputInput structure."

class EmptyInputOutputInputDict(TypedDict, total=False):
    "Dictionary form of `EmptyInputOutputInput`."

@dataclass(kw_only=True)
class EmptyInputOutputOutput(_SerdeShape):
    "Dataclass for EmptyInputOutputOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class Float16Input(_SerdeShape):
    "Dataclass for Float16Input structure."

class Float16InputDict(TypedDict, total=False):
    "Dictionary form of `Float16Input`."

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
class NoInputOutputInput(_SerdeShape):
    "Dataclass for NoInputOutputInput structure."

class NoInputOutputInputDict(TypedDict, total=False):
    "Dictionary form of `NoInputOutputInput`."

@dataclass(kw_only=True)
class NoInputOutputOutput(_SerdeShape):
    "Dataclass for NoInputOutputOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class OptionalInputOutputInput(_SerdeShape):
    "Dataclass for OptionalInputOutputInput structure."

    value: str | None = ...

class OptionalInputOutputInputDict(TypedDict, total=False):
    "Dictionary form of `OptionalInputOutputInput`."

    value: str | None

@dataclass(kw_only=True)
class OptionalInputOutputOutput(_SerdeShape):
    "Dataclass for OptionalInputOutputOutput structure."

    value: str | None = ...
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
class RpcV2CborDenseMapsInput(_SerdeShape):
    "Dataclass for RpcV2CborDenseMapsInput structure."

    dense_struct_map: dict[str, GreetingStruct] | None = ...
    dense_number_map: dict[str, int] | None = ...
    dense_boolean_map: dict[str, bool] | None = ...
    dense_string_map: dict[str, str] | None = ...
    dense_set_map: dict[str, list[str]] | None = ...

class RpcV2CborDenseMapsInputDict(TypedDict, total=False):
    "Dictionary form of `RpcV2CborDenseMapsInput`."

    dense_struct_map: Mapping[str, GreetingStruct | GreetingStructDict] | None
    dense_number_map: Mapping[str, int] | None
    dense_boolean_map: Mapping[str, bool] | None
    dense_string_map: Mapping[str, str] | None
    dense_set_map: Mapping[str, Sequence[str]] | None

@dataclass(kw_only=True)
class RpcV2CborDenseMapsOutput(_SerdeShape):
    "Dataclass for RpcV2CborDenseMapsOutput structure."

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
class RpcV2CborListsInput(_SerdeShape):
    "Dataclass for RpcV2CborListsInput structure."

    string_list: list[str] | None = ...
    string_set: list[str] | None = ...
    integer_list: list[int] | None = ...
    boolean_list: list[bool] | None = ...
    timestamp_list: list[datetime] | None = ...
    enum_list: list[str] | None = ...
    int_enum_list: list[int] | None = ...
    nested_string_list: list[list[str]] | None = ...
    structure_list: list[StructureListMember] | None = ...
    blob_list: list[bytes] | None = ...

class RpcV2CborListsInputDict(TypedDict, total=False):
    "Dictionary form of `RpcV2CborListsInput`."

    string_list: Sequence[str] | None
    string_set: Sequence[str] | None
    integer_list: Sequence[int] | None
    boolean_list: Sequence[bool] | None
    timestamp_list: Sequence[datetime] | None
    enum_list: Sequence[str] | None
    int_enum_list: Sequence[int] | None
    nested_string_list: Sequence[Sequence[str]] | None
    structure_list: Sequence[StructureListMember | StructureListMemberDict] | None
    blob_list: Sequence[bytes] | None

@dataclass(kw_only=True)
class RpcV2CborListsOutput(_SerdeShape):
    "Dataclass for RpcV2CborListsOutput structure."

    string_list: list[str] | None = ...
    string_set: list[str] | None = ...
    integer_list: list[int] | None = ...
    boolean_list: list[bool] | None = ...
    timestamp_list: list[datetime] | None = ...
    enum_list: list[str] | None = ...
    int_enum_list: list[int] | None = ...
    nested_string_list: list[list[str]] | None = ...
    structure_list: list[StructureListMember] | None = ...
    blob_list: list[bytes] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class RpcV2CborSparseMapsInput(_SerdeShape):
    "Dataclass for RpcV2CborSparseMapsInput structure."

    sparse_struct_map: dict[str, GreetingStruct | None] | None = ...
    sparse_number_map: dict[str, int | None] | None = ...
    sparse_boolean_map: dict[str, bool | None] | None = ...
    sparse_string_map: dict[str, str | None] | None = ...
    sparse_set_map: dict[str, list[str] | None] | None = ...

class RpcV2CborSparseMapsInputDict(TypedDict, total=False):
    "Dictionary form of `RpcV2CborSparseMapsInput`."

    sparse_struct_map: Mapping[str, GreetingStruct | GreetingStructDict | None] | None
    sparse_number_map: Mapping[str, int | None] | None
    sparse_boolean_map: Mapping[str, bool | None] | None
    sparse_string_map: Mapping[str, str | None] | None
    sparse_set_map: Mapping[str, Sequence[str] | None] | None

@dataclass(kw_only=True)
class RpcV2CborSparseMapsOutput(_SerdeShape):
    "Dataclass for RpcV2CborSparseMapsOutput structure."

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
class RpcV2CborUnionsInput(_SerdeShape):
    "Dataclass for RpcV2CborUnionsInput structure."

    contents: RpcV2CborUnion | None = ...
    other_value: str | None = ...

class RpcV2CborUnionsInputDict(TypedDict, total=False):
    "Dictionary form of `RpcV2CborUnionsInput`."

    contents: RpcV2CborUnion | RpcV2CborUnionDict | None
    other_value: str | None

@dataclass(kw_only=True)
class RpcV2CborUnionsOutput(_SerdeShape):
    "Dataclass for RpcV2CborUnionsOutput structure."

    contents: RpcV2CborUnion | None = ...
    other_value: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class SimpleScalarPropertiesInput(_SerdeShape):
    "Dataclass for SimpleScalarPropertiesInput structure."

    true_boolean_value: bool | None = ...
    false_boolean_value: bool | None = ...
    byte_value: int | None = ...
    double_value: float | None = ...
    float_value: float | None = ...
    integer_value: int | None = ...
    long_value: int | None = ...
    short_value: int | None = ...
    string_value: str | None = ...
    blob_value: bytes | None = ...

class SimpleScalarPropertiesInputDict(TypedDict, total=False):
    "Dictionary form of `SimpleScalarPropertiesInput`."

    true_boolean_value: bool | None
    false_boolean_value: bool | None
    byte_value: int | None
    double_value: float | None
    float_value: float | None
    integer_value: int | None
    long_value: int | None
    short_value: int | None
    string_value: str | None
    blob_value: bytes | None

@dataclass(kw_only=True)
class SimpleScalarPropertiesOutput(_SerdeShape):
    "Dataclass for SimpleScalarPropertiesOutput structure."

    true_boolean_value: bool | None = ...
    false_boolean_value: bool | None = ...
    byte_value: int | None = ...
    double_value: float | None = ...
    float_value: float | None = ...
    integer_value: int | None = ...
    long_value: int | None = ...
    short_value: int | None = ...
    string_value: str | None = ...
    blob_value: bytes | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class SparseNullsOperationInput(_SerdeShape):
    "Dataclass for SparseNullsOperationInput structure."

    sparse_string_list: list[str | None] | None = ...
    sparse_string_map: dict[str, str | None] | None = ...

class SparseNullsOperationInputDict(TypedDict, total=False):
    "Dictionary form of `SparseNullsOperationInput`."

    sparse_string_list: Sequence[str | None] | None
    sparse_string_map: Mapping[str, str | None] | None

@dataclass(kw_only=True)
class SparseNullsOperationOutput(_SerdeShape):
    "Dataclass for SparseNullsOperationOutput structure."

    sparse_string_list: list[str | None] | None = ...
    sparse_string_map: dict[str, str | None] | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

EMPTY_INPUT_OUTPUT: APIOperation[EmptyInputOutputInput, EmptyInputOutputOutput]
FLOAT16: APIOperation[Float16Input, Float16Output]
FRACTIONAL_SECONDS: APIOperation[FractionalSecondsInput, FractionalSecondsOutput]
GREETING_WITH_ERRORS: APIOperation[GreetingWithErrorsInput, GreetingWithErrorsOutput]
NO_INPUT_OUTPUT: APIOperation[NoInputOutputInput, NoInputOutputOutput]
OPERATION_WITH_DEFAULTS: APIOperation[
    OperationWithDefaultsInput, OperationWithDefaultsOutput
]
OPTIONAL_INPUT_OUTPUT: APIOperation[OptionalInputOutputInput, OptionalInputOutputOutput]
RECURSIVE_SHAPES: APIOperation[RecursiveShapesInput, RecursiveShapesOutput]
RPC_V2_CBOR_DENSE_MAPS: APIOperation[RpcV2CborDenseMapsInput, RpcV2CborDenseMapsOutput]
RPC_V2_CBOR_LISTS: APIOperation[RpcV2CborListsInput, RpcV2CborListsOutput]
RPC_V2_CBOR_SPARSE_MAPS: APIOperation[
    RpcV2CborSparseMapsInput, RpcV2CborSparseMapsOutput
]
RPC_V2_CBOR_UNIONS: APIOperation[RpcV2CborUnionsInput, RpcV2CborUnionsOutput]
SIMPLE_SCALAR_PROPERTIES: APIOperation[
    SimpleScalarPropertiesInput, SimpleScalarPropertiesOutput
]
SPARSE_NULLS_OPERATION: APIOperation[
    SparseNullsOperationInput, SparseNullsOperationOutput
]
