# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import copy
import hmac
import re
import typing
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import pytest
from aws_sdk_signers import (
    AWSCredentialIdentity,
    AWSRequest,
    ChunkSigner,
    EventSigner,
    Field,
    Fields,
    SigV4Signer,
    SigV4SigningProperties,
    URI,
)
from aws_sdk_signers._sigv4 import signing_key
from aws_sdk_signers.aio import AsyncBytesReader, AsyncSigV4Signer
from aws_sdk_signers.signers import EVENT_STREAM_CONTENT_TYPE, EVENT_STREAM_HASH
from smithy_aws_event_stream.events import Event, EventHeaderEncoder, EventMessage

SIGV4_RE = re.compile(
    r"AWS4-HMAC-SHA256 "
    r"Credential=(?P<access_key>\w+)/\d+/"
    r"(?P<signing_region>[a-z0-9-]+)/"
)
SIGNED_HEADERS_RE = re.compile(r"SignedHeaders=(?P<signed_headers>[^,]+)")

# Headers that must not be signed, paired with a representative value. Authorization
# is also excluded but is omitted here since signing replaces it.
EXCLUDED_HEADERS = [
    ("accept", "application/json"),
    ("accept-encoding", "gzip"),
    ("connection", "keep-alive"),
    ("expect", "100-continue"),
    ("keep-alive", "timeout=5"),
    ("proxy-authenticate", 'Basic realm="proxy.example.com"'),
    ("proxy-authorization", "Basic YWxhZGRpbjpvcGVuc2VzYW1l"),
    ("te", "trailers"),
    ("trailer", "x-amz-checksum-sha256"),
    ("transfer-encoding", "chunked"),
    ("upgrade", "websocket"),
    ("user-agent", "aws-sdk-python/0.1.0"),
    ("x-amzn-trace-id", "Root=foo;Parent=bar;Sampleid=1"),
]


@pytest.fixture(scope="module")
def aws_identity() -> AWSCredentialIdentity:
    return AWSCredentialIdentity(
        access_key_id="AKID123456",
        secret_access_key="EXAMPLE1234SECRET",
        session_token="X123456SESSION",
    )


@pytest.fixture(scope="module")
def signing_properties() -> SigV4SigningProperties:
    return SigV4SigningProperties(
        region="us-west-2",
        service="ec2",
        payload_signing_enabled=False,
    )


@pytest.fixture(scope="module")
def aws_request() -> AWSRequest:
    return AWSRequest(
        destination=URI(
            scheme="https",
            host="127.0.0.1",
            port=8000,
        ),
        method="GET",
        body=BytesIO(b"123456"),
        fields=Fields({}),
    )


CANONICAL_PATH_CASES: list[tuple[dict[str, bool], str, str]] = [
    # Default: normalize the path, then encode it a second time.
    ({}, "/a/./b/../c//d%20e", "/a/c/d%2520e"),
    # No double-encoding keeps consecutive slashes but still removes dot segments.
    ({"uri_encode_path": False}, "/a/./b/../c//d%20e", "/a/c//d%20e"),
    # No normalization keeps every segment but still encodes a second time.
    ({"normalize_path": False}, "/a/./b/../c//d%20e", "/a/./b/../c//d%2520e"),
    # S3 signs the path exactly as it is sent.
    (
        {"uri_encode_path": False, "normalize_path": False},
        "/a/./b/../c//d%20e",
        "/a/./b/../c//d%20e",
    ),
]


def _request_with_field(name: str, value: str) -> AWSRequest:
    return AWSRequest(
        destination=URI(
            scheme="https",
            host="127.0.0.1",
            port=8000,
        ),
        method="GET",
        body=BytesIO(b"123456"),
        fields=Fields([Field(name=name, values=[value])]),
    )


@dataclass(kw_only=True)
class DataclassRequest:
    """A request without a custom ``__deepcopy__``, like smithy-http's HTTPRequest."""

    destination: URI
    method: str
    body: typing.Any
    fields: Fields


def _dataclass_request(body: typing.Any) -> AWSRequest:
    request = DataclassRequest(
        destination=URI(scheme="https", host="127.0.0.1", port=8000),
        method="PUT",
        body=body,
        fields=Fields({}),
    )
    return typing.cast(AWSRequest, request)


async def _async_chunks(chunks: Iterable[bytes]) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


