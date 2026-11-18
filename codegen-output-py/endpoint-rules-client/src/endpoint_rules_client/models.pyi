from collections.abc import Sequence
from dataclasses import dataclass
from typing import Required, Self, TypedDict

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import ModeledError
from smithy_core.response import ResponseMetadata
from smithy_core.schemas import APIOperation
from smithy_core.serializers import ShapeSerializer

__all__ = [
    "PING",
    "PUT_THING",
    "PingInput",
    "PingOutput",
    "PutThingInput",
    "PutThingOutput",
    "ServiceError",
    "ThingTag",
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
class PutThingInput(_SerdeShape):
    "Dataclass for PutThingInput structure."

    name: str | None = ...
    tag: ThingTag | None = ...
    plugins_: list[str] | None = ...

class PutThingInputDict(TypedDict, total=False):
    "Dictionary form of `PutThingInput`."

    name: Required[str]
    tag: ThingTag | ThingTagDict | None
    plugins_: Sequence[str] | None

@dataclass(kw_only=True)
class ThingTag(_SerdeShape):
    "Dataclass for ThingTag structure."

    key: str | None = ...
    value: str | None = ...

class ThingTagDict(TypedDict, total=False):
    "Dictionary form of `ThingTag`."

    key: str | None
    value: str | None

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

@dataclass(kw_only=True)
class PutThingOutput(_SerdeShape):
    "Dataclass for PutThingOutput structure."

    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

PING: APIOperation[PingInput, PingOutput]
PUT_THING: APIOperation[PutThingInput, PutThingOutput]
