# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from io import BytesIO
from typing import Any

import pytest
from awscrt import auth as awscrt_auth
from awscrt import http as awscrt_http
from smithy_python._private.auth import Identity
from smithy_python._private.http import URI, Request
from smithy_python.exceptions import SmithyIdentityException
from smithy_python.interfaces import identity as identity_interface

from aws_smithy_python.auth import AwsSigV4Signer
from aws_smithy_python.identity import AwsCredentialIdentity

# from smithy_python.interfaces.http import HeadersList


@pytest.fixture(scope="module")
def sigv4_signer() -> AwsSigV4Signer:
    return AwsSigV4Signer()


@pytest.fixture(scope="module")
def http_request() -> Request:
    return Request(
        URI("example.com"),
        headers=[
            ("host", "example.com"),
            ("foo", "bar"),
            ("X-Amz-Content-SHA256", "foo"),
            ("x-amzn-trace-id", "bar"),
        ],
    )


class FakeIdentity(Identity):
    ...


@pytest.fixture(scope="module")
def fake_identity() -> FakeIdentity:
    return FakeIdentity()


@pytest.fixture(scope="module")
def aws_credential_identity() -> AwsCredentialIdentity:
    return AwsCredentialIdentity(
        access_key_id="access_key",
        secret_key_id="secret_key",
        session_token="session_token",
    )


class FakeSigV4Signer(AwsSigV4Signer):
    SIGNATURE_TYPE: awscrt_auth.AwsSignatureType = (
        awscrt_auth.AwsSignatureType.HTTP_REQUEST_HEADERS
    )
    ALGORITHM: awscrt_auth.AwsSigningAlgorithm = awscrt_auth.AwsSigningAlgorithm.V4
    USE_DOUBLE_URI_ENCODE: bool = True
    SHOULD_NORMALIZE_URI_PATH: bool = True
    SHOULD_GET_EXISTING_SHA256: bool = False
    USES_EXPIRATION: bool = False


@pytest.fixture(scope="module")
def fake_sigv4_signer() -> FakeSigV4Signer:
    return FakeSigV4Signer()


def test_wrong_identity_type_raises(
    sigv4_signer: AwsSigV4Signer,
    http_request: Request,
    fake_identity: identity_interface.Identity,
) -> None:
    with pytest.raises(SmithyIdentityException):
        sigv4_signer.sign(
            http_request=http_request, identity=fake_identity, signing_properties={}
        )


@pytest.mark.parametrize(
    "signing_properties",
    [{"region": "us-east-1"}, {"foo": "bar"}, {}, {"service": "s3"}],
)
def test_missing_required_signing_properties_raises(
    sigv4_signer: AwsSigV4Signer,
    http_request: Request,
    aws_credential_identity: identity_interface.Identity,
    signing_properties: dict[str, Any],
) -> None:
    with pytest.raises(SmithyIdentityException):
        sigv4_signer.sign(
            http_request=http_request,
            identity=aws_credential_identity,
            signing_properties=signing_properties,
        )


@pytest.mark.parametrize(
    "aws_request, signing_properties, expected_headers",
    [
        (
            Request(
                URI("example.com"),
                headers=[
                    ("expect", "yes"),
                    ("foo", "bar"),
                    ("X-Amz-Content-SHA256", "helloworld"),
                    ("Authorization", "Bearer 12345abcdefg"),
                    ("X-Amz-Date", "20230109T20013Z"),
                    ("X-Amz-Security-Token", "12345abcdefg"),
                ],
            ),
            {"region": "us-east-1", "service": "s3"},
            {
                "host": "example.com",
                "foo": "bar",
                "expect": "yes",
                "x-amz-content-sha256": "helloworld",
            },
        ),
        (
            Request(
                URI(host="example.com", scheme="https"),
                headers=[("expect", "yes"), ("foo", "bar")],
            ),
            {"region": "us-east-1", "service": "s3", "payload_signing_enabled": False},
            {
                "host": "example.com",
                "foo": "bar",
                "expect": "yes",
                "x-amz-content-sha256": "UNSIGNED-PAYLOAD",
            },
        ),
        (
            Request(URI(host="example.com", scheme="https"), headers=[]),
            {"region": "us-east-1", "service": "s3"},
            {"host": "example.com"},
        ),
        (
            Request(URI(host="example.com", scheme="https"), headers=[]),
            {
                "region": "us-east-1",
                "service": "s3",
                "checksum": {"request_algorithm": {"in": "trailer"}},
            },
            {
                "host": "example.com",
                "x-amz-content-sha256": "STREAMING-UNSIGNED-PAYLOAD-TRAILER",
            },
        ),
    ],
)
def test_sign(
    sigv4_signer: AwsSigV4Signer,
    aws_request: Request,
    aws_credential_identity: identity_interface.Identity,
    signing_properties: dict[str, Any],
    expected_headers: dict[str, str],
) -> None:
    sigv4_signer.sign(aws_request, aws_credential_identity, signing_properties)
    headers = aws_request.headers
    assert sigv4_signer._get_header(headers, "X-Amz-Date") is not None
    for name, value in expected_headers.items():
        assert sigv4_signer._get_header(headers, name) == value
    authorization = sigv4_signer._get_header(headers, "Authorization")
    assert authorization is not None
    assert authorization.startswith("AWS4-HMAC-SHA256 Credential=")
    assert signing_properties["region"] in authorization
    assert signing_properties["service"] in authorization
    assert "SignedHeaders=" in authorization
    assert isinstance(aws_credential_identity, AwsCredentialIdentity)
    assert aws_credential_identity.access_key_id in authorization