class AsyncSeekableBody:
    """An async body with async seek and sync tell, like smithy-core's readers."""

    def __init__(self, data: bytes) -> None:
        self._data = BytesIO(data)

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._chunks()

    async def _chunks(self) -> AsyncIterator[bytes]:
        while chunk := self._data.read(2):
            yield chunk

    async def seek(self, offset: int, whence: int = 0) -> int:
        return self._data.seek(offset, whence)

    def tell(self) -> int:
        return self._data.tell()


# Signs the payload and sends its hash, so tests can check what was hashed.
PAYLOAD_SIGNING_PROPERTIES = SigV4SigningProperties(
    region="us-west-2",
    service="s3",
    content_checksum_enabled=True,
)


def _payload_hash(request: AWSRequest) -> str:
    return request.fields["X-Amz-Content-SHA256"].as_string()


def _signed_headers(request: AWSRequest) -> list[str]:
    match = SIGNED_HEADERS_RE.search(request.fields["authorization"].as_string())
    assert match is not None
    return match.group("signed_headers").split(";")


MULTI_VALUE_PROPERTIES = SigV4SigningProperties(
    region="us-west-2",
    service="s3",
    date="20250101T000000Z",
    payload_signing_enabled=False,
)
MULTI_VALUE_CANONICAL_FIELD = "\ncontent-encoding:gzip,aws-chunked\n"
MULTI_VALUE_SIGNATURE = (
    "Signature=a09dab2d634373cdd8df8baae2f32979b64c416b0b08724e4094c78d67b77466"
)


def _multi_value_request(values: list[str]) -> AWSRequest:
    return _request_with_fields([Field(name="Content-Encoding", values=values)])


@dataclass
class ForeignField:
    """A ``Field`` from another package, like the smithy-http one smithy-aws-core signs.

    Its ``as_string`` joins with a comma and a space, as smithy-http's once did, so the
    tests fail if the signer serializes values through it.
    """

    name: str
    values: list[str]
    kind: typing.Literal["header", "trailer"] = "header"

    def as_string(self, delimiter: str = ", ") -> str:
        return ", ".join(self.values)


def _foreign_field_request(values: list[str]) -> AWSRequest:
    field = ForeignField(name="Content-Encoding", values=values)
    return _request_with_fields([typing.cast(Field, field)])


def _request_with_fields(fields: list[Field]) -> AWSRequest:
    return AWSRequest(
        destination=URI(scheme="https", host="example.amazonaws.com"),
        method="PUT",
        body=BytesIO(b""),
        fields=Fields(fields),
    )


# Transports send each value of a field as its own header line, and the service
# joins them with a bare comma before verifying the signature. The "joined" case is
# the request as the service sees it, so every case must produce its signature.
MULTI_VALUE_REQUESTS = pytest.mark.parametrize(
    "make_request",
    [
        lambda: _multi_value_request(["gzip", "aws-chunked"]),
        lambda: _foreign_field_request(["gzip", "aws-chunked"]),
        lambda: _multi_value_request(["gzip,aws-chunked"]),
        lambda: _multi_value_request([" gzip ", "  aws-chunked"]),
    ],
    ids=["aws-sdk-signers", "foreign-field", "joined", "padded"],
)

# Each case is (values sent as separate header lines, the value the service rebuilds).
# ``Field.as_string`` would quote the values containing a comma or a double quote.
CANONICAL_FIELD_VALUE_CASES = pytest.mark.parametrize(
    "values, expected",
    [
        (["gzip,br", "aws-chunked"], "gzip,br,aws-chunked"),
        (['"gzip"', "aws-chunked"], '"gzip",aws-chunked'),
        (["a  b ", " c"], "a b,c"),
    ],
    ids=["comma", "quote", "whitespace"],
)

# Fields that never reach the wire as a header line, so they must not be signed.
UNSENT_FIELDS = pytest.mark.parametrize(
    "field",
    [
        Field(name="X-Amz-Meta-Empty", values=[]),
        Field(name="X-Amz-Checksum-Crc32", values=["AAAAAA=="], kind="trailer"),
    ],
    ids=["no-values", "trailer"],
)
CANONICAL_FIELD_VALUE_REQUESTS = pytest.mark.parametrize(
    "make_request",
    [_multi_value_request, _foreign_field_request],
    ids=["aws-sdk-signers", "foreign-field"],
)


