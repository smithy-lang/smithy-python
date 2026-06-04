#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import dataclasses

import pytest
from smithy_http import Field, Fields, ResponseMetadata, ResponseMetadataBuilder
from smithy_http.aio import HTTPResponse


class TestResponseMetadata:
    def test_construct_with_status_only(self):
        metadata = ResponseMetadata(status_code=200)
        assert metadata.status_code == 200
        assert metadata.request_id is None
        assert metadata.extended_request_id is None

    def test_construct_with_all_fields(self):
        metadata = ResponseMetadata(
            status_code=404,
            request_id="req-123",
            extended_request_id="ext-456",
        )
        assert metadata.status_code == 404
        assert metadata.request_id == "req-123"
        assert metadata.extended_request_id == "ext-456"

    def test_frozen(self):
        metadata = ResponseMetadata(status_code=200)
        with pytest.raises(dataclasses.FrozenInstanceError):
            metadata.status_code = 500  # type: ignore


class TestResponseMetadataBuilder:
    def _make_response(self, status: int, headers: dict[str, str]) -> HTTPResponse:
        fields = Fields(
            [Field(name=k, values=[v]) for k, v in headers.items()]
        )
        return HTTPResponse(status=status, fields=fields, body=b"")

    def test_build_no_mapping(self):
        builder = ResponseMetadataBuilder()
        response = self._make_response(200, {"x-amz-request-id": "abc"})
        metadata = builder.build(response)
        assert metadata.status_code == 200
        assert metadata.request_id is None
        assert metadata.extended_request_id is None

    def test_build_with_mapping(self):
        builder = ResponseMetadataBuilder(
            header_mapping={
                "request_id": "x-amz-request-id",
                "extended_request_id": "x-amz-id-2",
            }
        )
        response = self._make_response(
            200, {"x-amz-request-id": "req-abc", "x-amz-id-2": "ext-def"}
        )
        metadata = builder.build(response)
        assert metadata.status_code == 200
        assert metadata.request_id == "req-abc"
        assert metadata.extended_request_id == "ext-def"

    def test_build_missing_headers(self):
        builder = ResponseMetadataBuilder(
            header_mapping={
                "request_id": "x-amz-request-id",
                "extended_request_id": "x-amz-id-2",
            }
        )
        response = self._make_response(500, {})
        metadata = builder.build(response)
        assert metadata.status_code == 500
        assert metadata.request_id is None
        assert metadata.extended_request_id is None

    def test_build_case_insensitive_headers(self):
        builder = ResponseMetadataBuilder(
            header_mapping={"request_id": "X-Amz-Request-Id"}
        )
        response = self._make_response(200, {"x-amz-request-id": "id-123"})
        metadata = builder.build(response)
        assert metadata.request_id == "id-123"
