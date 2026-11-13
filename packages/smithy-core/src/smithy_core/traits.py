#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# This ruff check warns against using the assert statement, which can be stripped out
# when running Python with certain (common) optimization settings. Assert is used here
# for trait values. Since these are always generated, we can be fairly confident that
# they're correct regardless, so it's okay if the checks are stripped out.
# ruff: noqa: S101

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from .shapes import ShapeID
from .types import PathPattern, TimestampFormat

if TYPE_CHECKING:
    from .documents import DocumentValue


__all__ = [
    "ORIGINAL_SHAPE_ID",
    "APIKeyLocation",
    "ContextParamTrait",
    "DefaultTrait",
    "DynamicTrait",
    "EndpointTrait",
    "EnumValueTrait",
    "ErrorFault",
    "ErrorTrait",
    "EventHeaderTrait",
    "EventPayloadTrait",
    "HTTPAPIKeyAuthTrait",
    "HTTPChecksumRequiredTrait",
    "HTTPErrorTrait",
    "HTTPHeaderTrait",
    "HTTPLabelTrait",
    "HTTPPayloadTrait",
    "HTTPPrefixHeadersTrait",
    "HTTPQueryParamsTrait",
    "HTTPQueryTrait",
    "HTTPResponseCodeTrait",
    "HTTPTrait",
    "HostLabelTrait",
    "IdempotencyTokenTrait",
    "InternalTrait",
    "JSONNameTrait",
    "LongPollTrait",
    "MediaTypeTrait",
    "OperationContextParamsTrait",
    "RequiredTrait",
    "RequiresLengthTrait",
    "RpcV2CborTrait",
    "RpcV2JsonTrait",
    "SensitiveTrait",
    "SparseTrait",
    "StaticContextParamsTrait",
    "StreamingTrait",
    "TimestampFormatTrait",
    "Trait",
    "UnitTypeTrait",
    "XMLAttributeTrait",
    "XMLFlattenedTrait",
    "XMLNameTrait",
    "XMLNamespaceTrait",
]


@dataclass(kw_only=True, frozen=True, slots=True)
class DynamicTrait:
    """A component that can be attached to a schema to describe additional information
    about it.

    Typed traits can be used by creating a :py:class:`Trait` subclass.
    """

    id: ShapeID
    """The ID of the trait."""

    document_value: "DocumentValue" = None
    """The value of the trait."""


ORIGINAL_SHAPE_ID = ShapeID("smithy.synthetic#originalShapeId")
"""A DynamicTrait id that indicates a structure was originally something else, usually Unit."""


@dataclass(init=False, frozen=True)
class Trait:
    """A component that can be attached to a schema to describe additional information
    about it.

    This is a base class that registers subclasses. Any known subclasses will
    automatically be used when constructing schemas. Any unknown traits may instead be
    created as a :py:class:`DynamicTrait`.

    The `id` property of subclasses is set during subclass creation by
    `__init_subclass__`, so it is not necessary for subclasses to set it manually.
    """

    _REGISTRY: ClassVar[dict[ShapeID, type["Trait"]]] = {}

    id: ClassVar[ShapeID]
    """The ID of the trait."""

    document_value: "DocumentValue" = None
    """The value of the trait as a DocumentValue."""

    def __init_subclass__(cls, id: ShapeID) -> None:
        cls.id = id
        Trait._REGISTRY[id] = cls

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        if type(self) is Trait:
            raise TypeError(
                "Only subclasses of Trait may be directly instantiated. "
                "Use DynamicTrait for traits without a concrete class."
            )

        if isinstance(value, DynamicTrait):
            if value.id != self.id:
                raise ValueError(
                    f"Attempted to instantiate an instance of {type(self)} from an "
                    f"invalid ID. Expected {self.id} but found {value.id}."
                )
            # Note that setattr is needed because it's a frozen (read-only) dataclass
            object.__setattr__(self, "document_value", value.document_value)
        else:
            object.__setattr__(self, "document_value", value)

    # Dynamically creates a subclass instance based on the trait id
    @staticmethod
    def new(id: ShapeID, value: "DocumentValue" = None) -> "Trait | DynamicTrait":
        """Dynamically create a new trait of the given ID.

        If the ID corresponds to a known Trait class, that class will be instantiated
        and returned. Otherwise, a :py:class:`DynamicTrait` will be returned.

        :returns: A trait of the given ID with the given value.
        """
        if (cls := Trait._REGISTRY.get(id, None)) is not None:
            return cls(value)
        return DynamicTrait(id=id, document_value=value)


