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

import pathlib
import re
from datetime import datetime, timezone
from hashlib import sha256
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from typing import AsyncIterable, Generator, Literal
from urllib.parse import parse_qs, quote, urlparse

import pytest
from freezegun import freeze_time
from smithy_python._private import URI, Field, Fields
from smithy_python._private.http import HTTPRequest
from smithy_python._private.identity import Identity
from smithy_python.async_utils import async_list
from smithy_python.exceptions import SmithyIdentityException

from aws_smithy_python.auth import (
    EMPTY_SHA256_HASH,
    PAYLOAD_BUFFER,
    SIGV4_TIMESTAMP_FORMAT,
    STREAMING_UNSIGNED_PAYLOAD_TRAILER,
    UNSIGNED_PAYLOAD,
    SigV4Signer,
    SigV4SigningProperties,
)
from aws_smithy_python.identity import AWSCredentialIdentity

SECRET_KEY: Literal[
    "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY"
] = "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY"
ACCESS_KEY: Literal["AKIDEXAMPLE"] = "AKIDEXAMPLE"
SESSION_TOKEN: Literal["ABCDEFG/////123456"] = "ABCDEFG/////123456"
TOKEN_PATTERN: re.Pattern[str] = re.compile(
    r"^x-amz-security-token:(.*)$", re.MULTILINE
)
DATE: datetime = datetime(2015, 8, 30, 12, 36, 0, tzinfo=timezone.utc)
SIGNING_PROPERTIES: SigV4SigningProperties = {
    "service": "service",
    "region": "us-east-1",
}
TESTSUITE_DIR: pathlib.Path = (
    pathlib.Path(__file__).absolute().parent / "aws4_testsuite"
)
SIGV4_REQUIRED_QUERY_PARAMS: tuple[str, str, str, str, str, str] = (
    "X-Amz-Algorithm",
    "X-Amz-Credential",
    "X-Amz-Date",
    "X-Amz-Expires",
    "X-Amz-SignedHeaders",
    "X-Amz-Signature",
)


@pytest.fixture(scope="module")
def http_request() -> HTTPRequest:
    return HTTPRequest(
        destination=URI(host="example.com"),
        fields=Fields(
            [
                Field(name="host", values=["example.com"]),
                Field(name="foo", values=["bar"]),
                Field(name="X-Amz-Content-SHA256", values=["foo"]),
                Field(name="x-amzn-trace-id", values=["bar"]),
            ]
        ),
        method="GET",
        body=async_list([b"foo"]),
    )


@pytest.fixture(scope="module")
def aws_credential_identity() -> AWSCredentialIdentity:
    return AWSCredentialIdentity(
        access_key_id=ACCESS_KEY,
        secret_access_key=SECRET_KEY,
        session_token=SESSION_TOKEN,
    )


class FakeIdentity(Identity):
    ...


@pytest.fixture(scope="module")
def fake_identity() -> FakeIdentity:
    return FakeIdentity()


@pytest.fixture(scope="module")
def sigv4_signer() -> SigV4Signer:
    return SigV4Signer()


class FakeSigV4Signer(SigV4Signer):
    ...


@pytest.fixture(scope="module")
def fake_sigv4_signer() -> FakeSigV4Signer:
    return FakeSigV4Signer()


class RawRequest(BaseHTTPRequestHandler):
    def __init__(self, raw_request: bytes):
        self.rfile: BytesIO = BytesIO(raw_request)
        self.raw_requestline: bytes = self.rfile.readline()
        self.error_code: int | None = None
        self.error_message: str | None = None
        self.parse_request()

    def send_error(
        self, code: int, message: str | None = None, explain: str | None = None
    ) -> None:
        self.error_code = code
        self.error_message = message


def _generate_test_case(path: pathlib.Path) -> tuple[bytes, str, str, str, str | None]:
    raw_request = (path / f"{path.name}.req").read_bytes()
    canonical_request = (path / f"{path.name}.creq").read_text().replace("\r", "")
    string_to_sign = (path / f"{path.name}.sts").read_text().replace("\r", "")
    authorization_header = (path / f"{path.name}.authz").read_text()

    token_match = TOKEN_PATTERN.search(canonical_request)
    token = token_match.group(1) if token_match else None

    return (raw_request, canonical_request, string_to_sign, authorization_header, token)


def _is_valid_test_case(path: pathlib.Path) -> bool:
    return path.is_dir() and any(f.suffix.endswith(".req") for f in path.iterdir())


