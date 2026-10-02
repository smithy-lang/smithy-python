# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from urllib.parse import unquote

from smithy_core.schemas import Schema, SchemaExtension
from smithy_core.shapes import ShapeType
from smithy_core.traits import (
    EndpointTrait,
    HostLabelTrait,
    HTTPHeaderTrait,
    HTTPLabelTrait,
    HTTPPrefixHeadersTrait,
    HTTPQueryTrait,
    HTTPTrait,
    MediaTypeTrait,
    RequiresLengthTrait,
    StreamingTrait,
    TimestampFormatTrait,
)
from smithy_core.types import PathPattern, TimestampFormat

from .bindings import Binding, RequestBindingMatcher, ResponseBindingMatcher

type HTTPResponseBindingDispatch = tuple[
    Schema,
    Binding,
    str | None,
    bool,
    TimestampFormat | None,
    ShapeType,
    bool,
]
"""Compact response binding entry used by the deserialization hot path."""


@dataclass(frozen=True, slots=True)
class HTTPMemberBindingMetadata:
    """Precomputed HTTP binding metadata for one structure member."""

    member: Schema
    """The canonical member schema."""

    member_index: int
    """The member's stable index in its containing structure."""

    request_binding: Binding
    """The member's request-direction binding."""

    response_binding: Binding
    """The member's response-direction binding."""

    request_wire_name: str | None
    """Request header, query, prefix, label, or host-label name."""

    response_wire_name: str | None
    """Response header or prefix name."""

    request_header_name: str | None
    """Canonical lowercase request header name."""

    response_header_name: str | None
    """Canonical lowercase response header name."""

    request_timestamp_format: TimestampFormat | None
    """Effective timestamp format for the request binding."""

    response_timestamp_format: TimestampFormat | None
    """Effective timestamp format for the response binding."""

    value_shape_type: ShapeType
    """Shape type written at the binding location, unwrapping lists."""

    is_list: bool
    """Whether the bound member targets a list."""

    media_type: str | None
    """Resolved ``@mediaType`` value, if present."""


@dataclass(frozen=True, slots=True)
class HTTPPayloadMetadata:
    """Precomputed handling information for an ``@httpPayload`` member."""

    member: Schema
    """The payload member schema."""

    shape_type: ShapeType
    """The payload member's target shape type."""

    media_type: str | None
    """Effective payload media type, including raw-payload defaults."""

    requires_length: bool
    """Whether the payload carries ``@requiresLength``."""

    is_streaming: bool
    """Whether the payload carries ``@streaming``."""

    is_event_stream: bool
    """Whether the payload is a streaming union."""

    is_raw: bool
    """Whether the payload uses raw string or byte serialization."""


@dataclass(frozen=True, slots=True)
class HTTPRequestBindingMetadata:
    """Precomputed request-direction HTTP binding plan."""

    bindings: tuple[Binding, ...]
    body_members: tuple[bool, ...]
    has_body: bool
    payload: HTTPPayloadMetadata | None
    event_stream_member: Schema | None
    header_names: frozenset[str]
    query_names: frozenset[str]
    has_content_type_header: bool

    def should_write_body(self, omit_empty_payload: bool) -> bool:
        """Return whether a request document body should be opened."""
        return self.has_body or (not omit_empty_payload and self.payload is None)


@dataclass(frozen=True, slots=True)
class HTTPResponseBindingMetadata:
    """Precomputed response-direction HTTP binding plan."""

    bindings: tuple[Binding, ...]
    body_members: tuple[bool, ...]
    has_body: bool
    payload: HTTPPayloadMetadata | None
    streaming_member: Schema | None
    """The first response member carrying ``@streaming``, if present."""

    event_stream_member: Schema | None
    bound_members: tuple[HTTPMemberBindingMetadata, ...]
    dispatch: tuple[HTTPResponseBindingDispatch, ...]
    header_members: tuple[HTTPMemberBindingMetadata, ...]
    headers_by_name: Mapping[str, HTTPMemberBindingMetadata]
    header_names: frozenset[str]
    response_status: int

    def should_write_body(self, omit_empty_payload: bool) -> bool:
        """Return whether a response document body should be opened."""
        return self.has_body or (not omit_empty_payload and self.payload is None)


