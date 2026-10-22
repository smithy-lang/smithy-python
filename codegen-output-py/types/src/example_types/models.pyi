from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Self

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.documents import Document
from smithy_core.exceptions import ModeledError
from smithy_core.response import ResponseMetadata
from smithy_core.serializers import ShapeSerializer
from smithy_core.types import UnknownEnumMixin

__all__ = [
    "Code",
    "ExampleError",
    "ExampleValue",
    "ExampleValueEmpty",
    "ExampleValueNumber",
    "ExampleValueText",
    "ExampleValueUnknown",
    "GetExampleInput",
    "GetExampleOutput",
    "RenamedExample",
    "ServiceError",
    "Status",
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
class GetExampleInput(_SerdeShape):
    "Input for retrieving an example."

    id: str | None = ...

@dataclass(kw_only=True)
class GetExampleOutput(_SerdeShape):
    "Dataclass for GetExampleOutput structure."

    example: RenamedExample | None = ...
    value: ExampleValue | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class ExampleError(ServiceError, _SerdeShape):
    "An example modeled error."

    retry_after_seconds: int | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class RenamedExample(_SerdeShape):
    "A representative generated structure."

    name: str
    "The example name."
    count: int | None = ...
    tags: list[str] | None = ...
    attributes: dict[str, Document] | None = ...
    choice: ExampleValue | None = ...
    status: str | None = ...
    code: int | None = ...

@dataclass
class ExampleValueText(_SerdeShape):
    value: str

@dataclass
class ExampleValueNumber(_SerdeShape):
    value: int

@dataclass
class ExampleValueEmpty(_SerdeShape):
    value: Unit

@dataclass
class ExampleValueUnknown(_SerdeShape):
    """
    Represents an unknown variant.

    If you receive this value, you will need to update your library to
    receive the parsed value.

    This value may not be deliberately sent.
    """

    tag: str

ExampleValue = (
    ExampleValueText | ExampleValueNumber | ExampleValueEmpty | ExampleValueUnknown
)
"A representative generated union."

class _ExampleValueDeserializer:
    def deserialize(self, deserializer: ShapeDeserializer) -> ExampleValue: ...

class Status(UnknownEnumMixin, StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Code(UnknownEnumMixin, IntEnum):
    OK = 200
    NOT_FOUND = 404

@dataclass(kw_only=True)
class Unit(_SerdeShape):
    pass
