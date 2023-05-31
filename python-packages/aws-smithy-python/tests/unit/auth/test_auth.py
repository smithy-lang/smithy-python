# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
import warnings
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from typing import AsyncIterable, Generator

import pytest
from freezegun import freeze_time
from smithy_python._private import URI, Field, Fields
from smithy_python._private.http import HTTPRequest
from smithy_python._private.identity import Identity
from smithy_python.async_utils import async_list
from smithy_python.exceptions import SmithyHTTPException, SmithyIdentityException
from smithy_python.interfaces.blobs import AsyncBytesReader, SeekableAsyncBytesReader

from aws_smithy_python.auth import (
    EMPTY_SHA256_HASH,
    SIGV4_TIMESTAMP_FORMAT,
    UNSIGNED_PAYLOAD,
    SigV4Signer,
    SigV4SigningProperties,
)
from aws_smithy_python.identity import AWSCredentialIdentity

SECRET_KEY: str = "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY"
ACCESS_KEY: str = "AKIDEXAMPLE"
SESSION_TOKEN: str = "ABCDEFG/////123456"
TOKEN_PATTERN: re.Pattern[str] = re.compile(
    pattern=r"^x-amz-security-token:(.*)$", flags=re.MULTILINE
)
DATE: datetime = datetime(
    year=2015, month=8, day=30, hour=12, minute=36, second=0, tzinfo=timezone.utc
)
DATE_STR: str = DATE.strftime(SIGV4_TIMESTAMP_FORMAT)
SIGNING_PROPERTIES: SigV4SigningProperties = {
    "service": "service",
    "region": "us-east-1",
}
DISABLED_SIGNING_PROPERTIES: SigV4SigningProperties = {
    "service": "service",
    "region": "us-east-1",
    "payload_signing_enabled": False,
}
TESTSUITE_DIR: pathlib.Path = (
    pathlib.Path(__file__).absolute().parent / "aws4_testsuite"
)
EMPTY_ASYNC_LIST: AsyncIterable[bytes] = async_list(lst=[])
EMPTY_ASYNC_BYTES_READER: AsyncBytesReader = AsyncBytesReader(data=async_list(lst=[]))
EMPTY_SEEKABLE_ASYNC_BYTES_READER: SeekableAsyncBytesReader = SeekableAsyncBytesReader(
    data=async_list(lst=[])
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
        body=AsyncBytesReader(data=async_list([b"foo"])),
    )