class TestSigV4Signer:
    SIGV4_SYNC_SIGNER = SigV4Signer()

    def test_sign(
        self,
        aws_identity: AWSCredentialIdentity,
        aws_request: AWSRequest,
        signing_properties: SigV4SigningProperties,
    ) -> None:
        signed_request = self.SIGV4_SYNC_SIGNER.sign(
            properties=signing_properties,
            request=aws_request,
            identity=aws_identity,
        )
        assert isinstance(signed_request, AWSRequest)
        assert signed_request is not aws_request
        assert "authorization" in signed_request.fields
        authorization_field = signed_request.fields["authorization"]
        assert SIGV4_RE.match(authorization_field.as_string())

    def test_sign_doesnt_modify_original_request(
        self,
        aws_identity: AWSCredentialIdentity,
        aws_request: AWSRequest,
        signing_properties: SigV4SigningProperties,
    ) -> None:
        original_request = copy.deepcopy(aws_request)
        signed_request = self.SIGV4_SYNC_SIGNER.sign(
            properties=signing_properties,
            request=aws_request,
            identity=aws_identity,
        )
        assert isinstance(signed_request, AWSRequest)
        assert signed_request is not aws_request
        assert aws_request.fields == original_request.fields
        assert signed_request.fields != aws_request.fields

    def test_sign_payload_restores_shared_seekable_body(
        self, aws_identity: AWSCredentialIdentity, tmp_path: Path
    ) -> None:
        path = tmp_path / "body"
        path.write_bytes(b"123456")
        with path.open("rb") as body:
            body.seek(2)
            request = _dataclass_request(body)
            signed_request = self.SIGV4_SYNC_SIGNER.sign(
                properties=PAYLOAD_SIGNING_PROPERTIES,
                request=request,
                identity=aws_identity,
            )
            assert signed_request.body is body
            assert body.tell() == 2
            assert _payload_hash(signed_request) == sha256(b"3456").hexdigest()

    @typing.no_type_check
    def test_sign_with_invalid_identity(
        self, aws_request: AWSRequest, signing_properties: SigV4SigningProperties
    ) -> None:
        """Ignore typing as we're testing an invalid input state."""
        identity = object()
        assert not isinstance(identity, AWSCredentialIdentity)
        with pytest.raises(ValueError):
            self.SIGV4_SYNC_SIGNER.sign(
                properties=signing_properties,
                request=aws_request,
                identity=identity,
            )

    def test_sign_with_expired_identity(
        self, aws_request: AWSRequest, signing_properties: SigV4SigningProperties
    ) -> None:
        identity = AWSCredentialIdentity(
            access_key_id="AKID123456",
            secret_access_key="EXAMPLE1234SECRET",
            session_token="X123456SESSION",
            expiration=datetime(1970, 1, 1, tzinfo=UTC),
        )
        with pytest.raises(ValueError):
            self.SIGV4_SYNC_SIGNER.sign(
                properties=signing_properties,
                request=aws_request,
                identity=identity,
            )

    @pytest.mark.parametrize("name, value", EXCLUDED_HEADERS)
    def test_sign_excludes_header_from_signed_headers(
        self,
        aws_identity: AWSCredentialIdentity,
        signing_properties: SigV4SigningProperties,
        name: str,
        value: str,
    ) -> None:
        signed_request = self.SIGV4_SYNC_SIGNER.sign(
            properties=signing_properties,
            request=_request_with_field(name, value),
            identity=aws_identity,
        )
        signed_headers = _signed_headers(signed_request)
        assert "host" in signed_headers
        assert name not in signed_headers
        assert signed_request.fields[name].as_string() == value

    @MULTI_VALUE_REQUESTS
    def test_sign_joins_multi_valued_field_with_bare_comma(
        self,
        aws_identity: AWSCredentialIdentity,
        make_request: typing.Callable[[], AWSRequest],
    ) -> None:
        request = make_request()
        canonical_request = self.SIGV4_SYNC_SIGNER.canonical_request(
            signing_properties=MULTI_VALUE_PROPERTIES, request=request
        )
        assert MULTI_VALUE_CANONICAL_FIELD in canonical_request
        signed = self.SIGV4_SYNC_SIGNER.sign(
            properties=MULTI_VALUE_PROPERTIES,
            request=request,
            identity=aws_identity,
        )
        assert (
            signed.fields["authorization"].as_string().endswith(MULTI_VALUE_SIGNATURE)
        )

    @UNSENT_FIELDS
    def test_does_not_sign_unsent_field(self, field: Field) -> None:
        canonical_request = self.SIGV4_SYNC_SIGNER.canonical_request(
            signing_properties=MULTI_VALUE_PROPERTIES,
            request=_request_with_fields([field]),
        )
        assert canonical_request == self.SIGV4_SYNC_SIGNER.canonical_request(
            signing_properties=MULTI_VALUE_PROPERTIES,
            request=_request_with_fields([]),
        )

    @CANONICAL_FIELD_VALUE_CASES
    @CANONICAL_FIELD_VALUE_REQUESTS
    def test_canonical_field_matches_value_service_rebuilds(
        self,
        make_request: typing.Callable[[list[str]], AWSRequest],
        values: list[str],
        expected: str,
    ) -> None:
        canonical_request = self.SIGV4_SYNC_SIGNER.canonical_request(
            signing_properties=MULTI_VALUE_PROPERTIES, request=make_request(values)
        )
        assert f"\ncontent-encoding:{expected}\n" in canonical_request
        assert canonical_request == self.SIGV4_SYNC_SIGNER.canonical_request(
            signing_properties=MULTI_VALUE_PROPERTIES,
            request=_multi_value_request([expected]),
        )

    def test_sign_event_stream(self, aws_identity: AWSCredentialIdentity) -> None:
        signed = self.SIGV4_SYNC_SIGNER.sign(
            properties=PAYLOAD_SIGNING_PROPERTIES,
            request=_event_stream_request(UnreadableStream()),
            identity=aws_identity,
        )
        assert _payload_hash(signed) == EVENT_STREAM_HASH

    def test_sign_uses_preset_payload_hash(
        self, aws_identity: AWSCredentialIdentity
    ) -> None:
        signed = self.SIGV4_SYNC_SIGNER.sign(
            properties=PAYLOAD_SIGNING_PROPERTIES,
            request=_preset_hash_request(UnreadableStream()),
            identity=aws_identity,
        )
        assert _payload_hash(signed) == PRESET_HASH
        assert (
            signed.fields["authorization"]
            .as_string()
            .endswith(_expected_signature(signed))
        )

    def test_format_canonical_query_keeps_blank_values(self) -> None:
        canonical_query = self.SIGV4_SYNC_SIGNER._format_canonical_query(  # pyright: ignore[reportPrivateUsage]
            query="foo=bar&baz="
        )
        assert canonical_query == "baz=&foo=bar"

    def test_format_canonical_query_with_literal_query_param(self) -> None:
        canonical_query = self.SIGV4_SYNC_SIGNER._format_canonical_query(  # pyright: ignore[reportPrivateUsage]
            query="sync"
        )
        assert canonical_query == "sync="

    @pytest.mark.parametrize("options, path, expected", CANONICAL_PATH_CASES)
    def test_format_canonical_path(
        self, options: dict[str, bool], path: str, expected: str
    ) -> None:
        properties = SigV4SigningProperties(region="us-west-2", service="s3", **options)  # type: ignore[typeddict-item]
        canonical_path = self.SIGV4_SYNC_SIGNER._format_canonical_path(  # pyright: ignore[reportPrivateUsage]
            path=path, signing_properties=properties
        )
        assert canonical_path == expected


