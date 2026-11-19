from dataclasses import dataclass
from typing import Self, TypedDict

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import ModeledError
from smithy_core.response import ResponseMetadata
from smithy_core.schemas import APIOperation
from smithy_core.serializers import ShapeSerializer

__all__ = [
    "GET_FORECAST",
    "GetForecastInput",
    "GetForecastOutput",
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
class GetForecastInput(_SerdeShape):
    "Dataclass for GetForecastInput structure."

    city: str | None = ...

class GetForecastInputDict(TypedDict, total=False):
    "Dictionary form of `GetForecastInput`."

    city: str | None

@dataclass(kw_only=True)
class GetForecastOutput(_SerdeShape):
    "Dataclass for GetForecastOutput structure."

    summary: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

GET_FORECAST: APIOperation[GetForecastInput, GetForecastOutput]