@pytest.mark.parametrize(
    "smithy_request, expected_crt_request",
    [
        (
            Request(URI("example.com")),
            awscrt_http.HttpRequest(
                method="GET",
                path="/",
                headers=awscrt_http.HttpHeaders([]),
                body_stream=None,
            ),
        ),
        (
            Request(URI("example.com", path="/foo")),
            awscrt_http.HttpRequest(
                method="GET",
                path="/foo",
                headers=awscrt_http.HttpHeaders([]),
                body_stream=None,
            ),
        ),
        (
            Request(URI("example.com", path="/foo", query="hello=world")),
            awscrt_http.HttpRequest(
                method="GET",
                path="/foo?hello=world",
                headers=awscrt_http.HttpHeaders([]),
                body_stream=None,
            ),
        ),
        (
            Request(URI("example.com"), method="POST"),
            awscrt_http.HttpRequest(
                method="POST",
                path="/",
                headers=awscrt_http.HttpHeaders([]),
                body_stream=None,
            ),
        ),
        (
            Request(URI("example.com"), headers=[("foo", "bar")]),
            awscrt_http.HttpRequest(
                method="GET",
                path="/",
                headers=awscrt_http.HttpHeaders([("foo", "bar")]),
                body_stream=None,
            ),
        ),
        (
            Request(URI("example.com"), body=b"foo"),
            awscrt_http.HttpRequest(
                method="GET",
                path="/",
                headers=awscrt_http.HttpHeaders([]),
                body_stream=BytesIO(b"foo"),
            ),
        ),
        (
            Request(URI("example.com"), body=BytesIO(b"foo")),
            awscrt_http.HttpRequest(
                method="GET",
                path="/",
                headers=awscrt_http.HttpHeaders([]),
                body_stream=BytesIO(b"foo"),
            ),
        ),
        (
            Request(URI("example.com"), body=BytesIO(b"foo")),
            awscrt_http.HttpRequest(
                method="GET",
                path="/",
                headers=awscrt_http.HttpHeaders([]),
                body_stream=BytesIO(b"foo"),
            ),
        ),
    ],
)
def test_crt_request_from_smithy_request(
    sigv4_signer: AwsSigV4Signer,
    smithy_request: Request,
    expected_crt_request: awscrt_http.HttpRequest,
) -> None:
    actual_crt_request = sigv4_signer._crt_request_from_smithy_request(smithy_request)
    assert actual_crt_request.method == expected_crt_request.method
    assert actual_crt_request.path == expected_crt_request.path
    assert list(actual_crt_request.headers) == list(expected_crt_request.headers)
    if actual_crt_request.body_stream is not None:
        actual_stream = actual_crt_request.body_stream._stream.read()
        expected_stream = expected_crt_request.body_stream._stream.read()
        assert actual_stream == expected_stream
    else:
        assert actual_crt_request.body_stream == expected_crt_request.body_stream


@pytest.mark.parametrize(
    "header_name, expected_value",
    [
        ("host", "example.com"),
        ("foo", "bar"),
        ("bar", None),
    ],
)
def test_get_header(
    sigv4_signer: AwsSigV4Signer,
    http_request: Request,
    header_name: str,
    expected_value: Any,
) -> None:
    assert sigv4_signer._get_header(http_request.headers, header_name) == expected_value


@pytest.mark.parametrize(
    "signing_properties, expected_result",
    [
        ({"foo": "bar"}, False),
        ({"checksum": {"foo": "bar"}}, False),
        ({"checksum": {"request_algorithm": "foo"}}, False),
        ({"checksum": {"request_algorithm": {"foo": "bar"}}}, False),
        ({"checksum": {"request_algorithm": {"in": "foo"}}}, False),
        ({"checksum": {"request_algorithm": {"in": "trailer"}}}, True),
    ],
)
def test_is_streaming_checksum_payload(
    sigv4_signer: AwsSigV4Signer,
    signing_properties: dict[str, Any],
    expected_result: bool,
) -> None:
    actual_result = sigv4_signer._is_streaming_checksum_payload(signing_properties)
    assert actual_result == expected_result


@pytest.mark.parametrize(
    "http_request, expected_header_value",
    [
        (Request(URI("example.com"), headers=[("X-Amz-Content-SHA256", "foo")]), "foo"),
        (Request(URI("example.com"), headers=[("foo", "bar")]), None),
    ],
)
def test_get_existing_sha256(
    sigv4_signer: AwsSigV4Signer,
    fake_sigv4_signer: FakeSigV4Signer,
    http_request: Request,
    expected_header_value: str | None,
) -> None:
    assert sigv4_signer._get_existing_sha256(http_request) == expected_header_value
    assert fake_sigv4_signer._get_existing_sha256(http_request) is None


@pytest.mark.parametrize(
    "header_name, expected_result",
    [("user-agent", False), ("foo", True)],
)
def test_should_sign_header(
    sigv4_signer: AwsSigV4Signer, header_name: str, expected_result: bool
) -> None:
    assert sigv4_signer._should_sign_header(header_name) == expected_result


@pytest.mark.parametrize(
    "aws_request, signing_properties, expected_result",
    [
        (Request(URI("example.com")), {}, True),
        (Request(URI(host="example.com", scheme="http")), {}, True),
        (Request(URI("example.com")), {"payload_signing_enabled": False}, False),
    ],
)
def test_should_sha256_sign_payload(
    sigv4_signer: AwsSigV4Signer,
    aws_request: Request,
    signing_properties: dict[str, Any],
    expected_result: bool,
) -> None:
    should_sign_payload = sigv4_signer._should_sha256_sign_payload(
        signing_properties, aws_request
    )
    assert should_sign_payload == expected_result