@pytest.fixture(scope="module")
def http_request_with_user_provided_security_token() -> HTTPRequest:
    return HTTPRequest(
        destination=URI(host="example.com"),
        body=EMPTY_ASYNC_BYTES_READER,
        method="GET",
        fields=Fields(initial=[Field(name="X-Amz-Security-Token", values=["foo"])]),
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


def generate_test_cases(
    test_path: pathlib.Path,
) -> Generator[tuple[HTTPRequest, AWSCredentialIdentity, str, str, str], None, None]:
    for path in test_path.glob("*"):
        if _is_valid_test_case(path=path):
            yield _generate_test_case(path=path)
        elif path.is_dir():
            yield from generate_test_cases(test_path=path)


def _is_valid_test_case(path: pathlib.Path) -> bool:
    return path.is_dir() and any(f.suffix.endswith(".req") for f in path.iterdir())


def _generate_test_case(
    path: pathlib.Path,
) -> tuple[HTTPRequest, AWSCredentialIdentity, str, str, str]:
    raw_request = (path / f"{path.name}.req").read_bytes()
    canonical_request = (path / f"{path.name}.creq").read_text()
    string_to_sign = (path / f"{path.name}.sts").read_text()
    authorization_header = (path / f"{path.name}.authz").read_text()

    token_match = TOKEN_PATTERN.search(string=canonical_request)
    token = token_match.group(1) if token_match else None
    smithy_request = _smithy_request_from_raw_request(
        raw_request=raw_request, token=token
    )

    return (
        smithy_request,
        AWSCredentialIdentity(
            access_key_id=ACCESS_KEY, secret_access_key=SECRET_KEY, session_token=token
        ),
        canonical_request,
        string_to_sign,
        authorization_header,
    )


class RawRequest(BaseHTTPRequestHandler):
    def __init__(self, raw_request: bytes):
        self.rfile: BytesIO = BytesIO(initial_bytes=raw_request)
        self.raw_requestline: bytes = self.rfile.readline()
        self.error_code: int | None = None
        self.error_message: str | None = None
        self.parse_request()

    def send_error(
        self, code: int, message: str | None = None, explain: str | None = None
    ) -> None:
        self.error_code = code
        self.error_message = message


def _smithy_request_from_raw_request(
    raw_request: bytes, token: str | None = None
) -> HTTPRequest:
    decoded = raw_request.decode()
    # The BaseHTTPRequestHandler chokes on extra spaces in the path,
    # so we need to replace them with the URL encoded whitespace `%20`.
    if "example space" in decoded:
        decoded = decoded.replace("example space", "example%20space")
        raw_request = decoded.encode()
    raw = RawRequest(raw_request=raw_request)
    if raw.error_code is not None:
        decoded = raw_request.decode()
        raise Exception(raw.error_message)

    request_method = raw.command
    fields = Fields()
    for k, v in raw.headers.items():
        if k in fields:
            field = fields.get_field(name=k)
            field.add(value=v)
        else:
            field = Field(name=k, values=[v])
            fields.set_field(field=field)
    fields.set_field(Field(name="X-Amz-Date", values=[DATE_STR]))
    if token is not None:
        fields.set_field(Field(name="X-Amz-Security-Token", values=[token]))
    body = _generate_async_list(data=raw.rfile)
    # For whatever reason, the BaseHTTPRequestHandler encodes
    # the first line of the response as 'iso-8859-1',
    # so we need to decode this into utf-8.
    if isinstance(path := raw.path, str):
        path = path.encode(encoding="iso-8859-1").decode(encoding="utf-8")
    if "?" in path:
        path, query = path.split(sep="?", maxsplit=1)
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


def _generate_async_list(data: BytesIO) -> AsyncIterable[bytes]:
    stream = []
    while True:
        part = data.read()
        if not part:
            break
        stream.append(part)
    return async_list(lst=stream)


@pytest.mark.parametrize(
    argnames="http_request, identity, canonical_request, string_to_sign, authorization_header",
    argvalues=generate_test_cases(test_path=TESTSUITE_DIR),
)
@pytest.mark.asyncio
@freeze_time(time_to_freeze=DATE)
async def test_sigv4_signing(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    identity: AWSCredentialIdentity,
    canonical_request: str,
    string_to_sign: str,
    authorization_header: str,
) -> None:
    with pytest.warns(UserWarning, match="Payload signing is enabled"):
        actual_canonical_request = await sigv4_signer.canonical_request(
            http_request=http_request,
            signing_properties=SIGNING_PROPERTIES,
        )
        assert actual_canonical_request == canonical_request
        actual_string_to_sign = sigv4_signer.string_to_sign(
            canonical_request=actual_canonical_request,
            signing_properties=SIGNING_PROPERTIES,
        )
        assert actual_string_to_sign == string_to_sign
        new_request = await sigv4_signer.sign(
            http_request=http_request,
            identity=identity,
            signing_properties=SIGNING_PROPERTIES,
        )
    actual_auth_header = new_request.fields.get_field(name="Authorization").as_string()
    assert actual_auth_header == authorization_header


@pytest.mark.asyncio
async def test_sign_wrong_identity_type_raises(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    fake_identity: FakeIdentity,
) -> None:
    # Ignore mypy while we test passing the wrong type raises an error.
    with pytest.raises(expected_exception=SmithyIdentityException):
        await sigv4_signer.sign(
            http_request=http_request,
            identity=fake_identity,  # type: ignore
            signing_properties={"region": "us-east-1", "service": "s3"},
        )


@pytest.mark.parametrize(
    argnames="signing_properties",
    argvalues=[{"region": "us-east-1"}, {"foo": "bar"}, {}, {"service": "s3"}],
)
@pytest.mark.asyncio
async def test_missing_required_signing_properties_raises(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    aws_credential_identity: AWSCredentialIdentity,
    signing_properties: SigV4SigningProperties,
) -> None:
    with pytest.raises(expected_exception=SmithyHTTPException):
        await sigv4_signer.sign(
            http_request=http_request,
            identity=aws_credential_identity,
            signing_properties=signing_properties,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("http_request, signing_properties, expected_payload, expected_body"),
    argvalues=[
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=EMPTY_ASYNC_LIST,
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            EMPTY_SHA256_HASH,
            b"",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=EMPTY_ASYNC_BYTES_READER,
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            EMPTY_SHA256_HASH,
            b"",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=EMPTY_SEEKABLE_ASYNC_BYTES_READER,
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            EMPTY_SHA256_HASH,
            b"",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list([b"foo"]),
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            sha256(b"foo").hexdigest(),
            b"foo",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=AsyncBytesReader(data=async_list(lst=[b"foo"])),
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            sha256(b"foo").hexdigest(),
            b"foo",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=SeekableAsyncBytesReader(data=async_list(lst=[b"foo"])),
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            sha256(b"foo").hexdigest(),
            b"foo",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=async_list(lst=[b"foo", b"bar", b"hello", b"world"]),
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            sha256(b"foobarhelloworld").hexdigest(),
            b"foobarhelloworld",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=AsyncBytesReader(
                    data=async_list(lst=[b"foo", b"bar", b"hello", b"world"])
                ),
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            sha256(b"foobarhelloworld").hexdigest(),
            b"foobarhelloworld",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=SeekableAsyncBytesReader(
                    data=async_list(lst=[b"foo", b"bar", b"hello", b"world"])
                ),
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            sha256(b"foobarhelloworld").hexdigest(),
            b"foobarhelloworld",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com", scheme="http"),
                body=EMPTY_ASYNC_BYTES_READER,
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            EMPTY_SHA256_HASH,
            b"",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com", scheme="http"),
                body=EMPTY_SEEKABLE_ASYNC_BYTES_READER,
                method="GET",
                fields=Fields(),
            ),
            SIGNING_PROPERTIES,
            EMPTY_SHA256_HASH,
            b"",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=EMPTY_ASYNC_LIST,
                method="GET",
                fields=Fields(),
            ),
            DISABLED_SIGNING_PROPERTIES,
            UNSIGNED_PAYLOAD,
            b"",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=EMPTY_ASYNC_BYTES_READER,
                method="GET",
                fields=Fields(),
            ),
            DISABLED_SIGNING_PROPERTIES,
            UNSIGNED_PAYLOAD,
            b"",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com"),
                body=EMPTY_SEEKABLE_ASYNC_BYTES_READER,
                method="GET",
                fields=Fields(),
            ),
            DISABLED_SIGNING_PROPERTIES,
            UNSIGNED_PAYLOAD,
            b"",
        ),
    ],
)
@pytest.mark.filterwarnings("ignore:Payload signing is enabled")
async def test_payload(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    signing_properties: SigV4SigningProperties,
    expected_payload: str,
    expected_body: bytes,
) -> None:
    canonical_request = await sigv4_signer.canonical_request(
        http_request=http_request,
        signing_properties=signing_properties,
    )
    # payload is the last line of the canonical request
    payload = canonical_request.split("\n")[-1]
    assert payload == expected_payload
    # body stream should have been reset to the beginning
    assert await http_request.consume_body() == expected_body