@dataclass(frozen=True, slots=True)
class HTTPBindingSchemaMetadata:
    """Precomputed request and response HTTP binding metadata for a schema."""

    members: tuple[HTTPMemberBindingMetadata, ...]
    """Per-member binding metadata indexed by ``Schema.member_index``."""

    request: HTTPRequestBindingMetadata
    """Request-direction binding plan."""

    response: HTTPResponseBindingMetadata
    """Response-direction binding plan."""

    @property
    def request_bindings(self) -> tuple[Binding, ...]:
        """Request binding route for each member index."""
        return self.request.bindings

    @property
    def response_bindings(self) -> tuple[Binding, ...]:
        """Response binding route for each member index."""
        return self.response.bindings

    @property
    def has_request_body(self) -> bool:
        """Whether the request structure contains document-body members."""
        return self.request.has_body

    @property
    def has_response_body(self) -> bool:
        """Whether the response structure contains document-body members."""
        return self.response.has_body

    @property
    def payload_member(self) -> Schema | None:
        """Member bound to the complete HTTP payload, if present."""
        payload = self.request.payload or self.response.payload
        return payload.member if payload is not None else None

    @property
    def event_stream_member(self) -> Schema | None:
        """Member bound to an event stream, if present."""
        return self.request.event_stream_member or self.response.event_stream_member

    @property
    def response_bound_members(
        self,
    ) -> tuple[tuple[Schema, Binding, str | None, bool], ...]:
        """Non-body response bindings in schema-member order."""
        return tuple(
            (member, binding, name, is_list)
            for (
                member,
                binding,
                name,
                is_list,
                _,
                _,
                _,
            ) in self.response.dispatch
        )

    @property
    def response_status(self) -> int:
        """Default response status derived from the structure traits."""
        return self.response.response_status

    def should_write_request_body(self, omit_empty_payload: bool) -> bool:
        """Return whether a request document body should be opened."""
        return self.request.should_write_body(omit_empty_payload)

    def should_write_response_body(self, omit_empty_payload: bool) -> bool:
        """Return whether a response document body should be opened."""
        return self.response.should_write_body(omit_empty_payload)


@dataclass(frozen=True, slots=True)
class HTTPOperationSchemaMetadata:
    """Precomputed HTTP binding metadata for an operation schema."""

    http_trait: HTTPTrait
    """The operation's resolved ``@http`` trait."""

    method: str
    """The operation's HTTP method."""

    path: PathPattern
    """The parsed operation URI path."""

    query: str | None
    """The static operation URI query string."""

    query_literal_names: frozenset[str]
    """Raw static query names used for ``@httpQueryParams`` precedence."""

    response_status: int
    """The operation's default HTTP response status."""

    host_prefix: str
    """The operation's endpoint host-prefix pattern."""

    greedy_label_names: frozenset[str]
    """Names of greedy labels in the URI path."""

    @classmethod
    def from_traits(
        cls,
        http_trait: HTTPTrait,
        endpoint_trait: EndpointTrait | None = None,
    ) -> "HTTPOperationSchemaMetadata":
        """Build operation metadata from already-resolved traits."""
        query = http_trait.query
        query_literal_names: frozenset[str] = (
            frozenset(unquote(entry.partition("=")[0]) for entry in query.split("&"))
            if query
            else frozenset[str]()
        )
        return cls(
            http_trait=http_trait,
            method=http_trait.method,
            path=http_trait.path,
            query=query,
            query_literal_names=query_literal_names,
            response_status=http_trait.code,
            host_prefix=endpoint_trait.host_prefix
            if endpoint_trait is not None
            else "",
            greedy_label_names=frozenset(http_trait.path.greedy_labels),
        )


def _wire_name(member: Schema, binding: Binding) -> str | None:
    match binding:
        case Binding.HEADER:
            return member.expect_trait(HTTPHeaderTrait).key
        case Binding.QUERY:
            return member.expect_trait(HTTPQueryTrait).key
        case Binding.PREFIX_HEADERS:
            return member.expect_trait(HTTPPrefixHeadersTrait).prefix
        case Binding.LABEL if HTTPLabelTrait in member:
            return member.expect_member_name()
        case Binding.HOST if HostLabelTrait in member:
            return member.expect_member_name()
        case _:
            return None


def _value_schema(member: Schema) -> Schema:
    return member.members["member"] if member.shape_type is ShapeType.LIST else member


def _timestamp_format(member: Schema, binding: Binding) -> TimestampFormat | None:
    value_schema = _value_schema(member)
    if value_schema.shape_type is not ShapeType.TIMESTAMP:
        return None
    if (trait := value_schema.get_trait(TimestampFormatTrait)) is not None:
        return trait.format
    if binding is Binding.HEADER:
        return TimestampFormat.HTTP_DATE
    if binding in (Binding.QUERY, Binding.LABEL):
        return TimestampFormat.DATE_TIME
    return None


def _build_payload_metadata(member: Schema | None) -> HTTPPayloadMetadata | None:
    if member is None:
        return None
    shape_type = member.shape_type
    media_type_trait = member.get_trait(MediaTypeTrait)
    media_type = media_type_trait.value if media_type_trait is not None else None
    if media_type is None:
        if shape_type is ShapeType.BLOB:
            media_type = "application/octet-stream"
        elif shape_type in (ShapeType.STRING, ShapeType.ENUM):
            media_type = "text/plain"
    is_streaming = StreamingTrait in member
    is_event_stream = is_streaming and shape_type is ShapeType.UNION
    return HTTPPayloadMetadata(
        member=member,
        shape_type=shape_type,
        media_type=media_type,
        requires_length=RequiresLengthTrait in member,
        is_streaming=is_streaming,
        is_event_stream=is_event_stream,
        is_raw=shape_type in (ShapeType.BLOB, ShapeType.STRING, ShapeType.ENUM),
    )


