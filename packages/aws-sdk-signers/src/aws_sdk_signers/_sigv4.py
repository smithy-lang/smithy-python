# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""SigV4 signing logic shared by the sync and async signers."""
# ruff: noqa: S101

import datetime
import hmac
import io
from collections.abc import Iterable
from copy import copy, deepcopy
from hashlib import sha256
from typing import Any, Required, TypedDict, TypeGuard
from urllib.parse import parse_qsl, quote

from ._http import AWSRequest, Field, URI
from ._program import Program
from .exceptions import MissingExpectedParameterException
from .interfaces.identity import AWSCredentialsIdentity
from .interfaces.io import ConditionallySeekable, Seekable

HEADERS_EXCLUDED_FROM_SIGNING: tuple[str, ...] = (
    "accept",
    "accept-encoding",
    "authorization",
    "connection",
    "expect",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "user-agent",
    "x-amzn-trace-id",
)
DEFAULT_PORTS: dict[str, int] = {"http": 80, "https": 443}

SIGV4_TIMESTAMP_FORMAT: str = "%Y%m%dT%H%M%SZ"
UNSIGNED_PAYLOAD: str = "UNSIGNED-PAYLOAD"
EVENT_STREAM_CONTENT_TYPE = "application/vnd.amazon.eventstream"
EVENT_STREAM_HASH = "STREAMING-AWS4-HMAC-SHA256-EVENTS"
EMPTY_SHA256_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class SigV4SigningProperties(TypedDict, total=False):
    region: Required[str]
    service: Required[str]
    date: str
    payload_signing_enabled: bool
    content_checksum_enabled: bool
    uri_encode_path: bool
    normalize_path: bool