class UnreadableStream:
    def __iter__(self) -> typing.Self:
        return self

    def __next__(self) -> bytes:
        raise Exception("Read should not have been called!")


PRESET_HASH = sha256(b"preset").hexdigest()


def _event_stream_request(body: typing.Any) -> AWSRequest:
    request = _dataclass_request(body)
    request.fields.set_field(
        Field(name="Content-Type", values=[EVENT_STREAM_CONTENT_TYPE])
    )
    return request


def _preset_hash_request(body: typing.Any) -> AWSRequest:
    request = _dataclass_request(body)
    request.fields.set_field(Field(name="X-Amz-Content-SHA256", values=[PRESET_HASH]))
    return request


def _expected_signature(request: AWSRequest) -> str:
    signer = SigV4Signer()
    properties = SigV4SigningProperties(**PAYLOAD_SIGNING_PROPERTIES)
    properties["date"] = request.fields["X-Amz-Date"].as_string()
    canonical_request = signer.canonical_request(
        signing_properties=properties, request=request
    )
    string_to_sign = signer.string_to_sign(
        canonical_request=canonical_request, signing_properties=properties
    )
    key = signing_key("EXAMPLE1234SECRET", properties)
    return hmac.new(key, string_to_sign.encode(), sha256).hexdigest()


