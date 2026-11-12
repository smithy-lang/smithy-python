from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import IntEnum, StrEnum
from typing import Self

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import ModeledError
from smithy_core.response import ResponseMetadata
from smithy_core.serializers import ShapeSerializer
from smithy_core.types import UnknownEnumMixin

__all__ = [
    "BigDecimalStructure",
    "BigIntegerStructure",
    "ClientOptionalDefaults",
    "ComplexError",
    "ComplexNestedErrorData",
    "Defaults",
    "EmptyStructure",
    "FooEnum",
    "FractionalSecondsOutput",
    "GreetingStruct",
    "GreetingWithErrorsOutput",
    "IntegerEnum",
    "InvalidGreeting",
    "OperationWithDefaultsInput",
    "OperationWithDefaultsOutput",
    "RecursiveShapesInputOutput",
    "RecursiveShapesInputOutputNested1",
    "RecursiveShapesInputOutputNested2",
    "RpcV2JsonDenseMapsInputOutput",
    "RpcV2JsonListInputOutput",
    "RpcV2JsonSparseMapsInputOutput",
    "ServiceError",
    "SimpleScalarStructure",
    "SimpleStructure",
    "SparseNullsOperationInputOutput",
    "StructureListMember",
    "TestEnum",
    "TestIntEnum",
    "TimestampFormatIgnoredIO",
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
class BigDecimalStructure(_SerdeShape):
    "Dataclass for BigDecimalStructure structure."

    value: Decimal | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class BigIntegerStructure(_SerdeShape):
    "Dataclass for BigIntegerStructure structure."

    value: int | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ClientOptionalDefaults(_SerdeShape):
    "Dataclass for ClientOptionalDefaults structure."

    member: int | None = ...

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

@dataclass(kw_only=True)
class EmptyStructure(_SerdeShape):
    "Dataclass for EmptyStructure structure."

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
class RpcV2JsonDenseMapsInputOutput(_SerdeShape):
    "Dataclass for RpcV2JsonDenseMapsInputOutput structure."

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
class RpcV2JsonListInputOutput(_SerdeShape):
    "Dataclass for RpcV2JsonListInputOutput structure."

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
class RpcV2JsonSparseMapsInputOutput(_SerdeShape):
    "Dataclass for RpcV2JsonSparseMapsInputOutput structure."

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
class SimpleScalarStructure(_SerdeShape):
    "Dataclass for SimpleScalarStructure structure."

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
class SimpleStructure(_SerdeShape):
    "Dataclass for SimpleStructure structure."

    value: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class SparseNullsOperationInputOutput(_SerdeShape):
    "Dataclass for SparseNullsOperationInputOutput structure."

    sparse_string_list: list[str | None] | None = ...
    sparse_string_map: dict[str, str | None] | None = ...
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

class TestEnum(UnknownEnumMixin, StrEnum):
    FOO = "FOO"
    BAR = "BAR"
    BAZ = "BAZ"

class TestIntEnum(UnknownEnumMixin, IntEnum):
    ONE = 1
    TWO = 2

@dataclass(kw_only=True)
class TimestampFormatIgnoredIO(_SerdeShape):
    "Dataclass for TimestampFormatIgnoredIO structure."

    date_time: datetime | None = ...
    http_date: datetime | None = ...
    epoch_seconds: datetime | None = ...
    normal: datetime | None = ...
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