class SigV4SignerBase:
    """The AWS Signature Version 4 algorithm, written once for both signers.

    Subclasses drive ``_sign`` and ``_canonical_request`` in their own mode and supply
    ``_hash_body``, the only step that reads the request body.
    """

    def string_to_sign(
        self,
        *,
        canonical_request: str,
        signing_properties: SigV4SigningProperties,
    ) -> str:
        """The string to sign is the second step of our signing algorithm which
        concatenates the formal identifier of our signing algorithm, the signing
        DateTime, the scope of our credentials, and a hash of our previously generated
        canonical request. This is another checkpoint that can be used to ensure we're
        constructing our signature as intended.

        The SigV4 specification defines the string to sign as:
            Algorithm \\n
            RequestDateTime \\n
            CredentialScope  \\n
            HashedCanonicalRequest

        :param canonical_request:
            String generated from the `canonical_request` method.
        :param signing_properties:
            SigV4SigningProperties to define signing primitives such as
            the target service, region, and date.
        """
        date = signing_properties.get("date")
        if date is None:
            raise MissingExpectedParameterException(
                "Cannot generate string_to_sign without a valid date "
                f"in your signing_properties. Current value: {date}"
            )
        return (
            "AWS4-HMAC-SHA256\n"
            f"{date}\n"
            f"{credential_scope(signing_properties)}\n"
            f"{sha256(canonical_request.encode()).hexdigest()}"
        )

    def generate_authorization_field(
        self, *, credential: str, signed_headers: list[str], signature: str
    ) -> Field:
        """Generate the `Authorization` field.

        :param credential:
            Credential scope string for generating the Authorization header.
            Defined as:
                <access_key>/<date>/<region>/<service>/<request_type>
        :param signed_headers:
            A list of the field names used in signing.
        :param signature:
            Final hash of the SigV4 signing algorithm generated from the
            canonical request and string to sign.
        """
        signed_headers_str = ";".join(signed_headers)
        auth_str = (
            f"AWS4-HMAC-SHA256 Credential={credential}, "
            f"SignedHeaders={signed_headers_str}, Signature={signature}"
        )
        return Field(name="Authorization", values=[auth_str])

    def _sign(
        self,
        request: AWSRequest,
        identity: AWSCredentialsIdentity,
        properties: SigV4SigningProperties,
    ) -> Program[AWSRequest]:
        validate_identity(identity)
        new_signing_properties = normalize_signing_properties(properties)
        new_request = copy_request(request)
        self._apply_required_fields(
            request=new_request,
            signing_properties=new_signing_properties,
            identity=identity,
        )

        canonical_request = yield from self._canonical_request(
            new_signing_properties, new_request
        )
        string_to_sign = self.string_to_sign(
            canonical_request=canonical_request,
            signing_properties=new_signing_properties,
        )
        signature = hmac.new(
            signing_key(identity.secret_access_key, new_signing_properties),
            string_to_sign.encode(),
            sha256,
        ).hexdigest()

        signing_fields = self._normalize_signing_fields(request=new_request)
        credential = (
            f"{identity.access_key_id}/{credential_scope(new_signing_properties)}"
        )
        new_request.fields.set_field(
            self.generate_authorization_field(
                credential=credential,
                signed_headers=list(signing_fields.keys()),
                signature=signature,
            )
        )
        return new_request

    def _canonical_request(
        self, signing_properties: SigV4SigningProperties, request: AWSRequest
    ) -> Program[str]:
        # The payload goes first so its field modifications are in place before the
        # canonical fields are chosen.
        canonical_payload = yield from self._format_canonical_payload(
            request=request, signing_properties=signing_properties
        )
        canonical_path = self._format_canonical_path(
            path=request.destination.path, signing_properties=signing_properties
        )
        canonical_query = self._format_canonical_query(query=request.destination.query)
        normalized_fields = self._normalize_signing_fields(request=request)
        canonical_fields = self._format_canonical_fields(fields=normalized_fields)
        return (
            f"{request.method.upper()}\n"
            f"{canonical_path}\n"
            f"{canonical_query}\n"
            f"{canonical_fields}\n"
            f"{';'.join(normalized_fields)}\n"
            f"{canonical_payload}"
        )

    def _hash_body(self, request: AWSRequest) -> Any:
        """Effect: hash a request body that isn't None, returning the hex digest."""
        raise NotImplementedError

    def _apply_required_fields(
        self,
        *,
        request: AWSRequest,
        signing_properties: SigV4SigningProperties,
        identity: AWSCredentialsIdentity,
    ) -> None:
        # Apply required X-Amz-Date if neither X-Amz-Date nor Date are present.
        if "Date" not in request.fields and "X-Amz-Date" not in request.fields:
            assert "date" in signing_properties
            request.fields.set_field(
                Field(name="X-Amz-Date", values=[signing_properties["date"]])
            )
        # Apply required X-Amz-Security-Token if token present on identity
        if (
            "X-Amz-Security-Token" not in request.fields
            and identity.session_token is not None
        ):
            request.fields.set_field(
                Field(name="X-Amz-Security-Token", values=[identity.session_token])
            )

    def _format_canonical_path(
        self, *, path: str | None, signing_properties: SigV4SigningProperties
    ) -> str:
        if path is None:
            path = "/"

        uri_encode_path = signing_properties.get("uri_encode_path", True)
        if signing_properties.get("normalize_path", True):
            path = remove_dot_segments(path, remove_consecutive_slashes=uri_encode_path)
        if uri_encode_path:
            return quote(string=path, safe="/")
        return path

    def _format_canonical_query(self, *, query: str | None) -> str:
        if query is None:
            return ""

        query_params = parse_qsl(qs=query, keep_blank_values=True)
        query_parts = (
            (quote(string=key, safe=""), quote(string=value, safe=""))
            for key, value in query_params
        )
        # key-value pairs must be in sorted order for their encoded forms.
        return "&".join(f"{key}={value}" for key, value in sorted(query_parts))

    def _normalize_signing_fields(self, *, request: AWSRequest) -> dict[str, str]:
        # A field with no values is never sent, and trailers aren't headers, so
        # signing either would claim a header line the service never receives.
        normalized_fields = {
            field.name.lower(): _canonical_field_value(field.values)
            for field in request.fields
            if field.kind == "header"
            and field.values
            and field.name.lower() not in HEADERS_EXCLUDED_FROM_SIGNING
        }
        if "host" not in normalized_fields:
            normalized_fields["host"] = self._normalize_host_field(
                uri=request.destination  # type: ignore - TODO(pyright)
            )

        return dict(sorted(normalized_fields.items()))

    def _normalize_host_field(self, *, uri: URI) -> str:
        if uri.port is not None and DEFAULT_PORTS.get(uri.scheme) == uri.port:
            uri_dict = uri.to_dict()
            uri_dict.update({"port": None})
            uri = URI(**uri_dict)
        return uri.netloc

    def _format_canonical_fields(self, *, fields: dict[str, str]) -> str:
        return "".join(f"{key}:{value}\n" for key, value in fields.items())

    def _format_canonical_payload(
        self,
        *,
        request: AWSRequest,
        signing_properties: SigV4SigningProperties,
    ) -> Program[str]:
        if (preset := preset_payload_hash(request)) is not None:
            return preset

        # All insecure connections should be signed
        if request.destination.scheme == "https" and not signing_properties.get(
            "payload_signing_enabled", True
        ):
            payload_hash = UNSIGNED_PAYLOAD
        elif request.body is None:
            payload_hash = EMPTY_SHA256_HASH
        else:
            payload_hash = yield lambda: self._hash_body(request)

        if signing_properties.get("content_checksum_enabled", False):
            request.fields.set_field(
                Field(name="X-Amz-Content-SHA256", values=[payload_hash])
            )
        return payload_hash


def signing_key(secret_key: str, signing_properties: SigV4SigningProperties) -> bytes:
    """Derive the key scoped to the signing date, region and service."""
    assert "date" in signing_properties
    k_date = _hmac(f"AWS4{secret_key}".encode(), signing_properties["date"][0:8])
    k_region = _hmac(k_date, signing_properties["region"])
    k_service = _hmac(k_region, signing_properties["service"])
    return _hmac(k_service, "aws4_request")


