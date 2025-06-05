#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from enum import Enum

from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeType
from smithy_core.traits import (
    ErrorFault,
    ErrorTrait,
    HostLabelTrait,
    HTTPErrorTrait,
    HTTPHeaderTrait,
    HTTPLabelTrait,
    HTTPPayloadTrait,
    HTTPPrefixHeadersTrait,
    HTTPQueryParamsTrait,
    HTTPQueryTrait,
    HTTPResponseCodeTrait,
    StreamingTrait,
)


class Binding(Enum):
    """HTTP binding locations."""

    HEADER = 0
    """Indicates the member is bound to a header."""

    QUERY = 1
    """Indicates the member is bound to a query parameter."""

    PAYLOAD = 2
    """Indicates the member is bound to the entire HTTP payload."""

    BODY = 3
    """Indicates the member is a property in the HTTP payload structure."""

    LABEL = 4
    """Indicates the member is bound to a path segment in the URI."""

    STATUS = 5
    """Indicates the member is bound to the response status code."""

    PREFIX_HEADERS = 6
    """Indicates the member is bound to multiple headers with a shared prefix."""

    QUERY_PARAMS = 7
    """Indicates the member is bound to the query string as multiple key-value pairs."""

    HOST = 8
    """Indicates the member is bound to a prefix to the host AND to the body."""


@dataclass(init=False)
class _BindingMatcher:
    bindings: list[Binding]
    """A list of bindings where the index matches the index of the member schema."""

    response_status: int
    """The default response status code."""

    has_body: bool
    """Whether the HTTP message has members bound to the body."""

    has_payload: bool
    """Whether the HTTP message has a member bound to the entire payload."""

    payload_member: Schema | None
    """The member bound to the payload, if one exists."""

    event_stream_member: Schema | None
    """The member bound to the event stream, if one exists."""

    def __init__(self, struct: Schema, response_status: int) -> None:
        self.response_status = response_status
        found_body = False
        found_payload = False
        self.bindings = []
        self.payload_member = None
        self.event_stream_member = None

        for member in struct.members.values():
            binding = self._do_match(member)
            self.bindings.append(binding)
            found_body = (
                found_body or binding is Binding.BODY or binding is Binding.HOST
            )
            if binding is Binding.PAYLOAD:
                found_payload = True
                self.payload_member = member
            if (
                StreamingTrait.id in member.traits
                and member.shape_type is ShapeType.UNION
            ):
                self.event_stream_member = member

        self.has_body = found_body
        self.has_payload = found_payload

    def should_write_body(self, omit_empty_payload: bool) -> bool:
        """Determines whether a body should be written.

        :param omit_empty_payload: Whether a body should be skipped in the case of an
            empty payload.
        """
        return self.has_body or (not omit_empty_payload and not self.has_payload)

    def match(self, member: Schema) -> Binding:
        """Determines which part of the HTTP message the given member is bound to."""
        return self.bindings[member.expect_member_index()]

    def _do_match(self, member: Schema) -> Binding: ...


@dataclass(init=False)
class RequestBindingMatcher(_BindingMatcher):
    """Matches structure members to HTTP request binding locations."""

    def __init__(self, struct: Schema) -> None:
        """Initialize a RequestBindingMatcher.

        :param struct: The structure to examine for HTTP bindings.
        """
        super().__init__(struct, -1)

    def _do_match(self, member: Schema) -> Binding:
        if HTTPLabelTrait.id in member.traits:
            return Binding.LABEL
        if HTTPQueryTrait.id in member.traits:
            return Binding.QUERY
        if HTTPQueryParamsTrait.id in member.traits:
            return Binding.QUERY_PARAMS
        if HTTPHeaderTrait.id in member.traits:
            return Binding.HEADER
        if HTTPPrefixHeadersTrait.id in member.traits:
            return Binding.PREFIX_HEADERS
        if HTTPPayloadTrait.id in member.traits:
            return Binding.PAYLOAD
        if HostLabelTrait.id in member.traits:
            return Binding.HOST
        return Binding.BODY


@dataclass(init=False)
class ResponseBindingMatcher(_BindingMatcher):
    """Matches structure members to HTTP response binding locations."""

    def __init__(self, struct: Schema) -> None:
        """Initialize a ResponseBindingMatcher.

        :param struct: The structure to examine for HTTP bindings.
        """
        super().__init__(struct, self._compute_response(struct))

    def _compute_response(self, struct: Schema) -> int:
        if (http_error := struct.get_trait(HTTPErrorTrait)) is not None:
            return http_error.code
        if (error := struct.get_trait(ErrorTrait)) is not None:
            return 400 if error.fault is ErrorFault.CLIENT else 500
        return -1

    def _do_match(self, member: Schema) -> Binding:
        if HTTPResponseCodeTrait.id in member.traits:
            return Binding.STATUS
        if HTTPHeaderTrait.id in member.traits:
            return Binding.HEADER
        if HTTPPrefixHeadersTrait.id in member.traits:
            return Binding.PREFIX_HEADERS
        if HTTPPayloadTrait.id in member.traits:
            return Binding.PAYLOAD
        return Binding.BODY