def generate_test_cases(
    test_path: pathlib.Path,
) -> Generator[tuple[bytes, str, str, str, str | None], None, None]:
    for path in test_path.glob("*"):
        if _is_valid_test_case(path):
            yield _generate_test_case(path)
        elif path.is_dir():
            yield from generate_test_cases(path)


def generate_async_byte_list(data: BytesIO) -> AsyncIterable[bytes]:
    stream = []
    part = data.read(PAYLOAD_BUFFER)
    while part:
        stream.append(part)
        part = data.read(PAYLOAD_BUFFER)
    return async_list(stream)


def smithy_request_from_raw_request(raw_request: bytes) -> HTTPRequest:
    decoded = raw_request.decode()
    # The BaseHTTPRequestHandler chokes on extra spaces in the path,
    # so we need to replace them with the URL encoded whitespace `%20`.
    if "example space" in decoded:
        decoded = decoded.replace("example space", "example%20space")
        raw_request = decoded.encode()
    raw = RawRequest(raw_request)
    if raw.error_code is not None:
        decoded = raw_request.decode()
        raise Exception(raw.error_message)

    request_method = raw.command
    fields = Fields()
    for k, v in raw.headers.items():
        try:
            field = fields.get_field(k)
            field.add(v)
        except KeyError:
            field = Field(name=k, values=[v])
            fields.set_field(field)
    body = generate_async_byte_list(raw.rfile)
    # For whatever reason, the BaseHTTPRequestHandler encodes
    # the first line of the response as 'iso-8859-1',
    # so we need to decode this into utf-8.
    if isinstance(path := raw.path, str):
        path = path.encode("iso-8859-1").decode("utf-8")
    if "?" in path:
        path, query = path.split("?", 1)
    else:
        query = ""
    host = raw.headers.get("host", "")
    url = URI(host=host, path=path, query=query)
    return HTTPRequest(
        destination=url,
        method=request_method,
        fields=fields,
        body=body,
    )


@pytest.mark.parametrize(
    "raw_request, canonical_request, string_to_sign, authorization_header, token",
    generate_test_cases(TESTSUITE_DIR),
)
@pytest.mark.asyncio
@freeze_time(DATE)
async def test_sigv4_signing_components(
    sigv4_signer: SigV4Signer,
    raw_request: bytes,
    canonical_request: str,
    string_to_sign: str,
    authorization_header: str,
    token: str | None,
) -> None:
    identity = AWSCredentialIdentity(
        access_key_id=ACCESS_KEY, secret_access_key=SECRET_KEY, session_token=token
    )
    request = smithy_request_from_raw_request(raw_request)
    sigv4_signer._validate_identity_and_signing_properties(identity, SIGNING_PROPERTIES)
    date = sigv4_signer._get_current_time().strftime(SIGV4_TIMESTAMP_FORMAT)
    headers_to_add = Fields([Field(name="X-Amz-Date", values=[date])])
    if identity.session_token:
        headers_to_add.set_field(
            Field(name="X-Amz-Security-Token", values=[identity.session_token])
        )
    new_request = await sigv4_signer._generate_new_request_before_signing(
        request, headers_to_add
    )
    formatted_headers = sigv4_signer._format_headers_for_signing(new_request)
    signed_headers = ";".join(formatted_headers)
    actual_canonical_request = await sigv4_signer._canonical_request(
        new_request, formatted_headers, signed_headers, SIGNING_PROPERTIES
    )
    assert actual_canonical_request == canonical_request
    request = smithy_request_from_raw_request(raw_request)
    scope = sigv4_signer._scope(date, SIGNING_PROPERTIES)
    actual_string_to_sign = sigv4_signer._string_to_sign(
        actual_canonical_request, date, scope
    )
    assert actual_string_to_sign == string_to_sign


@pytest.mark.parametrize(
    "raw_request, canonical_request, string_to_sign, authorization_header, token",
    generate_test_cases(TESTSUITE_DIR),
)
@pytest.mark.asyncio
@freeze_time(DATE)
async def test_sigv4_signing(
    sigv4_signer: SigV4Signer,
    raw_request: bytes,
    canonical_request: str,
    string_to_sign: str,
    authorization_header: str,
    token: str | None,
) -> None:
    identity = AWSCredentialIdentity(
        access_key_id=ACCESS_KEY, secret_access_key=SECRET_KEY, session_token=token
    )
    request = smithy_request_from_raw_request(raw_request)
    new_request = await sigv4_signer.sign(
        http_request=request, identity=identity, signing_properties=SIGNING_PROPERTIES
    )
    actual_auth_header = new_request.fields.get_field("Authorization").as_string()
    assert actual_auth_header == authorization_header