def _build_http_binding_schema_metadata(schema: Schema) -> HTTPBindingSchemaMetadata:
    request_matcher = RequestBindingMatcher(schema)
    response_matcher = ResponseBindingMatcher(schema)
    members = tuple(schema.members.values())
    request_bindings = tuple(request_matcher.bindings)
    response_bindings = tuple(response_matcher.bindings)

    member_metadata = tuple(
        HTTPMemberBindingMetadata(
            member=member,
            member_index=member.expect_member_index(),
            request_binding=request_binding,
            response_binding=response_binding,
            request_wire_name=_wire_name(member, request_binding),
            response_wire_name=_wire_name(member, response_binding),
            request_header_name=(
                member.expect_trait(HTTPHeaderTrait).key.lower()
                if request_binding is Binding.HEADER
                else None
            ),
            response_header_name=(
                member.expect_trait(HTTPHeaderTrait).key.lower()
                if response_binding is Binding.HEADER
                else None
            ),
            request_timestamp_format=_timestamp_format(member, request_binding),
            response_timestamp_format=_timestamp_format(member, response_binding),
            value_shape_type=_value_schema(member).shape_type,
            is_list=member.shape_type is ShapeType.LIST,
            media_type=(
                media_type.value
                if (media_type := _value_schema(member).get_trait(MediaTypeTrait))
                is not None
                else None
            ),
        )
        for member, request_binding, response_binding in zip(
            members, request_bindings, response_bindings, strict=True
        )
    )

    request_header_names = frozenset(
        metadata.request_header_name
        for metadata in member_metadata
        if metadata.request_header_name is not None
    )
    request_query_names = frozenset(
        metadata.request_wire_name
        for metadata in member_metadata
        if metadata.request_binding is Binding.QUERY
        and metadata.request_wire_name is not None
    )

    response_bound_members = tuple(
        metadata
        for metadata in member_metadata
        if metadata.response_binding
        in (
            Binding.HEADER,
            Binding.PREFIX_HEADERS,
            Binding.STATUS,
            Binding.PAYLOAD,
        )
    )
    response_header_members = tuple(
        metadata
        for metadata in response_bound_members
        if metadata.response_binding is Binding.HEADER
    )
    response_headers_by_name = MappingProxyType(
        {
            metadata.response_header_name: metadata
            for metadata in response_header_members
            if metadata.response_header_name is not None
        }
    )
    response_header_names = frozenset(response_headers_by_name)
    response_dispatch: tuple[HTTPResponseBindingDispatch, ...] = tuple(
        (
            metadata.member,
            metadata.response_binding,
            (
                metadata.response_header_name
                if metadata.response_binding is Binding.HEADER
                else metadata.response_wire_name
            ),
            metadata.is_list,
            metadata.response_timestamp_format,
            metadata.value_shape_type,
            metadata.media_type is not None,
        )
        for metadata in response_bound_members
    )

    request_payload = _build_payload_metadata(request_matcher.payload_member)
    response_payload = (
        request_payload
        if response_matcher.payload_member is request_matcher.payload_member
        else _build_payload_metadata(response_matcher.payload_member)
    )
    response_streaming_member = next(
        (member for member in members if StreamingTrait in member),
        None,
    )

    return HTTPBindingSchemaMetadata(
        members=member_metadata,
        request=HTTPRequestBindingMetadata(
            bindings=request_bindings,
            body_members=tuple(
                binding in (Binding.BODY, Binding.HOST) for binding in request_bindings
            ),
            has_body=request_matcher.has_body,
            payload=request_payload,
            event_stream_member=request_matcher.event_stream_member,
            header_names=request_header_names,
            query_names=request_query_names,
            has_content_type_header="content-type" in request_header_names,
        ),
        response=HTTPResponseBindingMetadata(
            bindings=response_bindings,
            body_members=tuple(
                binding is Binding.BODY for binding in response_bindings
            ),
            has_body=response_matcher.has_body,
            payload=response_payload,
            streaming_member=response_streaming_member,
            event_stream_member=response_matcher.event_stream_member,
            bound_members=response_bound_members,
            dispatch=response_dispatch,
            header_members=response_header_members,
            headers_by_name=response_headers_by_name,
            header_names=response_header_names,
            response_status=response_matcher.response_status,
        ),
    )


def _build_http_operation_schema_metadata(
    schema: Schema,
) -> HTTPOperationSchemaMetadata:
    return HTTPOperationSchemaMetadata.from_traits(
        http_trait=schema.expect_trait(HTTPTrait),
        endpoint_trait=schema.get_trait(EndpointTrait),
    )


HTTP_BINDING_SCHEMA_EXTENSION = SchemaExtension(_build_http_binding_schema_metadata)
"""Shared HTTP binding extension used by every HTTP protocol instance."""

HTTP_OPERATION_SCHEMA_EXTENSION = SchemaExtension(_build_http_operation_schema_metadata)
"""Shared HTTP operation extension used by every HTTP protocol instance."""
