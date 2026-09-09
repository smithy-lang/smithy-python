# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from smithy_core.schemas import Schema, SchemaExtension
from smithy_core.shapes import ShapeType
from smithy_core.traits import HTTPHeaderTrait, HTTPPrefixHeadersTrait

from .bindings import Binding, RequestBindingMatcher, ResponseBindingMatcher

type ResponseBoundMember = tuple[Schema, Binding, str | None, bool]


@dataclass(frozen=True, slots=True)
class HTTPBindingSchemaMetadata:
    """Precomputed request and response HTTP binding metadata for a schema."""

    request_bindings: tuple[Binding, ...]
    """Request binding route for each member index."""

    response_bindings: tuple[Binding, ...]
    """Response binding route for each member index."""

    has_request_body: bool
    """Whether the request structure contains document-body members."""

    has_response_body: bool
    """Whether the response structure contains document-body members."""

    payload_member: Schema | None
    """Member bound to the complete HTTP payload, if present."""

    event_stream_member: Schema | None
    """Member bound to an event stream, if present."""

    response_bound_members: tuple[ResponseBoundMember, ...]
    """Non-body response bindings in schema-member order."""

    response_status: int
    """Default response status derived from the structure traits."""

    def should_write_request_body(self, omit_empty_payload: bool) -> bool:
        """Return whether a request document body should be opened."""
        return self.has_request_body or (
            not omit_empty_payload and self.payload_member is None
        )

    def should_write_response_body(self, omit_empty_payload: bool) -> bool:
        """Return whether a response document body should be opened."""
        return self.has_response_body or (
            not omit_empty_payload and self.payload_member is None
        )


def _build_http_binding_schema_metadata(schema: Schema) -> HTTPBindingSchemaMetadata:
    request_matcher = RequestBindingMatcher(schema)
    response_matcher = ResponseBindingMatcher(schema)
    members = tuple(schema.members.values())
    request_bindings = tuple(request_matcher.bindings)
    response_bindings = tuple(response_matcher.bindings)

    response_bound_members: list[ResponseBoundMember] = []
    for member, binding in zip(members, response_bindings, strict=True):
        match binding:
            case Binding.HEADER:
                trait = member.expect_trait(HTTPHeaderTrait)
                response_bound_members.append(
                    (
                        member,
                        binding,
                        trait.key.lower(),
                        member.shape_type is ShapeType.LIST,
                    )
                )
            case Binding.PREFIX_HEADERS:
                trait = member.expect_trait(HTTPPrefixHeadersTrait)
                response_bound_members.append((member, binding, trait.prefix, False))
            case Binding.STATUS | Binding.PAYLOAD:
                response_bound_members.append((member, binding, None, False))
            case _:
                pass

    return HTTPBindingSchemaMetadata(
        request_bindings=request_bindings,
        response_bindings=response_bindings,
        has_request_body=request_matcher.has_body,
        has_response_body=response_matcher.has_body,
        payload_member=request_matcher.payload_member,
        event_stream_member=request_matcher.event_stream_member,
        response_bound_members=tuple(response_bound_members),
        response_status=response_matcher.response_status,
    )


HTTP_BINDING_SCHEMA_EXTENSION = SchemaExtension(_build_http_binding_schema_metadata)
"""Shared HTTP binding extension used by every HTTP protocol instance."""