@dataclass(init=False, frozen=True)
class DefaultTrait(Trait, id=ShapeID("smithy.api#default")):
    """Sets the default value of a shape or member."""

    @property
    def value(self) -> "DocumentValue":
        """The default value."""
        return self.document_value


@dataclass(init=False, frozen=True)
class SparseTrait(Trait, id=ShapeID("smithy.api#sparse")):
    """Indicates that a list or map may contain null values."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class TimestampFormatTrait(Trait, id=ShapeID("smithy.api#timestampFormat")):
    """Sets the format a timestamp is serialized in."""

    format: TimestampFormat

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        assert isinstance(self.document_value, str)
        object.__setattr__(self, "format", TimestampFormat(self.document_value))


class ErrorFault(Enum):
    """Whether an error is the client's fault or the server's."""

    CLIENT = "client"
    SERVER = "server"


@dataclass(init=False, frozen=True)
class ErrorTrait(Trait, id=ShapeID("smithy.api#error")):
    """Marks a structure as an error."""

    fault: ErrorFault

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        assert isinstance(self.document_value, str)
        object.__setattr__(self, "fault", ErrorFault(self.document_value))


@dataclass(init=False, frozen=True)
class RequiredTrait(Trait, id=ShapeID("smithy.api#required")):
    """Marks a member as required."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class InternalTrait(Trait, id=ShapeID("smithy.api#internal")):
    """Marks a shape as internal to the service."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class SensitiveTrait(Trait, id=ShapeID("smithy.api#sensitive")):
    """Marks a shape as holding sensitive data that must not be logged."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class StreamingTrait(Trait, id=ShapeID("smithy.api#streaming")):
    """Marks a blob or union as streamed rather than buffered."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class RequiresLengthTrait(Trait, id=ShapeID("smithy.api#requiresLength")):
    """Indicates that a streaming blob must have a known length."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class UnitTypeTrait(Trait, id=ShapeID("smithy.api#unitType")):
    """Marks a structure as the unit type."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class MediaTypeTrait(Trait, id=ShapeID("smithy.api#mediaType")):
    """Sets the media type of a blob or string."""

    document_value: str | None = None

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, str)

    @property
    def value(self) -> str:
        """The media type."""
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class EventHeaderTrait(Trait, id=ShapeID("smithy.api#eventHeader")):
    """Binds an event member to an event stream header."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class EventPayloadTrait(Trait, id=ShapeID("smithy.api#eventPayload")):
    """Binds an event member to the event stream payload."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class JSONNameTrait(Trait, id=ShapeID("smithy.api#jsonName")):
    """Overrides the JSON key a member is serialized under."""

    document_value: str | None = None

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, str)

    @property
    def value(self) -> str:
        """The JSON key."""
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class IdempotencyTokenTrait(Trait, id=ShapeID("smithy.api#idempotencyToken")):
    """Marks a member as an idempotency token the client fills in when unset."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class EnumValueTrait(Trait, id=ShapeID("smithy.api#enumValue")):
    """Sets the serialized value of an enum member."""

    @property
    def value(self) -> str | int:
        """The serialized enum value."""
        assert isinstance(self.document_value, str | int)
        return self.document_value


@dataclass(init=False, frozen=True)
class LongPollTrait(Trait, id=ShapeID("smithy.api#longPoll")):
    """Indicates that the service may hold the request open while waiting for
    information to become available."""

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, Mapping)
        assert isinstance(self.document_value["timeoutMillis"], int)

    @property
    def timeout_millis(self) -> int:
        """The timeout in milliseconds that a client should wait for a response."""
        return self.document_value["timeoutMillis"]  # type: ignore


# TODO: Get all this moved over to the http package
@dataclass(init=False, frozen=True)
class HTTPTrait(Trait, id=ShapeID("smithy.api#http")):
    """Binds an operation to an HTTP method, URI pattern and status code."""

    path: PathPattern = field(repr=False, hash=False, compare=False)
    code: int = field(repr=False, hash=False, compare=False)
    query: str | None = field(default=None, repr=False, hash=False, compare=False)

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        assert isinstance(self.document_value, Mapping)
        assert isinstance(self.document_value["method"], str)

        code = self.document_value.get("code", 200)
        assert isinstance(code, int)
        object.__setattr__(self, "code", code)

        uri = self.document_value["uri"]
        assert isinstance(uri, str)
        parts = uri.split("?", 1)

        object.__setattr__(self, "path", PathPattern(parts[0]))
        object.__setattr__(self, "query", parts[1] if len(parts) == 2 else None)

    @property
    def method(self) -> str:
        """The HTTP method."""
        return self.document_value["method"]  # type: ignore