def credential_scope(signing_properties: SigV4SigningProperties) -> str:
    """Format the scope as ``<YYYYMMDD>/<AWS Region>/<AWS Service>/aws4_request``."""
    assert "date" in signing_properties
    formatted_date = signing_properties["date"][0:8]
    region = signing_properties["region"]
    service = signing_properties["service"]
    return f"{formatted_date}/{region}/{service}/aws4_request"


def normalize_signing_properties(
    signing_properties: SigV4SigningProperties,
) -> SigV4SigningProperties:
    """Copy the signing properties, defaulting the date to now."""
    new_signing_properties = SigV4SigningProperties(**signing_properties)
    if "date" not in new_signing_properties:
        date_obj = datetime.datetime.now(datetime.UTC)
        new_signing_properties["date"] = date_obj.strftime(SIGV4_TIMESTAMP_FORMAT)
    return new_signing_properties


def validate_identity(identity: AWSCredentialsIdentity) -> None:
    """Perform runtime and expiration checks before attempting signing."""
    if not isinstance(identity, AWSCredentialsIdentity):  # pyright: ignore
        raise ValueError(
            "Received unexpected value for identity parameter. Expected "
            f"AWSCredentialIdentity but received {type(identity)}."
        )
    elif identity.is_expired:
        raise ValueError(
            f"Provided identity expired at {identity.expiration}. Please "
            "refresh the credentials or update the expiration parameter."
        )


def hash_sync_body(request: AWSRequest) -> str:
    """Hash a synchronous request body, buffering it if it can't be rewound."""
    body = request.body
    if not isinstance(body, Iterable):
        raise TypeError(
            "An async body was attached to a synchronous signer. Please use "
            "aws_sdk_signers.aio.AsyncSigV4Signer for async AWSRequests or ensure "
            "your body is of type Iterable[bytes]."
        )

    checksum = sha256()
    if is_seekable(body):
        position = body.tell()
        for chunk in body:  # type: ignore
            checksum.update(chunk)  # type: ignore
        body.seek(position)
    else:
        buffer = io.BytesIO()
        for chunk in body:
            buffer.write(chunk)
            checksum.update(chunk)
        buffer.seek(0)
        request.body = buffer
    return checksum.hexdigest()


def is_seekable(body: Any) -> TypeGuard[Seekable]:
    """Whether a body can be rewound after hashing."""
    if isinstance(body, ConditionallySeekable):
        return body.seekable()
    return isinstance(body, Seekable)


def preset_payload_hash(request: AWSRequest) -> str | None:
    """Return the payload hash fixed by the request, setting it for event streams."""
    if (
        "X-Amz-Content-SHA256" in request.fields
        and len(request.fields["X-Amz-Content-SHA256"].values) == 1
    ):
        return request.fields["X-Amz-Content-SHA256"].values[0]

    if (
        "Content-Type" in request.fields
        and request.fields["Content-Type"].as_string() == EVENT_STREAM_CONTENT_TYPE
    ):
        request.fields.set_field(
            Field(name="X-Amz-Content-SHA256", values=[EVENT_STREAM_HASH])
        )
        return EVENT_STREAM_HASH

    return None


def copy_request(request: AWSRequest) -> AWSRequest:
    """Copies a request for signing, deep-copying only the fields signing modifies.

    The body is shared since streams generally can't be copied, so signing may
    consume a non-seekable one.
    """
    new_request = copy(request)
    new_request.fields = deepcopy(request.fields)
    return new_request


def remove_dot_segments(path: str, remove_consecutive_slashes: bool = True) -> str:
    """Removes dot segments from a path per :rfc:`3986#section-5.2.4`.

    Optionally removes consecutive slashes, true by default.
    :param path: The path to modify.
    :param remove_consecutive_slashes: Whether to remove consecutive slashes.
    :returns: The path with dot segments removed.
    """
    output: list[str] = []
    for segment in path.split("/"):
        if segment == ".":
            continue
        elif segment != "..":
            output.append(segment)
        elif output:
            output.pop()
    if path.startswith("/") and (not output or output[0]):
        output.insert(0, "")
    if output and path.endswith(("/.", "/..")):
        output.append("")
    result = "/".join(output)
    if remove_consecutive_slashes:
        result = result.replace("//", "/")
    return result


def _canonical_field_value(values: list[str]) -> str:
    """Join a field's values the way the service rebuilds them to check a signature.

    Transports send each value as its own header line, and the service joins the
    lines with a bare comma. Each value is trimmed and its internal whitespace is
    collapsed to single spaces, as botocore does; ``str.split`` treats all Unicode
    whitespace as whitespace. Values are never quoted, unlike ``Field.as_string``.
    """
    return ",".join(" ".join(value.split()) for value in values)


def _hmac(key: bytes, value: str) -> bytes:
    return hmac.new(key=key, msg=value.encode(), digestmod=sha256).digest()