@pytest.mark.parametrize(
    argnames="signing_properties, num_expected_warnings",
    argvalues=[(SIGNING_PROPERTIES, 1), (DISABLED_SIGNING_PROPERTIES, 0)],
)
@pytest.mark.asyncio
async def test_warnings(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    aws_credential_identity: AWSCredentialIdentity,
    signing_properties: SigV4SigningProperties,
    num_expected_warnings: int,
) -> None:
    with warnings.catch_warnings(record=True) as caught_warnings:
        await sigv4_signer.sign(
            http_request=http_request,
            identity=aws_credential_identity,
            signing_properties=signing_properties,
        )
    filtered_warnings = [
        w
        for w in caught_warnings
        if w.category == UserWarning and "Payload signing is enabled" in str(w.message)
    ]
    assert len(filtered_warnings) == num_expected_warnings


@pytest.mark.asyncio
async def test_user_provided_token_header_removed(
    sigv4_signer: SigV4Signer,
    http_request_with_user_provided_security_token: HTTPRequest,
) -> None:
    identity = AWSCredentialIdentity(access_key_id="foo", secret_access_key="bar")
    with pytest.warns(UserWarning, match="Payload signing is enabled"):
        new_request = await sigv4_signer.sign(
            http_request=http_request_with_user_provided_security_token,
            identity=identity,
            signing_properties=SIGNING_PROPERTIES,
        )
    assert "X-Amz-Security-Token" not in new_request.fields