class UnreadableAsyncStream:
    def __aiter__(self) -> typing.Self:
        return self

    async def __anext__(self) -> bytes:
        raise Exception("Read should not have been called!")


class TestEventSigner:
    def test_sign_wraps_event_message_payload(
        self,
        aws_identity: AWSCredentialIdentity,
    ) -> None:
        signer = EventSigner(
            initial_signature=b"initial-signature",
            event_encoder_cls=EventHeaderEncoder,
        )
        message = EventMessage(
            headers={":message-type": "event", ":event-type": "AudioEvent"},
            payload=b"audio",
        )

        signed = signer.sign(
            event=message,
            identity=aws_identity,
            properties=SigV4SigningProperties(region="us-west-2", service="transcribe"),
        )

        assert (
            signed.payload
            == EventMessage(
                headers={":message-type": "event", ":event-type": "AudioEvent"},
                payload=b"audio",
            ).encode()
        )
        assert ":date" in signed.headers
        assert ":chunk-signature" in signed.headers

    def test_sign_empty_uses_zero_byte_outer_payload(
        self,
        aws_identity: AWSCredentialIdentity,
    ) -> None:
        signer = EventSigner(
            initial_signature=b"initial-signature",
            event_encoder_cls=EventHeaderEncoder,
        )

        signed = signer.sign_empty(
            event=EventMessage(),
            identity=aws_identity,
            properties=SigV4SigningProperties(region="us-west-2", service="transcribe"),
        )

        decoded = Event.decode(BytesIO(signed.encode()))
        assert decoded is not None
        assert decoded.message.payload == b""
        assert ":date" in decoded.message.headers
        assert ":chunk-signature" in decoded.message.headers

    def test_sign_empty_rejects_non_empty_event(
        self,
        aws_identity: AWSCredentialIdentity,
    ) -> None:
        signer = EventSigner(
            initial_signature=b"initial-signature",
            event_encoder_cls=EventHeaderEncoder,
        )

        with pytest.raises(ValueError):
            signer.sign_empty(
                event=EventMessage(headers={"foo": "bar"}),
                identity=aws_identity,
                properties=SigV4SigningProperties(
                    region="us-west-2", service="transcribe"
                ),
            )

        with pytest.raises(ValueError):
            signer.sign_empty(
                event=EventMessage(payload=b"audio"),
                identity=aws_identity,
                properties=SigV4SigningProperties(
                    region="us-west-2", service="transcribe"
                ),
            )

    def test_sign_rejects_events_after_empty_event(
        self,
        aws_identity: AWSCredentialIdentity,
    ) -> None:
        signer = EventSigner(
            initial_signature=b"initial-signature",
            event_encoder_cls=EventHeaderEncoder,
        )
        properties = SigV4SigningProperties(region="us-west-2", service="transcribe")

        signer.sign_empty(
            event=EventMessage(),
            identity=aws_identity,
            properties=properties,
        )

        with pytest.raises(RuntimeError, match="final empty event"):
            signer.sign(
                event=EventMessage(
                    headers={":message-type": "event", ":event-type": "AudioEvent"},
                    payload=b"audio",
                ),
                identity=aws_identity,
                properties=properties,
            )