@pytest.mark.parametrize(
    "raw_request, canonical_request, string_to_sign, authorization_header, token",
    generate_test_cases(TESTSUITE_DIR),
)
@pytest.mark.asyncio
@freeze_time(DATE)
async def test_sigv4_generate_presigned_url(
    sigv4_signer: SigV4Signer,
    raw_request: bytes,
    canonical_request: str,
    string_to_sign: str,
    authorization_header: str,
    token: str | None,
) -> None:
    identity = AWSCredentialIdentity(
        access_key_id=ACCESS_KEY, secret_access_key=SECRET_KEY, session_token=token
    )
    request = smithy_request_from_raw_request(raw_request)
    # Only identities with a session token can generate presigned URLs.
    if token is not None:
        url = await sigv4_signer.generate_presigned_url(
            http_request=request,
            identity=identity,
            signing_properties=SIGNING_PROPERTIES,
        )
        parsed_url = urlparse(url)
        parsed_query = parse_qs(parsed_url.query)
        for param in SIGV4_REQUIRED_QUERY_PARAMS:
            assert param in parsed_query

    else:
        with pytest.raises(SmithyIdentityException):
            await sigv4_signer.generate_presigned_url(
                http_request=request,
                identity=identity,
                signing_properties=SIGNING_PROPERTIES,
            )


@pytest.mark.asyncio
async def test_sigv4_generate_presigned_url_with_expires(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    aws_credential_identity: AWSCredentialIdentity,
) -> None:
    signing_properties = SIGNING_PROPERTIES.copy()
    expires = 10000
    signing_properties["expires"] = expires
    url = await sigv4_signer.generate_presigned_url(
        http_request=http_request,
        identity=aws_credential_identity,
        signing_properties=signing_properties,
    )
    parsed_url = urlparse(url)
    parsed_query = parse_qs(parsed_url.query)
    assert "X-Amz-Expires" in parsed_query
    assert parsed_query["X-Amz-Expires"][0] == str(expires)


@pytest.mark.asyncio
async def test_sigv4_generate_presigned_url_with_additional_query_params(
    sigv4_signer: SigV4Signer,
    aws_credential_identity: AWSCredentialIdentity,
) -> None:
    http_request = HTTPRequest(
        method="GET",
        destination=URI(host="example.com", query="foo=bar&baz=qux"),
        fields=Fields(),
        body=async_list([]),
    )
    url = await sigv4_signer.generate_presigned_url(
        http_request=http_request,
        identity=aws_credential_identity,
        signing_properties=SIGNING_PROPERTIES,
    )
    parsed_url = urlparse(url)
    parsed_query = parse_qs(parsed_url.query)
    assert "foo" in parsed_query
    assert parsed_query["foo"][0] == "bar"
    assert "baz" in parsed_query
    assert parsed_query["baz"][0] == "qux"


@freeze_time(DATE)
def test_get_current_time(sigv4_signer: SigV4Signer) -> None:
    assert sigv4_signer._get_current_time() == DATE


@pytest.mark.asyncio
async def test_sign_wrong_identity_type_raises(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    fake_identity: AWSCredentialIdentity,
) -> None:
    with pytest.raises(SmithyIdentityException):
        await sigv4_signer.sign(
            http_request=http_request,
            identity=fake_identity,
            signing_properties={"region": "us-east-1", "service": "s3"},
        )


@pytest.mark.parametrize(
    "signing_properties",
    [{"region": "us-east-1"}, {"foo": "bar"}, {}, {"service": "s3"}],
)
@pytest.mark.asyncio
async def test_missing_required_signing_properties_raises(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    aws_credential_identity: AWSCredentialIdentity,
    signing_properties: SigV4SigningProperties,
) -> None:
    with pytest.raises(SmithyIdentityException):
        await sigv4_signer.sign(
            http_request=http_request,
            identity=aws_credential_identity,
            signing_properties=signing_properties,
        )
    with pytest.raises(SmithyIdentityException):
        await sigv4_signer.generate_presigned_url(
            http_request=http_request,
            identity=aws_credential_identity,
            signing_properties=signing_properties,
        )


