from dataclasses import dataclass
from typing import Self, TypedDict

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import ModeledError
from smithy_core.response import ErrorResponseMetadata, ResponseMetadata
from smithy_core.schemas import APIOperation
from smithy_core.serializers import ShapeSerializer

__all__ = [
    "QUERY_COMPATIBLE_OPERATION",
    "CustomCodeError",
    "NoCustomCodeError",
    "QueryCompatibleOperationInput",
    "QueryCompatibleOperationOutput",
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
class CustomCodeError(ServiceError, _SerdeShape):
    "Dataclass for CustomCodeError structure."

    response_metadata: ErrorResponseMetadata = ...
    """
    Metadata about the response that produced this error.

    Use this to read the error code or to recover the request identifiers a
    service's support team needs in order to investigate a call. Members of
    the metadata are individually optional.
    """

@dataclass(kw_only=True)
class NoCustomCodeError(ServiceError, _SerdeShape):
    "Dataclass for NoCustomCodeError structure."

    response_metadata: ErrorResponseMetadata = ...
    """
    Metadata about the response that produced this error.

    Use this to read the error code or to recover the request identifiers a
    service's support team needs in order to investigate a call. Members of
    the metadata are individually optional.
    """

@dataclass(kw_only=True)
class QueryCompatibleOperationInput(_SerdeShape):
    "Dataclass for QueryCompatibleOperationInput structure."

class QueryCompatibleOperationInputDict(TypedDict, total=False):
    "Dictionary form of `QueryCompatibleOperationInput`."

@dataclass(kw_only=True)
class QueryCompatibleOperationOutput(_SerdeShape):
    "Dataclass for QueryCompatibleOperationOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

QUERY_COMPATIBLE_OPERATION: APIOperation[
    QueryCompatibleOperationInput, QueryCompatibleOperationOutput
]