class TestAsyncSigV4Signer:
    SIGV4_ASYNC_SIGNER = AsyncSigV4Signer()

    async def test_sign(
        self,
        aws_identity: AWSCredentialIdentity,
        aws_request: AWSRequest,
        signing_properties: SigV4SigningProperties,
    ) -> None:
        signed_request = await self.SIGV4_ASYNC_SIGNER.sign(
            properties=signing_properties,
            request=aws_request,
            identity=aws_identity,
        )
        assert isinstance(signed_request, AWSRequest)
        assert signed_request is not aws_request
        assert "authorization" in signed_request.fields
        authorization_field = signed_request.fields["authorization"]
        assert SIGV4_RE.match(authorization_field.as_string())

    async def test_sign_doesnt_modify_original_request(
        self,
        aws_identity: AWSCredentialIdentity,
        aws_request: AWSRequest,
        signing_properties: SigV4SigningProperties,
    ) -> None:
        original_request = copy.deepcopy(aws_request)
        signed_request = await self.SIGV4_ASYNC_SIGNER.sign(
            properties=signing_properties,
            request=aws_request,
            identity=aws_identity,
        )
        assert isinstance(signed_request, AWSRequest)
        assert signed_request is not aws_request
        assert aws_request.fields == original_request.fields
        assert signed_request.fields != aws_request.fields

    async def test_sign_payload_restores_shared_seekable_body(
        self, aws_identity: AWSCredentialIdentity
    ) -> None:
        body = AsyncSeekableBody(b"123456")
        await body.seek(2)
        request = _dataclass_request(body)
        signed_request = await self.SIGV4_ASYNC_SIGNER.sign(
            properties=PAYLOAD_SIGNING_PROPERTIES,
            request=request,
            identity=aws_identity,
        )
        assert signed_request.body is body
        assert body.tell() == 2
        assert _payload_hash(signed_request) == sha256(b"3456").hexdigest()

    async def test_sign_payload_buffers_non_seekable_body(
        self, aws_identity: AWSCredentialIdentity
    ) -> None:
        request = _dataclass_request(_async_chunks([b"123", b"456"]))
        signed_request = await self.SIGV4_ASYNC_SIGNER.sign(
            properties=PAYLOAD_SIGNING_PROPERTIES,
            request=request,
            identity=aws_identity,
        )
        assert _payload_hash(signed_request) == sha256(b"123456").hexdigest()
        assert isinstance(signed_request.body, AsyncBytesReader)
        assert await signed_request.body.read() == b"123456"

    async def test_sign_payload_hashes_sync_body(
        self, aws_identity: AWSCredentialIdentity
    ) -> None:
        body = BytesIO(b"123456")
        signed_request = await self.SIGV4_ASYNC_SIGNER.sign(
            properties=PAYLOAD_SIGNING_PROPERTIES,
            request=_dataclass_request(body),
            identity=aws_identity,
        )
        assert _payload_hash(signed_request) == sha256(b"123456").hexdigest()
        assert signed_request.body is body
        assert body.tell() == 0

    @typing.no_type_check
    async def test_sign_with_invalid_identity(
        self, aws_request: AWSRequest, signing_properties: SigV4SigningProperties
    ) -> None:
        """Ignore typing as we're testing an invalid input state."""
        identity = object()
        assert not isinstance(identity, AWSCredentialIdentity)
        with pytest.raises(ValueError):
            await self.SIGV4_ASYNC_SIGNER.sign(
                properties=signing_properties,
                request=aws_request,
                identity=identity,
            )

    async def test_sign_with_expired_identity(
        self, aws_request: AWSRequest, signing_properties: SigV4SigningProperties
    ) -> None:
        identity = AWSCredentialIdentity(
            access_key_id="AKID123456",
            secret_access_key="EXAMPLE1234SECRET",
            session_token="X123456SESSION",
            expiration=datetime(1970, 1, 1, tzinfo=UTC),
        )
        with pytest.raises(ValueError):
            await self.SIGV4_ASYNC_SIGNER.sign(
                properties=signing_properties,
                request=aws_request,
                identity=identity,
            )

    @pytest.mark.parametrize("name, value", EXCLUDED_HEADERS)
    async def test_sign_excludes_header_from_signed_headers(
        self,
        aws_identity: AWSCredentialIdentity,
        signing_properties: SigV4SigningProperties,
        name: str,
        value: str,
    ) -> None:
        signed_request = await self.SIGV4_ASYNC_SIGNER.sign(
            properties=signing_properties,
            request=_request_with_field(name, value),
            identity=aws_identity,
        )
        signed_headers = _signed_headers(signed_request)
        assert "host" in signed_headers
        assert name not in signed_headers
        assert signed_request.fields[name].as_string() == value

    @MULTI_VALUE_REQUESTS
    async def test_sign_joins_multi_valued_field_with_bare_comma(
        self,
        aws_identity: AWSCredentialIdentity,
        make_request: typing.Callable[[], AWSRequest],
    ) -> None:
        request = make_request()
        canonical_request = await self.SIGV4_ASYNC_SIGNER.canonical_request(
            signing_properties=MULTI_VALUE_PROPERTIES, request=request
        )
        assert MULTI_VALUE_CANONICAL_FIELD in canonical_request
        signed = await self.SIGV4_ASYNC_SIGNER.sign(
            properties=MULTI_VALUE_PROPERTIES,
            request=request,
            identity=aws_identity,
        )
        assert (
            signed.fields["authorization"].as_string().endswith(MULTI_VALUE_SIGNATURE)
        )

    @UNSENT_FIELDS
    async def test_does_not_sign_unsent_field(self, field: Field) -> None:
        canonical_request = await self.SIGV4_ASYNC_SIGNER.canonical_request(
            signing_properties=MULTI_VALUE_PROPERTIES,
            request=_request_with_fields([field]),
        )
        assert canonical_request == await self.SIGV4_ASYNC_SIGNER.canonical_request(
            signing_properties=MULTI_VALUE_PROPERTIES,
            request=_request_with_fields([]),
        )

    @CANONICAL_FIELD_VALUE_CASES
    @CANONICAL_FIELD_VALUE_REQUESTS
    async def test_canonical_field_matches_value_service_rebuilds(
        self,
        make_request: typing.Callable[[list[str]], AWSRequest],
        values: list[str],
        expected: str,
    ) -> None:
        canonical_request = await self.SIGV4_ASYNC_SIGNER.canonical_request(
            signing_properties=MULTI_VALUE_PROPERTIES, request=make_request(values)
        )
        assert f"\ncontent-encoding:{expected}\n" in canonical_request
        assert canonical_request == await self.SIGV4_ASYNC_SIGNER.canonical_request(
            signing_properties=MULTI_VALUE_PROPERTIES,
            request=_multi_value_request([expected]),
        )

    async def test_sign_event_stream(
        self,
        aws_identity: AWSCredentialIdentity,
    ) -> None:
        headers = Fields()
        headers.set_field(
            Field(name="Content-Type", values=["application/vnd.amazon.eventstream"])
        )
        request = AWSRequest(
            destination=URI(
                scheme="https",
                host="127.0.0.1",
                port=8000,
            ),
            method="GET",
            body=UnreadableAsyncStream(),
            fields=headers,
        )
        signed = await self.SIGV4_ASYNC_SIGNER.sign(
            properties=SigV4SigningProperties(
                region="us-west-2",
                service="ec2",
                date="0",
            ),
            request=request,
            identity=aws_identity,
        )
        assert "X-Amz-Content-SHA256" in signed.fields
        payload_hash = signed.fields["X-Amz-Content-SHA256"].as_string()
        assert payload_hash == "STREAMING-AWS4-HMAC-SHA256-EVENTS"

    async def test_sign_uses_preset_payload_hash(
        self, aws_identity: AWSCredentialIdentity
    ) -> None:
        signed = await self.SIGV4_ASYNC_SIGNER.sign(
            properties=PAYLOAD_SIGNING_PROPERTIES,
            request=_preset_hash_request(UnreadableAsyncStream()),
            identity=aws_identity,
        )
        assert _payload_hash(signed) == PRESET_HASH
        assert (
            signed.fields["authorization"]
            .as_string()
            .endswith(_expected_signature(signed))
        )

    async def test_sign_matches_sync_signer(
        self, aws_identity: AWSCredentialIdentity
    ) -> None:
        properties = SigV4SigningProperties(region="us-west-2", service="s3")
        signed = await self.SIGV4_ASYNC_SIGNER.sign(
            properties=properties,
            request=_dataclass_request(AsyncBytesReader(b"123456")),
            identity=aws_identity,
        )
        sync_properties = SigV4SigningProperties(**properties)
        sync_properties["date"] = signed.fields["X-Amz-Date"].as_string()
        expected = SigV4Signer().sign(
            properties=sync_properties,
            request=_dataclass_request(BytesIO(b"123456")),
            identity=aws_identity,
        )
        assert signed.fields == expected.fields

    def test_format_canonical_query_keeps_blank_values(self) -> None:
        canonical_query = self.SIGV4_ASYNC_SIGNER._format_canonical_query(  # pyright: ignore[reportPrivateUsage]
            query="foo=bar&baz="
        )
        assert canonical_query == "baz=&foo=bar"

    def test_format_canonical_query_with_literal_query_param(self) -> None:
        canonical_query = self.SIGV4_ASYNC_SIGNER._format_canonical_query(  # pyright: ignore[reportPrivateUsage]
            query="sync"
        )
        assert canonical_query == "sync="

    @pytest.mark.parametrize("options, path, expected", CANONICAL_PATH_CASES)
    def test_format_canonical_path(
        self, options: dict[str, bool], path: str, expected: str
    ) -> None:
        properties = SigV4SigningProperties(region="us-west-2", service="s3", **options)  # type: ignore[typeddict-item]
        canonical_path = self.SIGV4_ASYNC_SIGNER._format_canonical_path(  # pyright: ignore[reportPrivateUsage]
            path=path, signing_properties=properties
        )
        assert canonical_path == expected


