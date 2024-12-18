import os
import pathlib
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler
from io import BytesIO

import pytest
from aws_sdk_signers import (
    URI,
    AsyncBytesReader,
    AWSCredentialIdentity,
    AWSRequest,
    Field,
    Fields,
)
from aws_sdk_signers.exceptions import AWSSDKWarning
from aws_sdk_signers.signers import (
    SIGV4_TIMESTAMP_FORMAT,
    AsyncSigV4Signer,
    SigV4Signer,
    SigV4SigningProperties,
)
from freezegun import freeze_time

SECRET_KEY: str = "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY"
ACCESS_KEY: str = "AKIDEXAMPLE"
SERVICE: str = "service"
REGION: str = "us-east-1"

DATE: datetime = datetime(
    year=2015, month=8, day=30, hour=12, minute=36, second=0, tzinfo=UTC
)
DATE_STR: str = DATE.strftime(SIGV4_TIMESTAMP_FORMAT)

TESTSUITE_DIR: pathlib.Path = (
    pathlib.Path(__file__).absolute().parent / "aws4_testsuite"
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


class SignatureTestCase:
    def __init__(self, test_case: str) -> None:
        self.name: str = os.path.basename(test_case)
        base_path: pathlib.Path = TESTSUITE_DIR / test_case

        self.raw_request: bytes = (base_path / f"{self.name}.req").read_bytes()
        self.canonical_request: str = (base_path / f"{self.name}.creq").read_text()
        self.string_to_sign: str = (base_path / f"{self.name}.sts").read_text()
        self.authorization_header: str = (base_path / f"{self.name}.authz").read_text()
        self.signed_request: str = (base_path / f"{self.name}.sreq").read_text()
        self.credentials: AWSCredentialIdentity = AWSCredentialIdentity(
            access_key_id=ACCESS_KEY,
            secret_access_key=SECRET_KEY,
            session_token=self.get_token(),
        )

    def get_token(self) -> str | None:
        token_pattern = r"^x-amz-security-token:(.*)$"
        token_match = re.search(token_pattern, self.canonical_request, re.MULTILINE)
        return token_match.group(1) if token_match else None


def generate_test_cases() -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(TESTSUITE_DIR):
        # Skip over tests without a request file
        if not any(f.endswith(".req") for f in filenames):
            continue

        test_case_name = os.path.relpath(dirpath, TESTSUITE_DIR).replace(os.sep, "/")

        yield test_case_name


@pytest.mark.parametrize("test_case_name", generate_test_cases())
@freeze_time("2015-08-30 12:36:00")
def test_signature_version_4_sync(test_case_name: str) -> None:
    signer = SigV4Signer()
    _test_signature_version_4_sync(test_case_name, signer)


def _test_signature_version_4_sync(test_case_name: str, signer: SigV4Signer) -> None:
    test_case = SignatureTestCase(test_case_name)
    request = create_request_from_raw_request(test_case)

    signing_props = SigV4SigningProperties(
        region=REGION,
        service=SERVICE,
        date=DATE_STR,
    )
    with pytest.warns(AWSSDKWarning):
        actual_canonical_request = signer.canonical_request(
            signing_properties=signing_props, request=request
        )
    assert test_case.canonical_request == actual_canonical_request
    actual_string_to_sign = signer.string_to_sign(
        canonical_request=actual_canonical_request, signing_properties=signing_props
    )
    assert test_case.string_to_sign == actual_string_to_sign
    with pytest.warns(AWSSDKWarning):
        signed_request = signer.sign(
            signing_properties=signing_props,
            request=request,
            identity=test_case.credentials,
        )
    assert (
        signed_request.fields["Authorization"].as_string()
        == test_case.authorization_header
    )


@pytest.mark.parametrize("test_case_name", generate_test_cases())
@freeze_time("2015-08-30 12:36:00")
async def test_signature_version_4_async(test_case_name: str) -> None:
    signer = AsyncSigV4Signer()
    await _test_signature_version_4_async(test_case_name, signer)


async def _test_signature_version_4_async(
    test_case_name: str, signer: AsyncSigV4Signer
) -> None:
    test_case = SignatureTestCase(test_case_name)
    request = create_request_from_raw_request(test_case, async_body=True)

    signing_props = SigV4SigningProperties(
        region=REGION,
        service=SERVICE,
        date=DATE_STR,
    )
    with pytest.warns(AWSSDKWarning):
        actual_canonical_request = await signer.canonical_request(
            signing_properties=signing_props, request=request
        )
    assert test_case.canonical_request == actual_canonical_request
    actual_string_to_sign = await signer.string_to_sign(
        canonical_request=actual_canonical_request, signing_properties=signing_props
    )
    assert test_case.string_to_sign == actual_string_to_sign
    with pytest.warns(AWSSDKWarning):
        signed_request = await signer.sign(
            signing_properties=signing_props,
            request=request,
            identity=test_case.credentials,
        )
    assert (
        signed_request.fields["Authorization"].as_string()
        == test_case.authorization_header
    )


def create_request_from_raw_request(
    test_case: SignatureTestCase, async_body: bool = False
) -> AWSRequest:
    raw = RawRequest(raw_request=test_case.raw_request)
    if raw.error_code is not None:
        raise Exception(raw.error_message)

    request_method = raw.command
    fields = Fields()
    for k, v in raw.headers.items():
        if k in fields:
            fields[k].add(value=v)
        else:
            field = Field(name=k, values=[v])
            fields.set_field(field=field)
    fields.set_field(Field(name="X-Amz-Date", values=[DATE_STR]))
    if test_case.credentials.session_token is not None:
        fields.set_field(
            Field(
                name="X-Amz-Security-Token",
                values=[test_case.credentials.session_token],
            )
        )
    body: BytesIO | AsyncBytesReader = raw.rfile
    if async_body:
        body = AsyncBytesReader(raw.rfile)
    # BaseHTTPRequestHandler encodes the first line of the request
    # as 'iso-8859-1', so we need to decode this into utf-8.
    if isinstance(path := raw.path, str):
        path = path.encode(encoding="iso-8859-1").decode(encoding="utf-8")
    if "?" in path:
        path, query = path.split(sep="?", maxsplit=1)
    else:
        query = ""
    host = raw.headers.get("host", "")
    url = URI(host=host, path=path, query=query)
    return AWSRequest(
        destination=url,
        method=request_method,
        fields=fields,
        body=body,
    )
