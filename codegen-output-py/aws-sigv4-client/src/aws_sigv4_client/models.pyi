from dataclasses import dataclass
from typing import Self, TypedDict

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import ModeledError
from smithy_core.response import ResponseMetadata
from smithy_core.schemas import APIOperation
from smithy_core.serializers import ShapeSerializer

__all__ = [
    "HEALTH",
    "PUT_NOTE",
    "HealthInput",
    "HealthOutput",
    "PutNoteInput",
    "PutNoteOutput",
    "ServiceError",
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
class PutNoteInput(_SerdeShape):
    "Dataclass for PutNoteInput structure."

    text: str | None = ...

class PutNoteInputDict(TypedDict, total=False):
    "Dictionary form of `PutNoteInput`."

    text: str | None

@dataclass(kw_only=True)
class PutNoteOutput(_SerdeShape):
    "Dataclass for PutNoteOutput structure."

    id: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class HealthInput(_SerdeShape):
    "Dataclass for HealthInput structure."

class HealthInputDict(TypedDict, total=False):
    "Dictionary form of `HealthInput`."

@dataclass(kw_only=True)
class HealthOutput(_SerdeShape):
    "Dataclass for HealthOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

HEALTH: APIOperation[HealthInput, HealthOutput]
PUT_NOTE: APIOperation[PutNoteInput, PutNoteOutput]