class TestChunkSigner:
    # The S3 example for signing a payload in chunks, whose 66560-byte payload of
    # "a" is sent in a 65536-byte chunk, a 1024-byte chunk and an empty chunk. The
    # signatures match those of the CRT's chunked signing tests.
    IDENTITY = AWSCredentialIdentity(
        access_key_id="AKIAIOSFODNN7EXAMPLE",
        secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    )
    PROPERTIES = SigV4SigningProperties(
        region="us-east-1", service="s3", date="20130524T000000Z"
    )
    SEED_SIGNATURE = "4f232c4386841ef735655705268965c44a0e4690baa4adea153f7db9fa80a0a9"
    CHUNK_SIGNATURES = (
        "ad80c730a21e5b8d04586a2213dd63b9a0e99e0e2307b0ade35a65485a288648",
        "0055627c9e194cb4542bae2aa5492e3c1575bbb81b612b7d234b86a503ef5497",
        "b6c6ea8a5354eaf15b3cb7646744f4275b71ea724fed81ceb9323e279d449df9",
    )
    TRAILER_SIGNATURE = (
        "df5735bd9f3295cd9386572292562fefc93ba94e80a0a1ddcbd652c4e0a75e6c"
    )

    def signed_request(self) -> AWSRequest:
        request = AWSRequest(
            destination=URI(
                host="s3.amazonaws.com", path="/examplebucket/chunkObject.txt"
            ),
            method="PUT",
            body=None,
            fields=Fields(
                [
                    Field(name="host", values=["s3.amazonaws.com"]),
                    Field(name="x-amz-storage-class", values=["REDUCED_REDUNDANCY"]),
                    Field(name="content-encoding", values=["aws-chunked"]),
                    Field(name="x-amz-decoded-content-length", values=["66560"]),
                    Field(name="content-length", values=["66824"]),
                    Field(
                        name="x-amz-content-sha256",
                        values=["STREAMING-AWS4-HMAC-SHA256-PAYLOAD"],
                    ),
                ]
            ),
        )
        return SigV4Signer().sign(
            request=request, identity=self.IDENTITY, properties=self.PROPERTIES
        )

    def sign_payload(self, signer: ChunkSigner) -> tuple[str, ...]:
        return tuple(
            signer.sign_chunk(data)
            for data in (b"a" * 65536, bytearray(b"a" * 1024), memoryview(b""))
        )

    def test_chains_chunk_and_trailer_signatures(self) -> None:
        signer = ChunkSigner(
            seed_signature=self.SEED_SIGNATURE,
            identity=self.IDENTITY,
            properties=self.PROPERTIES,
        )
        assert self.sign_payload(signer) == self.CHUNK_SIGNATURES
        trailer = "first:1st\nsecond:2nd\nthird:3rd\n"
        assert signer.sign_trailer(trailer) == self.TRAILER_SIGNATURE

    def test_continues_signature_of_signed_request(self) -> None:
        request = self.signed_request()
        assert (
            request.fields["Authorization"]
            .as_string()
            .endswith(f"Signature={self.SEED_SIGNATURE}")
        )
        signer = ChunkSigner.from_signed_request(request, self.IDENTITY)
        assert self.sign_payload(signer) == self.CHUNK_SIGNATURES

    def test_requires_date(self) -> None:
        with pytest.raises(ValueError, match="date"):
            ChunkSigner(
                seed_signature=self.SEED_SIGNATURE,
                identity=self.IDENTITY,
                properties=SigV4SigningProperties(region="us-east-1", service="s3"),
            )

    @pytest.mark.parametrize(
        "authorization",
        [
            None,
            "Bearer token",
            "AWS4-HMAC-SHA256 Credential=AKID/20130524/us-east-1/s3/aws4_request",
            "AWS4-HMAC-SHA256 Credential=AKID/20200101/us-east-1/s3/aws4_request, "
            "SignedHeaders=host, Signature=abc",
            "AWS4-HMAC-SHA256 Credential=AKID/20130524/s3/aws4_request, "
            "SignedHeaders=host, Signature=abc",
        ],
    )
    def test_rejects_request_not_signed_with_sigv4(
        self, authorization: str | None
    ) -> None:
        request = self.signed_request()
        del request.fields["Authorization"]
        if authorization is not None:
            request.fields.set_field(
                Field(name="Authorization", values=[authorization])
            )
        with pytest.raises(ValueError):
            ChunkSigner.from_signed_request(request, self.IDENTITY)
