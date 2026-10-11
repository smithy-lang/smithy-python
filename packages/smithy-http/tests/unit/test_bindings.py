#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_core.prelude import INTEGER, STRING
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeID, ShapeType
from smithy_core.traits import (
    EndpointTrait,
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
    HTTPTrait,
    MediaTypeTrait,
    RequiresLengthTrait,
    StreamingTrait,
    TimestampFormatTrait,
)
from smithy_core.types import TimestampFormat
from smithy_http.bindings import Binding, RequestBindingMatcher, ResponseBindingMatcher
from smithy_http.schema_extensions import (
    HTTP_BINDING_SCHEMA_EXTENSION,
    HTTP_OPERATION_SCHEMA_EXTENSION,
)

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
        "query": {"target": STRING, "traits": [HTTPQueryTrait("query")]},
        "queryParams": {
            "target": STRING_MAP,
            "traits": [HTTPQueryParamsTrait()],
        },
        "header": {"target": STRING, "traits": [HTTPHeaderTrait("header")]},
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


def test_http_binding_schema_extension_is_cached() -> None:
    info = GENERAL_BINDINGS.get_extension(HTTP_BINDING_SCHEMA_EXTENSION)

    assert info is GENERAL_BINDINGS.get_extension(HTTP_BINDING_SCHEMA_EXTENSION)
    assert info.request_bindings == tuple(
        RequestBindingMatcher(GENERAL_BINDINGS).bindings
    )
    assert info.response_bindings == tuple(
        ResponseBindingMatcher(GENERAL_BINDINGS).bindings
    )
    assert info.has_request_body
    assert info.has_response_body
    assert info.request.query_names == frozenset({"query"})
    assert info.request.header_names == frozenset({"header"})
    assert info.request.body_members == (
        False,
        False,
        False,
        False,
        False,
        True,
        True,
        True,
    )
    assert info.response.body_members == (
        True,
        True,
        True,
        False,
        False,
        True,
        False,
        True,
    )
    assert (
        info.response.headers_by_name["header"].member
        is (GENERAL_BINDINGS.members["header"])
    )
    assert tuple(entry[:4] for entry in info.response.dispatch) == (
        (
            GENERAL_BINDINGS.members["header"],
            Binding.HEADER,
            "header",
            False,
        ),
        (
            GENERAL_BINDINGS.members["prefixHeaders"],
            Binding.PREFIX_HEADERS,
            "foo",
            False,
        ),
        (
            GENERAL_BINDINGS.members["status"],
            Binding.STATUS,
            None,
            False,
        ),
    )
    assert info.response_bound_members == (
        (
            GENERAL_BINDINGS.members["header"],
            Binding.HEADER,
            "header",
            False,
        ),
        (
            GENERAL_BINDINGS.members["prefixHeaders"],
            Binding.PREFIX_HEADERS,
            "foo",
            False,
        ),
        (
            GENERAL_BINDINGS.members["status"],
            Binding.STATUS,
            None,
            False,
        ),
    )


def test_http_binding_schema_extension_caches_payload_and_event_stream() -> None:
    payload_info = PAYLOAD_BINDING.get_extension(HTTP_BINDING_SCHEMA_EXTENSION)
    event_info = EVENT_STREAM_BINDING.get_extension(HTTP_BINDING_SCHEMA_EXTENSION)

    assert payload_info.payload_member is PAYLOAD_BINDING.members["payload"]
    assert payload_info.response.streaming_member is None
    assert payload_info.response_bound_members == (
        (
            PAYLOAD_BINDING.members["payload"],
            Binding.PAYLOAD,
            None,
            False,
        ),
    )
    assert event_info.event_stream_member is EVENT_STREAM_BINDING.members["stream"]
    assert (
        event_info.response.streaming_member is EVENT_STREAM_BINDING.members["stream"]
    )


def test_http_binding_schema_extension_caches_member_formatting() -> None:
    schema = Schema.collection(
        id=ShapeID("com.example#Formatting"),
        members={
            "query": {
                "target": STRING,
                "traits": [HTTPQueryTrait("wireQuery")],
            },
            "header": {
                "target": STRING,
                "traits": [
                    HTTPHeaderTrait("X-Header"),
                    MediaTypeTrait("text/plain"),
                ],
            },
            "timestamp": {
                "target": Schema(
                    id=ShapeID("smithy.api#Timestamp"),
                    shape_type=ShapeType.TIMESTAMP,
                ),
                "traits": [
                    HTTPHeaderTrait("X-Time"),
                    TimestampFormatTrait("epoch-seconds"),
                ],
            },
        },
    )

    metadata = schema.get_extension(HTTP_BINDING_SCHEMA_EXTENSION)
    query, header, timestamp = metadata.members

    assert query.request_wire_name == "wireQuery"
    assert header.request_header_name == "x-header"
    assert header.media_type == "text/plain"
    assert timestamp.request_timestamp_format is TimestampFormat.EPOCH_SECONDS
    assert timestamp.response_timestamp_format is TimestampFormat.EPOCH_SECONDS


def test_http_binding_schema_extension_caches_payload_handling() -> None:
    schema = Schema.collection(
        id=ShapeID("com.example#PayloadMetadata"),
        members={
            "payload": {
                "target": STRING,
                "traits": [
                    HTTPPayloadTrait(),
                    MediaTypeTrait("application/custom"),
                    RequiresLengthTrait(),
                    StreamingTrait(),
                ],
            }
        },
    )

    payload = schema.get_extension(HTTP_BINDING_SCHEMA_EXTENSION).request.payload
    response = schema.get_extension(HTTP_BINDING_SCHEMA_EXTENSION).response

    assert payload is not None
    assert payload.member is schema.members["payload"]
    assert payload.media_type == "application/custom"
    assert payload.requires_length
    assert payload.is_streaming
    assert payload.is_raw
    assert response.streaming_member is schema.members["payload"]


def test_http_operation_schema_extension_is_cached() -> None:
    schema = Schema(
        id=ShapeID("com.example#Operation"),
        shape_type=ShapeType.OPERATION,
        traits=[
            HTTPTrait(
                {
                    "method": "PUT",
                    "code": 201,
                    "uri": "/items/{id+}?fixed=value&flag",
                }
            ),
            EndpointTrait({"hostPrefix": "{account}."}),
        ],
    )

    metadata = schema.get_extension(HTTP_OPERATION_SCHEMA_EXTENSION)

    assert metadata is schema.get_extension(HTTP_OPERATION_SCHEMA_EXTENSION)
    assert metadata.method == "PUT"
    assert metadata.path.pattern == "/items/{id+}"
    assert metadata.query == "fixed=value&flag"
    assert metadata.query_literal_names == frozenset({"fixed", "flag"})
    assert metadata.response_status == 201
    assert metadata.host_prefix == "{account}."
    assert metadata.greedy_label_names == frozenset({"id"})
