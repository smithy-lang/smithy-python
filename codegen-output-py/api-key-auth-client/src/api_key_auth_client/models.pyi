from dataclasses import dataclass
from typing import Self, TypedDict

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import ModeledError
from smithy_core.response import ResponseMetadata
from smithy_core.schemas import APIOperation
from smithy_core.serializers import ShapeSerializer

__all__ = [
    "GET_THING",
    "HEALTH",
    "PING",
    "GetThingInput",
    "GetThingOutput",
    "HealthInput",
    "HealthOutput",
    "PingInput",
    "PingOutput",
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
class GetThingInput(_SerdeShape):
    "Dataclass for GetThingInput structure."

    name: str | None = ...

class GetThingInputDict(TypedDict, total=False):
    "Dictionary form of `GetThingInput`."

    name: str | None

@dataclass(kw_only=True)
class GetThingOutput(_SerdeShape):
    "Dataclass for GetThingOutput structure."

    value: str | None = ...
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

@dataclass(kw_only=True)
class PingInput(_SerdeShape):
    "Dataclass for PingInput structure."

class PingInputDict(TypedDict, total=False):
    "Dictionary form of `PingInput`."

@dataclass(kw_only=True)
class PingOutput(_SerdeShape):
    "Dataclass for PingOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

GET_THING: APIOperation[GetThingInput, GetThingOutput]
HEALTH: APIOperation[HealthInput, HealthOutput]
PING: APIOperation[PingInput, PingOutput]
