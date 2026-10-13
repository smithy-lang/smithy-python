# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import copy
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
    AsyncBytesReader,
    AsyncEventSigner,
    AsyncSigV4Signer,
    AWSCredentialIdentity,
    AWSRequest,
    Field,
    Fields,
    SigV4Signer,
    SigV4SigningProperties,
    URI,
)
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


class UnreadableAsyncStream:
    def __aiter__(self) -> typing.Self:
        return self

    async def __anext__(self) -> bytes:
        raise Exception("Read should not have been called!")


class TestAsyncEventSigner:
    async def test_sign_wraps_event_message_payload(
        self,
        aws_identity: AWSCredentialIdentity,
    ) -> None:
        signer = AsyncEventSigner(
            initial_signature=b"initial-signature",
            event_encoder_cls=EventHeaderEncoder,
        )
        message = EventMessage(
            headers={":message-type": "event", ":event-type": "AudioEvent"},
            payload=b"audio",
        )

        signed = await signer.sign(
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

    async def test_sign_empty_uses_zero_byte_outer_payload(
        self,
        aws_identity: AWSCredentialIdentity,
    ) -> None:
        signer = AsyncEventSigner(
            initial_signature=b"initial-signature",
            event_encoder_cls=EventHeaderEncoder,
        )

        signed = await signer.sign_empty(
            event=EventMessage(),
            identity=aws_identity,
            properties=SigV4SigningProperties(region="us-west-2", service="transcribe"),
        )

        decoded = Event.decode(BytesIO(signed.encode()))
        assert decoded is not None
        assert decoded.message.payload == b""
        assert ":date" in decoded.message.headers
        assert ":chunk-signature" in decoded.message.headers

    async def test_sign_empty_rejects_non_empty_event(
        self,
        aws_identity: AWSCredentialIdentity,
    ) -> None:
        signer = AsyncEventSigner(
            initial_signature=b"initial-signature",
            event_encoder_cls=EventHeaderEncoder,
        )

        with pytest.raises(ValueError):
            await signer.sign_empty(
                event=EventMessage(headers={"foo": "bar"}),
                identity=aws_identity,
                properties=SigV4SigningProperties(
                    region="us-west-2", service="transcribe"
                ),
            )

        with pytest.raises(ValueError):
            await signer.sign_empty(
                event=EventMessage(payload=b"audio"),
                identity=aws_identity,
                properties=SigV4SigningProperties(
                    region="us-west-2", service="transcribe"
                ),
            )

    async def test_sign_rejects_events_after_empty_event(
        self,
        aws_identity: AWSCredentialIdentity,
    ) -> None:
        signer = AsyncEventSigner(
            initial_signature=b"initial-signature",
            event_encoder_cls=EventHeaderEncoder,
        )
        properties = SigV4SigningProperties(region="us-west-2", service="transcribe")

        await signer.sign_empty(
            event=EventMessage(),
            identity=aws_identity,
            properties=properties,
        )

        with pytest.raises(RuntimeError, match="final empty event"):
            await signer.sign(
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

    async def test_format_canonical_query_keeps_blank_values(self) -> None:
        canonical_query = await self.SIGV4_ASYNC_SIGNER._format_canonical_query(  # pyright: ignore[reportPrivateUsage]
            query="foo=bar&baz="
        )
        assert canonical_query == "baz=&foo=bar"

    async def test_format_canonical_query_with_literal_query_param(self) -> None:
        canonical_query = await self.SIGV4_ASYNC_SIGNER._format_canonical_query(  # pyright: ignore[reportPrivateUsage]
            query="sync"
        )
        assert canonical_query == "sync="

    @pytest.mark.parametrize("options, path, expected", CANONICAL_PATH_CASES)
    async def test_format_canonical_path(
        self, options: dict[str, bool], path: str, expected: str
    ) -> None:
        properties = SigV4SigningProperties(region="us-west-2", service="s3", **options)  # type: ignore[typeddict-item]
        canonical_path = await self.SIGV4_ASYNC_SIGNER._format_canonical_path(  # pyright: ignore[reportPrivateUsage]
            path=path, signing_properties=properties
        )
        assert canonical_path == expected
