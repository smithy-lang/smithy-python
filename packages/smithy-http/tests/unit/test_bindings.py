#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_core.prelude import INTEGER, STRING
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
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
from smithy_http.bindings import Binding, RequestBindingMatcher, ResponseBindingMatcher

PAYLOAD_BINDING = Schema.collection(
    id=ShapeID("com.example#Payload"),
    members={"payload": {"target": STRING, "traits": [HTTPPayloadTrait()]}},
)

EVENT_STREAM_SCHEMA = Schema.collection(
    id=ShapeID("com.example#EventStream"),
    shape_type=ShapeType.UNION,
    members={
        "stream": {
            "target": Schema.collection(id=ShapeID("com.example#Event")),
        }
    },
    traits=[StreamingTrait()],
)
EVENT_STREAM_BINDING = Schema.collection(
    id=ShapeID("com.example#Events"),
    members={"stream": {"target": EVENT_STREAM_SCHEMA}},
)

STRING_MAP = Schema.collection(
    id=ShapeID("com.example#StringMap"),
    shape_type=ShapeType.MAP,
    members={
        "key": {"target": STRING},
        "value": {"target": STRING},
    },
)

GENERAL_BINDINGS = Schema.collection(
    id=ShapeID("com.example#BodyBindings"),
    members={
        "label": {"target": STRING, "traits": [HTTPLabelTrait()]},
        "query": {"target": STRING, "traits": [HTTPQueryTrait()]},
        "queryParams": {
            "target": STRING_MAP,
            "traits": [HTTPQueryParamsTrait()],
        },
        "header": {"target": STRING, "traits": [HTTPHeaderTrait()]},
        "prefixHeaders": {
            "target": STRING_MAP,
            "traits": [HTTPPrefixHeadersTrait("foo")],
        },
        "hostLabel": {"target": STRING, "traits": [HostLabelTrait()]},
        "status": {
            "target": INTEGER,
            "traits": [HTTPResponseCodeTrait()],
        },
        "body": {"target": STRING},
    },
)


def test_request_payload_matching() -> None:
    matcher = RequestBindingMatcher(PAYLOAD_BINDING)
    member_schema = PAYLOAD_BINDING.members["payload"]
    actual = matcher.match(member_schema)
    assert actual == Binding.PAYLOAD
    assert matcher.payload_member is member_schema


def test_response_payload_matching() -> None:
    matcher = ResponseBindingMatcher(PAYLOAD_BINDING)
    member_schema = PAYLOAD_BINDING.members["payload"]
    actual = matcher.match(member_schema)
    assert actual == Binding.PAYLOAD
    assert matcher.payload_member is member_schema


def test_request_event_stream_matching() -> None:
    matcher = RequestBindingMatcher(EVENT_STREAM_BINDING)
    member_schema = EVENT_STREAM_BINDING.members["stream"]
    assert matcher.event_stream_member is member_schema


def test_response_event_stream_matching() -> None:
    matcher = ResponseBindingMatcher(EVENT_STREAM_BINDING)
    member_schema = EVENT_STREAM_BINDING.members["stream"]
    assert matcher.event_stream_member is member_schema


def test_response_matches_http_error_trait() -> None:
    schema = Schema.collection(
        id=ShapeID("com.example#HTTPErrorTrait"), traits=[HTTPErrorTrait(404)]
    )
    matcher = ResponseBindingMatcher(schema)
    assert matcher.response_status == 404


def test_response_matches_error_trait() -> None:
    schema = Schema.collection(
        id=ShapeID("com.example#ErrorTrait"), traits=[ErrorTrait("client")]
    )
    matcher = ResponseBindingMatcher(schema)
    assert matcher.response_status == 400

    schema = Schema.collection(
        id=ShapeID("com.example#ErrorTrait"), traits=[ErrorTrait("server")]
    )
    matcher = ResponseBindingMatcher(schema)
    assert matcher.response_status == 500


def test_request_matching() -> None:
    matcher = RequestBindingMatcher(GENERAL_BINDINGS)
    assert matcher.match(GENERAL_BINDINGS.members["label"]) == Binding.LABEL
    assert matcher.match(GENERAL_BINDINGS.members["query"]) == Binding.QUERY

    query_params_member = GENERAL_BINDINGS.members["queryParams"]
    assert matcher.match(query_params_member) == Binding.QUERY_PARAMS

    assert matcher.match(GENERAL_BINDINGS.members["header"]) == Binding.HEADER

    prefix_member = GENERAL_BINDINGS.members["prefixHeaders"]
    assert matcher.match(prefix_member) == Binding.PREFIX_HEADERS

    assert matcher.match(GENERAL_BINDINGS.members["hostLabel"]) == Binding.HOST
    assert matcher.match(GENERAL_BINDINGS.members["status"]) == Binding.BODY
    assert matcher.match(GENERAL_BINDINGS.members["body"]) == Binding.BODY


def test_response_matching() -> None:
    matcher = ResponseBindingMatcher(GENERAL_BINDINGS)
    assert matcher.match(GENERAL_BINDINGS.members["label"]) == Binding.BODY
    assert matcher.match(GENERAL_BINDINGS.members["query"]) == Binding.BODY

    query_params_member = GENERAL_BINDINGS.members["queryParams"]
    assert matcher.match(query_params_member) == Binding.BODY

    assert matcher.match(GENERAL_BINDINGS.members["header"]) == Binding.HEADER

    prefix_member = GENERAL_BINDINGS.members["prefixHeaders"]
    assert matcher.match(prefix_member) == Binding.PREFIX_HEADERS

    assert matcher.match(GENERAL_BINDINGS.members["hostLabel"]) == Binding.BODY
    assert matcher.match(GENERAL_BINDINGS.members["status"]) == Binding.STATUS
    assert matcher.match(GENERAL_BINDINGS.members["body"]) == Binding.BODY
