from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Required, Self, TypedDict

from smithy_core.deserializers import ShapeDeserializer
from smithy_core.exceptions import ModeledError
from smithy_core.response import ErrorResponseMetadata, ResponseMetadata
from smithy_core.schemas import APIOperation
from smithy_core.serializers import ShapeSerializer
from smithy_core.types import UnknownEnumMixin

__all__ = [
    "DESCRIBE_NOTE",
    "ECHO",
    "GET_NOTE",
    "GET_THING",
    "LIST_NOTES",
    "PING",
    "PUT_NOTE",
    "PUT_THING",
    "ChecksumAlgorithm",
    "ChecksumMode",
    "DescribeNoteInput",
    "DescribeNoteOutput",
    "EchoInput",
    "EchoOutput",
    "GetNoteInput",
    "GetNoteOutput",
    "GetThingInput",
    "GetThingOutput",
    "ListNotesInput",
    "ListNotesOutput",
    "NoteNotFound",
    "NoteState",
    "PingInput",
    "PingOutput",
    "PutNoteInput",
    "PutNoteOutput",
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

class ChecksumAlgorithm(UnknownEnumMixin, StrEnum):
    CRC32 = "CRC32"
    SHA256 = "SHA256"

class ChecksumMode(UnknownEnumMixin, StrEnum):
    ENABLED = "ENABLED"

@dataclass(kw_only=True)
class DescribeNoteInput(_SerdeShape):
    "Dataclass for DescribeNoteInput structure."

    id: str | None = ...

class DescribeNoteInputDict(TypedDict, total=False):
    "Dictionary form of `DescribeNoteInput`."

    id: Required[str]

@dataclass(kw_only=True)
class DescribeNoteOutput(_SerdeShape):
    "Dataclass for DescribeNoteOutput structure."

    id: str | None = ...
    state: str | None = ...
    reason: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class GetNoteInput(_SerdeShape):
    "Dataclass for GetNoteInput structure."

    id: str | None = ...
    checksum_mode: str | None = ...

class GetNoteInputDict(TypedDict, total=False):
    "Dictionary form of `GetNoteInput`."

    id: str | None
    checksum_mode: str | None

@dataclass(kw_only=True)
class GetNoteOutput(_SerdeShape):
    "Dataclass for GetNoteOutput structure."

    text: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
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
class ListNotesInput(_SerdeShape):
    "Dataclass for ListNotesInput structure."

    next_token: str | None = ...
    page_size: int | None = ...

class ListNotesInputDict(TypedDict, total=False):
    "Dictionary form of `ListNotesInput`."

    next_token: str | None
    page_size: int | None

@dataclass(kw_only=True)
class ListNotesOutput(_SerdeShape):
    "Dataclass for ListNotesOutput structure."

    items: list[str] | None = ...
    next_token: str | None = ...
    response_metadata: ResponseMetadata = ...
    """
    Metadata about the response that produced this output.

    Use this to recover the request identifiers a service's support team
    needs in order to investigate a call. Members of the metadata are
    individually optional.
    """

@dataclass(kw_only=True)
class NoteNotFound(ServiceError, _SerdeShape):
    "Dataclass for NoteNotFound structure."

    response_metadata: ErrorResponseMetadata = ...
    """
    Metadata about the response that produced this error.

    Use this to read the error code or to recover the request identifiers a
    service's support team needs in order to investigate a call. Members of
    the metadata are individually optional.
    """

class NoteState(UnknownEnumMixin, StrEnum):
    DRAFT = "DRAFT"
    SAVED = "SAVED"
    REJECTED = "REJECTED"

@dataclass(kw_only=True)
class PutNoteInput(_SerdeShape):
    "Dataclass for PutNoteInput structure."

    text: str | None = ...
    checksum_algorithm: str | None = ...

class PutNoteInputDict(TypedDict, total=False):
    "Dictionary form of `PutNoteInput`."

    text: str | None
    checksum_algorithm: str | None

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
class EchoInput(_SerdeShape):
    "Dataclass for EchoInput structure."

class EchoInputDict(TypedDict, total=False):
    "Dictionary form of `EchoInput`."

@dataclass(kw_only=True)
class EchoOutput(_SerdeShape):
    "Dataclass for EchoOutput structure."

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

DESCRIBE_NOTE: APIOperation[DescribeNoteInput, DescribeNoteOutput]
ECHO: APIOperation[EchoInput, EchoOutput]
GET_NOTE: APIOperation[GetNoteInput, GetNoteOutput]
GET_THING: APIOperation[GetThingInput, GetThingOutput]
LIST_NOTES: APIOperation[ListNotesInput, ListNotesOutput]
PING: APIOperation[PingInput, PingOutput]
PUT_NOTE: APIOperation[PutNoteInput, PutNoteOutput]
PUT_THING: APIOperation[PutThingInput, PutThingOutput]