@pytest.mark.asyncio
async def test_generate_presigned_url_no_session_token_raises(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
) -> None:
    identity = AWSCredentialIdentity(
        access_key_id=ACCESS_KEY, secret_access_key=SECRET_KEY, session_token=None
    )
    with pytest.raises(SmithyIdentityException):
        await sigv4_signer.generate_presigned_url(
            http_request=http_request,
            identity=identity,
            signing_properties=SIGNING_PROPERTIES,
        )


@pytest.mark.asyncio
async def test_sigv4_sign_s3_content_sha_header(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
) -> None:
    headers_to_add = Fields(
        [
            Field(
                name="X-Amz-Date",
                values=[
                    sigv4_signer._get_current_time().strftime(SIGV4_TIMESTAMP_FORMAT)
                ],
            ),
            Field(
                name="X-Amz-Content-SHA256",
                values=[await sigv4_signer._payload(http_request, SIGNING_PROPERTIES)],
            ),
        ]
    )
    request = await sigv4_signer._generate_new_request_before_signing(
        http_request=http_request,
        headers_to_add=headers_to_add,
    )
    try:
        content_sha_header = request.fields.get_field("X-Amz-Content-SHA256")
    except KeyError:
        pytest.fail("X-Amz-Content-SHA256 header not found")
    assert content_sha_header.as_string() == sha256(b"foo").hexdigest()


@pytest.mark.parametrize(
    "signing_properties, expected_result",
    [
        ({"foo": "bar"}, False),
        ({"checksum": {"foo": "bar"}}, False),
        ({"checksum": {"request_algorithm": {}}}, False),
        ({"checksum": {"request_algorithm": {"foo": "bar"}}}, False),
        ({"checksum": {"request_algorithm": {"in": "foo"}}}, False),
        ({"checksum": {"request_algorithm": {"in": "trailer"}}}, True),
    ],
)
def test_is_streaming_checksum_payload(
    sigv4_signer: SigV4Signer,
    signing_properties: SigV4SigningProperties,
    expected_result: bool,
) -> None:
    actual_result = sigv4_signer._is_streaming_checksum_payload(signing_properties)
    assert actual_result == expected_result


@pytest.mark.parametrize(
    "aws_request, signing_properties, expected_result",
    [
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
            {},
            True,
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com", scheme="http"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
            {},
            True,
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
            {"payload_signing_enabled": False},
            False,
        ),
    ],
)
def test_should_sha256_sign_payload(
    sigv4_signer: SigV4Signer,
    aws_request: HTTPRequest,
    signing_properties: SigV4SigningProperties,
    expected_result: bool,
) -> None:
    should_sign_payload = sigv4_signer._should_sha256_sign_payload(
        aws_request, signing_properties
    )
    assert should_sign_payload == expected_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "http_request, signing_properties, for_presigning, expected_payload",
    [
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            False,
            EMPTY_SHA256_HASH,
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([b"foo"]),
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            False,
            sha256(b"foo").hexdigest(),
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            True,
            UNSIGNED_PAYLOAD,
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
            {"payload_signing_enabled": False, "region": "us-east-1", "service": "s3"},
            False,
            UNSIGNED_PAYLOAD,
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
            {
                "checksum": {"request_algorithm": {"in": "trailer"}},
                "region": "us-east-1",
                "service": "s3",
            },
            False,
            STREAMING_UNSIGNED_PAYLOAD_TRAILER,
        ),
    ],
)
async def test_payload(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    signing_properties: SigV4SigningProperties,
    for_presigning: bool,
    expected_payload: str,
) -> None:
    payload = await sigv4_signer._payload(
        http_request, signing_properties, for_presigning
    )
    assert payload == expected_payload