@dataclass(init=False, frozen=True)
class HTTPErrorTrait(Trait, id=ShapeID("smithy.api#httpError")):
    """Sets the HTTP status code of an error."""

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, int)

    @property
    def code(self) -> int:
        """The HTTP status code."""
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class HTTPHeaderTrait(Trait, id=ShapeID("smithy.api#httpHeader")):
    """Binds a member to an HTTP header."""

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, str)

    @property
    def key(self) -> str:
        """The header name."""
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class HTTPLabelTrait(Trait, id=ShapeID("smithy.api#httpLabel")):
    """Binds a member to a label in the HTTP path."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class HTTPPayloadTrait(Trait, id=ShapeID("smithy.api#httpPayload")):
    """Binds a member to the HTTP body."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class HTTPPrefixHeadersTrait(Trait, id=ShapeID("smithy.api#httpPrefixHeaders")):
    """Binds a map member to the HTTP headers that share a prefix."""

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, str)

    @property
    def prefix(self) -> str:
        """The header name prefix."""
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class HTTPQueryTrait(Trait, id=ShapeID("smithy.api#httpQuery")):
    """Binds a member to an HTTP query parameter."""

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, str)

    @property
    def key(self) -> str:
        """The query parameter name."""
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class HTTPQueryParamsTrait(Trait, id=ShapeID("smithy.api#httpQueryParams")):
    """Binds a map member to the HTTP query parameters."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class HTTPResponseCodeTrait(Trait, id=ShapeID("smithy.api#httpResponseCode")):
    """Binds a member to the HTTP status code."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class HTTPChecksumRequiredTrait(Trait, id=ShapeID("smithy.api#httpChecksumRequired")):
    """Indicates that an operation requires a checksum of its HTTP payload."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class EndpointTrait(Trait, id=ShapeID("smithy.api#endpoint")):
    """Sets a host prefix for an operation's endpoint."""

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, str)

    @property
    def host_prefix(self) -> str:
        """The host prefix pattern."""
        return self.document_value["hostPrefix"]  # type: ignore


@dataclass(init=False, frozen=True)
class HostLabelTrait(Trait, id=ShapeID("smithy.api#hostLabel")):
    """Binds a member to a label in the endpoint host prefix."""

    def __post_init__(self) -> None:
        assert self.document_value is None


class APIKeyLocation(Enum):
    """The locations that the api key could be placed in the signed request."""

    HEADER = "header"
    QUERY = "query"


@dataclass(init=False, frozen=True)
class HTTPAPIKeyAuthTrait(Trait, id=ShapeID("smithy.api#httpApiKeyAuth")):
    """Configures API key auth for a service."""

    location: APIKeyLocation = field(repr=False, hash=False, compare=False)

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        assert isinstance(self.document_value, Mapping)
        assert isinstance(self.document_value["in"], str)
        assert isinstance(self.document_value["name"], str)
        assert isinstance(self.document_value.get("scheme"), str | None)

        location = self.document_value["in"]
        object.__setattr__(self, "location", APIKeyLocation(location))

    @property
    def name(self) -> str:
        """The name of the header or query parameter that carries the key."""
        return self.document_value["name"]  # type: ignore

    @property
    def scheme(self) -> str | None:
        """The scheme the key is prefixed with in the header, if any."""
        return self.document_value.get("scheme")  # type: ignore


@dataclass(init=False, frozen=True)
class RpcV2CborTrait(Trait, id=ShapeID("smithy.protocols#rpcv2Cbor")):
    """The ``smithy.protocols#rpcv2Cbor`` protocol trait."""

    http: Sequence[str] = field(
        repr=False, hash=False, compare=False, default_factory=tuple
    )
    event_stream_http: Sequence[str] = field(
        repr=False, hash=False, compare=False, default_factory=tuple
    )

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        http, event_stream_http = _parse_http_protocol_values(self.document_value)
        object.__setattr__(self, "http", http)
        object.__setattr__(self, "event_stream_http", event_stream_http)


