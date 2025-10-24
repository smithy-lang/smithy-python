#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from smithy_http.testing import create_test_request


def test_create_test_request_defaults():
    request = create_test_request()

    assert request.method == "GET"
    assert request.destination.host == "test.aws.dev"
    assert request.destination.path is None
    assert request.body == b""
    assert len(request.fields) == 0


def test_create_test_request_custom_values():
    request = create_test_request(
        method="POST",
        host="api.example.com",
        path="/users",
        headers=[
            ("Content-Type", "application/json"),
            ("Authorization", "AWS4-HMAC-SHA256"),
        ],
        body=b'{"name": "test"}',
    )

    assert request.method == "POST"
    assert request.destination.host == "api.example.com"
    assert request.destination.path == "/users"
    assert request.body == b'{"name": "test"}'

    assert "Content-Type" in request.fields
    assert request.fields["Content-Type"].as_string() == "application/json"
    assert "Authorization" in request.fields
    assert request.fields["Authorization"].as_string() == "AWS4-HMAC-SHA256"


def test_create_test_request_empty_headers():
    request = create_test_request(headers=[])
    assert len(request.fields) == 0