@pytest.mark.parametrize(
    "http_request, expected_headers",
    [
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
            {"host": "example.com"},
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields([Field(name="foo", values=["bar"])]),
            ),
            {"foo": "bar", "host": "example.com"},
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields([Field(name="foo", values=["bar", "baz"])]),
            ),
            {"foo": "bar,baz", "host": "example.com"},
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields([Field(name="host", values=["foo"])]),
            ),
            {"host": "foo"},
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(
                    [
                        Field(name="expect", values=["100-continue"]),
                        Field(name="user-agent", values=["foo"]),
                        Field(
                            name="x-amzn-trace-id",
                            values=["Root=1-5759e988-bd862e3fe1be46a994272793"],
                        ),
                    ]
                ),
            ),
            {"host": "example.com"},
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(
                    [
                        Field(name="authorization", values=["foo"]),
                        Field(name="x-amz-content-sha256", values=["baz"]),
                    ]
                ),
            ),
            {"host": "example.com"},
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com", port=8080),
                body=async_list([]),
                method="GET",
                fields=Fields(
                    [
                        Field(name="authorization", values=["foo"]),
                        Field(name="x-amz-content-sha256", values=["baz"]),
                    ]
                ),
            ),
            {"host": "example.com:8080"},
        ),
        (
            HTTPRequest(
                destination=URI(
                    host="example.com", port=8080, username="foo", password="bar"
                ),
                body=async_list([]),
                method="GET",
                fields=Fields(
                    [
                        Field(name="authorization", values=["foo"]),
                        Field(name="x-amz-content-sha256", values=["baz"]),
                    ]
                ),
            ),
            {"host": "foo:bar@example.com:8080"},
        ),
    ],
)
def test_format_headers_for_signing(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    expected_headers: dict[str, str],
) -> None:
    formatted_headers = sigv4_signer._format_headers_for_signing(http_request)
    assert formatted_headers == expected_headers


@pytest.mark.parametrize(
    "http_request, date, credential_scope, expires, signed_headers",
    [
        (
            HTTPRequest(
                destination=URI(host="example.com", query="foo=bar"),
                method="GET",
                fields=Fields(
                    [
                        Field(name="X-Amz-Security-Token", values=[SESSION_TOKEN]),
                        Field(name="foo", values=["bar"]),
                    ]
                ),
                body=async_list([]),
            ),
            "20230214",
            "foo//",
            1000,
            "host;x-amz-date",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                method="GET",
                fields=Fields(
                    [Field(name="X-Amz-Security-Token", values=[SESSION_TOKEN])]
                ),
                body=async_list([]),
            ),
            "20230214",
            "foo//",
            1000,
            "host;x-amz-date",
        ),
    ],
)
def test_generate_url_query_params(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    date: str,
    credential_scope: str,
    expires: int,
    signed_headers: str,
) -> None:
    url_query = sigv4_signer._generate_url_query_params(
        http_request=http_request,
        date=date,
        credential_scope=credential_scope,
        expires=expires,
        signed_headers=signed_headers,
        session_token=SESSION_TOKEN,
    )
    assert f"X-Amz-SignedHeaders={signed_headers}" in url_query
    assert f"X-Amz-Expires={expires}" in url_query
    assert f"X-Amz-Date={date}" in url_query
    for field in http_request.fields:
        assert f"{field.name}={quote(field.as_string(), safe='')}" in url_query


@pytest.mark.asyncio
@freeze_time(DATE)
@pytest.mark.parametrize(
    "http_request, headers_to_add, expected_request",
    [
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(
                    [
                        Field(name="X-Amz-Security-Token", values=[SESSION_TOKEN]),
                        Field(name="X-Amz-Content-SHA256", values=[EMPTY_SHA256_HASH]),
                    ]
                ),
            ),
            Fields(),
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
            Fields([Field(name="foo", values=["bar"])]),
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields([Field(name="foo", values=["bar"])]),
            ),
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
            Fields(),
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(),
            ),
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields([Field(name="foo", values=["bar"])]),
            ),
            Fields(),
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields([Field(name="foo", values=["bar"])]),
            ),
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields(
                    [
                        Field(name="foo", values=["bar"]),
                        Field(name="authorization", values=["baz"]),
                        Field(name="x-amz-date", values=["qux"]),
                        Field(name="x-amz-security-token", values=["quux"]),
                        Field(name="x-amz-content-sha256", values=["quuz"]),
                    ]
                ),
            ),
            Fields(),
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([]),
                method="GET",
                fields=Fields([Field(name="foo", values=["bar"])]),
            ),
        ),
    ],
)
async def test_generate_new_request_before_signing(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    headers_to_add: Fields,
    expected_request: HTTPRequest,
) -> None:
    new_request = await sigv4_signer._generate_new_request_before_signing(
        http_request, headers_to_add
    )
    for field in new_request.fields:
        assert field == expected_request.fields.get_field(field.name)
    assert new_request.method == expected_request.method
    assert new_request.destination == expected_request.destination
    assert await new_request.consume_body() == await expected_request.consume_body()