@pytest.mark.asyncio
async def test_replace_user_provided_token_header(
    sigv4_signer: SigV4Signer,
    http_request_with_user_provided_security_token: HTTPRequest,
    aws_credential_identity: AWSCredentialIdentity,
) -> None:

    with pytest.warns(UserWarning, match="Payload signing is enabled"):
        new_request = await sigv4_signer.sign(
            http_request=http_request_with_user_provided_security_token,
            identity=aws_credential_identity,
            signing_properties=SIGNING_PROPERTIES,
        )
    token_field = new_request.fields.get_field(name="X-Amz-Security-Token").as_string()
    assert token_field == aws_credential_identity.session_token


@pytest.mark.parametrize(
    argnames="http_request, expected_host",
    argvalues=[
        (
            HTTPRequest(
                destination=URI(host="example.com", port=443),
                body=EMPTY_ASYNC_LIST,
                method="GET",
                fields=Fields(),
            ),
            "example.com",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com", port=80),
                body=EMPTY_ASYNC_LIST,
                method="GET",
                fields=Fields(),
            ),
            "example.com:80",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com", port=443, scheme="http"),
                body=EMPTY_ASYNC_LIST,
                method="GET",
                fields=Fields(),
            ),
            "example.com:443",
        ),
        (
            HTTPRequest(
                destination=URI(host="example.com", port=80, scheme="http"),
                body=EMPTY_ASYNC_LIST,
                method="GET",
                fields=Fields(),
            ),
            "example.com",
        ),
    ],
)
@pytest.mark.asyncio
async def test_port_removed_from_host(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    expected_host: str,
) -> None:
    with pytest.warns(UserWarning, match="Payload signing is enabled"):
        cr = await sigv4_signer.canonical_request(
            http_request=http_request, signing_properties=SIGNING_PROPERTIES
        )
    # with the above examples `host` will always be on the fourth line of
    # the canonical request
    host_header = cr.splitlines()[3]
    assert host_header == f"host:{expected_host}"


@pytest.mark.asyncio
async def test_ephemeral_date(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    aws_credential_identity: AWSCredentialIdentity,
) -> None:
    signing_properties = SIGNING_PROPERTIES.copy()
    for num in range(1, 3):
        old_date = signing_properties.get("date")
        future_time = datetime.utcnow() + timedelta(minutes=num)
        with freeze_time(future_time):
            with pytest.warns(UserWarning, match="Payload signing is enabled"):
                new_request = await sigv4_signer.sign(
                    http_request=http_request,
                    identity=aws_credential_identity,
                    signing_properties=signing_properties,
                )
        new_date = signing_properties["date"]
        assert old_date != new_date
        assert new_request.fields.get_field("X-Amz-Date").as_string() == new_date


@pytest.mark.asyncio
async def test_non_ephemeral_date(
    sigv4_signer: SigV4Signer,
    http_request: HTTPRequest,
    aws_credential_identity: AWSCredentialIdentity,
) -> None:
    signing_properties = SIGNING_PROPERTIES.copy()
    signing_properties["date"] = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    with freeze_time(datetime.utcnow() + timedelta(minutes=1)):
        old_date = signing_properties["date"]
        with pytest.warns(UserWarning, match="Payload signing is enabled"):
            new_request = await sigv4_signer.sign(
                http_request=http_request,
                identity=aws_credential_identity,
                signing_properties=signing_properties,
            )
        new_date = signing_properties["date"]
        assert old_date == new_date
        assert new_request.fields.get_field("X-Amz-Date").as_string() == old_date