@dataclass(init=False, frozen=True)
class RpcV2JsonTrait(Trait, id=ShapeID("smithy.protocols#rpcv2Json")):
    """The ``smithy.protocols#rpcv2Json`` protocol trait."""

    http: Sequence[str] = field(
        repr=False, hash=False, compare=False, default_factory=tuple
    )
    event_stream_http: Sequence[str] = field(
        repr=False, hash=False, compare=False, default_factory=tuple
    )

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        http, event_stream_http = _parse_http_protocol_values(self.document_value)
        object.__setattr__(self, "http", http)
        object.__setattr__(self, "event_stream_http", event_stream_http)


@dataclass(init=False, frozen=True)
class XMLNameTrait(Trait, id=ShapeID("smithy.api#xmlName")):
    """Overrides the XML element or attribute name of a shape or member."""

    document_value: str | None = None

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, str)

    @property
    def value(self) -> str:
        """The XML name."""
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class XMLNamespaceTrait(Trait, id=ShapeID("smithy.api#xmlNamespace")):
    """Sets the XML namespace of a shape or member."""

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, Mapping)
        assert isinstance(self.document_value["uri"], str)
        assert isinstance(self.document_value.get("prefix"), str | None)

    @property
    def uri(self) -> str:
        """The namespace URI."""
        return self.document_value["uri"]  # type: ignore

    @property
    def prefix(self) -> str | None:
        """The namespace prefix, if any."""
        return self.document_value.get("prefix")  # type: ignore


@dataclass(init=False, frozen=True)
class XMLFlattenedTrait(Trait, id=ShapeID("smithy.api#xmlFlattened")):
    """Serializes a list or map without a wrapping element."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class XMLAttributeTrait(Trait, id=ShapeID("smithy.api#xmlAttribute")):
    """Serializes a member as an XML attribute."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class ContextParamTrait(Trait, id=ShapeID("smithy.rules#contextParam")):
    """Binds a member to an endpoint ruleset parameter."""

    name: str = field(repr=False, hash=False, compare=False)

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        assert isinstance(self.document_value, Mapping)
        name = self.document_value["name"]
        assert isinstance(name, str)
        object.__setattr__(self, "name", name)


@dataclass(init=False, frozen=True)
class StaticContextParamsTrait(Trait, id=ShapeID("smithy.rules#staticContextParams")):
    """Sets constant endpoint ruleset parameters for an operation."""

    values: Mapping[str, "DocumentValue"] = field(repr=False, hash=False, compare=False)

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        assert isinstance(self.document_value, Mapping)

        values: dict[str, DocumentValue] = {}
        for name, definition in self.document_value.items():
            assert isinstance(definition, Mapping)
            values[name] = definition["value"]
        object.__setattr__(self, "values", values)


@dataclass(init=False, frozen=True)
class OperationContextParamsTrait(
    Trait, id=ShapeID("smithy.rules#operationContextParams")
):
    """Binds endpoint ruleset parameters to JMESPath expressions over the input."""

    paths: Mapping[str, str] = field(repr=False, hash=False, compare=False)

    def __init__(self, value: "DocumentValue | DynamicTrait" = None):
        super().__init__(value)
        assert isinstance(self.document_value, Mapping)

        paths: dict[str, str] = {}
        for name, definition in self.document_value.items():
            assert isinstance(definition, Mapping)
            path = definition["path"]
            assert isinstance(path, str)
            paths[name] = path
        object.__setattr__(self, "paths", paths)


def _parse_http_protocol_values(
    value: "DocumentValue",
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Parse ``{"http": [...], "eventStreamHttp": [...]}`` into (http, eventStreamHttp).

    A missing ``eventStreamHttp`` defaults to the ``http`` versions; a missing ``http``
    defaults to ``("http/1.1",)``.
    """
    document_value = value or {}
    assert isinstance(document_value, Mapping)

    http_raw = document_value.get("http", ["http/1.1"])
    assert isinstance(http_raw, Sequence)
    http: list[str] = []
    for entry in http_raw:
        assert isinstance(entry, str)
        http.append(entry)

    event_stream_http_raw = document_value.get("eventStreamHttp")
    if not event_stream_http_raw:
        return tuple(http), tuple(http)

    assert isinstance(event_stream_http_raw, Sequence)
    event_stream_http: list[str] = []
    for entry in event_stream_http_raw:
        assert isinstance(entry, str)
        event_stream_http.append(entry)

    return tuple(http), tuple(event_stream_http)
