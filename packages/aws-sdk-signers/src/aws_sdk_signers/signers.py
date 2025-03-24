# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# ruff: noqa: S101
import asyncio
import datetime
import hmac
import io
import warnings
from asyncio import iscoroutinefunction
from binascii import hexlify
from collections.abc import AsyncIterable, Iterable
from copy import deepcopy
from hashlib import sha256
from typing import TYPE_CHECKING, Required, TypedDict
from urllib.parse import parse_qsl, quote

from ._http import AWSRequest, Field, URI
from ._identity import AWSCredentialIdentity
from ._io import AsyncBytesReader
from .exceptions import AWSSDKWarning, MissingExpectedParameterException
from .interfaces.identity import AWSCredentialsIdentity as _AWSCredentialsIdentity
from .interfaces.io import AsyncSeekable, Seekable

if TYPE_CHECKING:
    from .interfaces.events import EventHeaderEncoder, EventMessage

HEADERS_EXCLUDED_FROM_SIGNING: tuple[str, ...] = (
    "accept",
    "accept-encoding",
    "authorization",
    "connection",
    "expect",
    "user-agent",
    "x-amzn-trace-id",
)
DEFAULT_PORTS: dict[str, int] = {"http": 80, "https": 443}

SIGV4_TIMESTAMP_FORMAT: str = "%Y%m%dT%H%M%SZ"
UNSIGNED_PAYLOAD: str = "UNSIGNED-PAYLOAD"
EMPTY_SHA256_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class SigV4SigningProperties(TypedDict, total=False):
    region: Required[str]
    service: Required[str]
    date: str
    payload_signing_enabled: bool
    content_checksum_enabled: bool
    uri_encode_path: bool


class SigV4Signer:
    """Request signer for applying the AWS Signature Version 4 algorithm."""

    def sign(
        self,
        *,
        signing_properties: SigV4SigningProperties,
        http_request: AWSRequest,
        identity: AWSCredentialIdentity,
    ) -> AWSRequest:
        """Generate and apply a SigV4 Signature to a copy of the supplied request.

        :param signing_properties: SigV4SigningProperties to define signing primitives
            such as the target service, region, and date.
        :param http_request: An AWSRequest to sign prior to sending to the service.
        :param identity: A set of credentials representing an AWS Identity or role
            capacity.
        """
        # Copy and prepopulate any missing values in the
        # supplied request and signing properties.
        self._validate_identity(identity=identity)
        new_signing_properties = self._normalize_signing_properties(
            signing_properties=signing_properties
        )
        assert "date" in new_signing_properties

        new_request = self._generate_new_request(request=http_request)
        self._apply_required_fields(
            request=new_request,
            signing_properties=new_signing_properties,
            identity=identity,
        )

        # Construct core signing components
        canonical_request = self.canonical_request(
            signing_properties=new_signing_properties,
            request=new_request,
        )
        string_to_sign = self.string_to_sign(
            canonical_request=canonical_request,
            signing_properties=new_signing_properties,
        )
        signature = self._signature(
            string_to_sign=string_to_sign,
            secret_key=identity.secret_access_key,
            signing_properties=new_signing_properties,
        )

        signing_fields = self._normalize_signing_fields(request=new_request)
        credential_scope = self._scope(signing_properties=new_signing_properties)
        credential = f"{identity.access_key_id}/{credential_scope}"
        authorization = self.generate_authorization_field(
            credential=credential,
            signed_headers=list(signing_fields.keys()),
            signature=signature,
        )
        new_request.fields.set_field(authorization)

        return new_request

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

    def _signature(
        self,
        *,
        string_to_sign: str,
        secret_key: str,
        signing_properties: SigV4SigningProperties,
    ) -> str:
        """Sign the string to sign.

        In SigV4, a signing key is created that is scoped to a specific region and
        service. The date, region, service and resulting signing key are individually
        hashed, then the composite hash is used to sign the string to sign.
        """

        # Components of Signing Key Calculation
        #
        # DateKey              = HMAC-SHA256("AWS4"+"<SecretAccessKey>", "<YYYYMMDD>")
        # DateRegionKey        = HMAC-SHA256(<DateKey>, "<aws-region>")
        # DateRegionServiceKey = HMAC-SHA256(<DateRegionKey>, "<aws-service>")
        # SigningKey = HMAC-SHA256(<DateRegionServiceKey>, "aws4_request")
        assert "date" in signing_properties
        k_date = self._hash(
            key=f"AWS4{secret_key}".encode(), value=signing_properties["date"][0:8]
        )
        k_region = self._hash(key=k_date, value=signing_properties["region"])
        k_service = self._hash(key=k_region, value=signing_properties["service"])
        k_signing = self._hash(key=k_service, value="aws4_request")

        return self._hash(key=k_signing, value=string_to_sign).hex()

    def _hash(self, key: bytes, value: str) -> bytes:
        return hmac.new(key=key, msg=value.encode(), digestmod=sha256).digest()

    def _validate_identity(self, *, identity: AWSCredentialIdentity) -> None:
        """Perform runtime and expiration checks before attempting signing."""
        if not isinstance(identity, _AWSCredentialsIdentity):  # pyright: ignore
            raise ValueError(
                "Received unexpected value for identity parameter. Expected "
                f"AWSCredentialIdentity but received {type(identity)}."
            )
        elif identity.is_expired:
            raise ValueError(
                f"Provided identity expired at {identity.expiration}. Please "
                "refresh the credentials or update the expiration parameter."
            )

    def _normalize_signing_properties(
        self, *, signing_properties: SigV4SigningProperties
    ) -> SigV4SigningProperties:
        # Create copy of signing properties to avoid mutating the original
        new_signing_properties = SigV4SigningProperties(**signing_properties)
        if "date" not in new_signing_properties:
            date_obj = datetime.datetime.now(datetime.UTC)
            new_signing_properties["date"] = date_obj.strftime(SIGV4_TIMESTAMP_FORMAT)
        return new_signing_properties

    def _generate_new_request(self, *, request: AWSRequest) -> AWSRequest:
        return deepcopy(request)

    def _apply_required_fields(
        self,
        *,
        request: AWSRequest,
        signing_properties: SigV4SigningProperties,
        identity: AWSCredentialIdentity,
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

    def canonical_request(
        self, *, signing_properties: SigV4SigningProperties, request: AWSRequest
    ) -> str:
        """The canonical request is a standardized string laying out the components used
        in the SigV4 signing algorithm. This is useful to quickly compare inputs to find
        signature mismatches and unintended variances.

        The SigV4 specification defines the canonical request to be:
            <HTTPMethod>\n
            <CanonicalURI>\n
            <CanonicalQueryString>\n
            <CanonicalHeaders>\n
            <SignedHeaders>\n
            <HashedPayload>

        :param signing_properties:
            SigV4SigningProperties to define signing primitives such as
            the target service, region, and date.
        :param request:
            An AWSRequest to use for generating a SigV4 signature.
        """
        # We generate the payload first to ensure any field modifications
        # are in place before choosing the canonical fields.
        canonical_payload = self._format_canonical_payload(
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
            Algorithm \n
            RequestDateTime \n
            CredentialScope  \n
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
            f"{self._scope(signing_properties=signing_properties)}\n"
            f"{sha256(canonical_request.encode()).hexdigest()}"
        )

    def _scope(self, signing_properties: SigV4SigningProperties) -> str:
        assert "date" in signing_properties
        formatted_date = signing_properties["date"][0:8]
        region = signing_properties["region"]
        service = signing_properties["service"]
        # Scope format: <YYYYMMDD>/<AWS Region>/<AWS Service>/aws4_request
        return f"{formatted_date}/{region}/{service}/aws4_request"

    def _format_canonical_path(
        self, *, path: str | None, signing_properties: SigV4SigningProperties
    ) -> str:
        if path is None:
            path = "/"

        if signing_properties.get("uri_encode_path", True):
            normalized_path = _remove_dot_segments(path)
            return quote(string=normalized_path, safe="/")
        else:
            return _remove_dot_segments(path, remove_consecutive_slashes=False)

    def _format_canonical_query(self, *, query: str | None) -> str:
        if query is None:
            return ""

        query_params = parse_qsl(qs=query)
        query_parts = (
            (quote(string=key, safe=""), quote(string=value, safe=""))
            for key, value in query_params
        )
        # key-value pairs must be in sorted order for their encoded forms.
        return "&".join(f"{key}={value}" for key, value in sorted(query_parts))

    def _normalize_signing_fields(self, *, request: AWSRequest) -> dict[str, str]:
        normalized_fields = {
            field.name.lower(): field.as_string()
            for field in request.fields
            if self._is_signable_header(field.name.lower())
        }
        if "host" not in normalized_fields:
            normalized_fields["host"] = self._normalize_host_field(
                uri=request.destination  # type: ignore - TODO(pyright)
            )

        return dict(sorted(normalized_fields.items()))

    def _is_signable_header(self, field_name: str):
        if field_name in HEADERS_EXCLUDED_FROM_SIGNING:
            return False
        return True

    def _normalize_host_field(self, *, uri: URI) -> str:
        if uri.port is not None and DEFAULT_PORTS.get(uri.scheme) == uri.port:
            uri_dict = uri.to_dict()
            uri_dict.update({"port": None})
            uri = URI(**uri_dict)
        return uri.netloc

    def _format_canonical_fields(self, *, fields: dict[str, str]) -> str:
        return "".join(
            f"{key}:{' '.join(value.split())}\n" for key, value in fields.items()
        )

    def _should_sha256_sign_payload(
        self,
        *,
        request: AWSRequest,
        signing_properties: SigV4SigningProperties,
    ) -> bool:
        # All insecure connections should be signed
        if request.destination.scheme != "https":
            return True

        return signing_properties.get("payload_signing_enabled", True)

    def _format_canonical_payload(
        self,
        *,
        request: AWSRequest,
        signing_properties: SigV4SigningProperties,
    ) -> str:
        payload_hash = self._compute_payload_hash(
            request=request, signing_properties=signing_properties
        )
        if signing_properties.get("content_checksum_enabled", False):
            request.fields.set_field(
                Field(name="X-Amz-Content-SHA256", values=[payload_hash])
            )
        return payload_hash

    def _compute_payload_hash(
        self, *, request: AWSRequest, signing_properties: SigV4SigningProperties
    ) -> str:
        if not self._should_sha256_sign_payload(
            request=request, signing_properties=signing_properties
        ):
            return UNSIGNED_PAYLOAD

        body = request.body

        if body is None:
            return EMPTY_SHA256_HASH

        if not isinstance(body, Iterable):
            raise TypeError(
                "An async body was attached to a synchronous signer. Please use "
                "AsyncSigV4Signer for async AWSRequests or ensure your body is "
                "of type Iterable[bytes]."
            )

        warnings.warn(
            "Payload signing is enabled. This may result in "
            "decreased performance for large request bodies.",
            AWSSDKWarning,
        )

        checksum = sha256()
        if isinstance(body, Seekable):
            position = body.tell()
            for chunk in body:
                checksum.update(chunk)
            body.seek(position)
        else:
            buffer = io.BytesIO()
            for chunk in body:
                buffer.write(chunk)
                checksum.update(chunk)
            buffer.seek(0)
            request.body = buffer
        return checksum.hexdigest()


class AsyncSigV4Signer:
    """Request signer for applying the AWS Signature Version 4 algorithm."""

    async def sign(
        self,
        *,
        signing_properties: SigV4SigningProperties,
        http_request: AWSRequest,
        identity: AWSCredentialIdentity,
    ) -> AWSRequest:
        """Generate and apply a SigV4 Signature to a copy of the supplied request.

        :param signing_properties: SigV4SigningProperties to define signing primitives
            such as the target service, region, and date.
        :param http_request: An AWSRequest to sign prior to sending to the service.
        :param identity: A set of credentials representing an AWS Identity or role
            capacity.
        """
        # Copy and prepopulate any missing values in the
        # supplied request and signing properties.

        await self._validate_identity(identity=identity)
        new_signing_properties = await self._normalize_signing_properties(
            signing_properties=signing_properties
        )
        new_request = await self._generate_new_request(request=http_request)
        await self._apply_required_fields(
            request=new_request,
            signing_properties=new_signing_properties,
            identity=identity,
        )

        # Construct core signing components
        canonical_request = await self.canonical_request(
            signing_properties=signing_properties,
            request=new_request,
        )
        string_to_sign = await self.string_to_sign(
            canonical_request=canonical_request,
            signing_properties=new_signing_properties,
        )
        signature = await self._signature(
            string_to_sign=string_to_sign,
            secret_key=identity.secret_access_key,
            signing_properties=new_signing_properties,
        )

        signing_fields = await self._normalize_signing_fields(request=new_request)
        credential_scope = await self._scope(signing_properties=new_signing_properties)
        credential = f"{identity.access_key_id}/{credential_scope}"
        authorization = await self.generate_authorization_field(
            credential=credential,
            signed_headers=list(signing_fields.keys()),
            signature=signature,
        )
        new_request.fields.set_field(authorization)
        return new_request

    async def generate_authorization_field(
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

    async def _signature(
        self,
        *,
        string_to_sign: str,
        secret_key: str,
        signing_properties: SigV4SigningProperties,
    ) -> str:
        """Sign the string to sign.

        In SigV4, a signing key is created that is scoped to a specific region and
        service. The date, region, service and resulting signing key are individually
        hashed, then the composite hash is used to sign the string to sign.
        """

        # Components of Signing Key Calculation
        #
        # DateKey              = HMAC-SHA256("AWS4"+"<SecretAccessKey>", "<YYYYMMDD>")
        # DateRegionKey        = HMAC-SHA256(<DateKey>, "<aws-region>")
        # DateRegionServiceKey = HMAC-SHA256(<DateRegionKey>, "<aws-service>")
        # SigningKey = HMAC-SHA256(<DateRegionServiceKey>, "aws4_request")
        assert "date" in signing_properties
        k_date = await self._hash(
            key=f"AWS4{secret_key}".encode(), value=signing_properties["date"][0:8]
        )
        k_region = await self._hash(key=k_date, value=signing_properties["region"])
        k_service = await self._hash(key=k_region, value=signing_properties["service"])
        k_signing = await self._hash(key=k_service, value="aws4_request")
        final_hash = await self._hash(key=k_signing, value=string_to_sign)

        return final_hash.hex()

    async def _hash(self, key: bytes, value: str) -> bytes:
        return hmac.new(key=key, msg=value.encode(), digestmod=sha256).digest()

    async def _validate_identity(self, *, identity: AWSCredentialIdentity) -> None:
        """Perform runtime and expiration checks before attempting signing."""
        if not isinstance(identity, _AWSCredentialsIdentity):  # pyright: ignore
            raise ValueError(
                "Received unexpected value for identity parameter. Expected "
                f"AWSCredentialIdentity but received {type(identity)}."
            )
        elif identity.is_expired:
            raise ValueError(
                f"Provided identity expired at {identity.expiration}. Please "
                "refresh the credentials or update the expiration parameter."
            )

    async def _normalize_signing_properties(
        self, *, signing_properties: SigV4SigningProperties
    ) -> SigV4SigningProperties:
        # Create copy of signing properties to avoid mutating the original
        new_signing_properties = SigV4SigningProperties(**signing_properties)
        if "date" not in new_signing_properties:
            date_obj = datetime.datetime.now(datetime.UTC)
            new_signing_properties["date"] = date_obj.strftime(SIGV4_TIMESTAMP_FORMAT)
        return new_signing_properties

    async def _generate_new_request(self, *, request: AWSRequest) -> AWSRequest:
        return deepcopy(request)

    async def _apply_required_fields(
        self,
        *,
        request: AWSRequest,
        signing_properties: SigV4SigningProperties,
        identity: AWSCredentialIdentity,
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

    async def canonical_request(
        self, *, signing_properties: SigV4SigningProperties, request: AWSRequest
    ) -> str:
        """The canonical request is a standardized string laying out the components used
        in the SigV4 signing algorithm. This is useful to quickly compare inputs to find
        signature mismatches and unintended variances.

        The SigV4 specification defines the canonical request to be:
            <HTTPMethod>\n
            <CanonicalURI>\n
            <CanonicalQueryString>\n
            <CanonicalHeaders>\n
            <SignedHeaders>\n
            <HashedPayload>

        :param signing_properties:
            SigV4SigningProperties to define signing primitives such as
            the target service, region, and date.
        :param request:
            An AWSRequest to use for generating a SigV4 signature.
        """
        # We generate the payload first to ensure any field modifications
        # are in place before choosing the canonical fields.
        canonical_payload = await self._format_canonical_payload(
            request=request, signing_properties=signing_properties
        )
        canonical_path = await self._format_canonical_path(
            path=request.destination.path, signing_properties=signing_properties
        )
        canonical_query = await self._format_canonical_query(
            query=request.destination.query
        )
        normalized_fields = await self._normalize_signing_fields(request=request)
        canonical_fields = await self._format_canonical_fields(fields=normalized_fields)
        return (
            f"{request.method.upper()}\n"
            f"{canonical_path}\n"
            f"{canonical_query}\n"
            f"{canonical_fields}\n"
            f"{';'.join(normalized_fields)}\n"
            f"{canonical_payload}"
        )

    async def string_to_sign(
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
            Algorithm \n
            RequestDateTime \n
            CredentialScope  \n
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
        scope = await self._scope(signing_properties=signing_properties)
        return (
            "AWS4-HMAC-SHA256\n"
            f"{date}\n"
            f"{scope}\n"
            f"{sha256(canonical_request.encode()).hexdigest()}"
        )

    async def _scope(self, signing_properties: SigV4SigningProperties) -> str:
        assert "date" in signing_properties
        formatted_date = signing_properties["date"][0:8]
        region = signing_properties["region"]
        service = signing_properties["service"]
        # Scope format: <YYYYMMDD>/<AWS Region>/<AWS Service>/aws4_request
        return f"{formatted_date}/{region}/{service}/aws4_request"

    async def _format_canonical_path(
        self, *, path: str | None, signing_properties: SigV4SigningProperties
    ) -> str:
        if path is None:
            path = "/"

        if signing_properties.get("uri_encode_path", True):
            normalized_path = _remove_dot_segments(path)
            return quote(string=normalized_path, safe="/")
        else:
            return _remove_dot_segments(path, remove_consecutive_slashes=False)

    async def _format_canonical_query(self, *, query: str | None) -> str:
        if query is None:
            return ""

        query_params = parse_qsl(qs=query)
        query_parts = (
            (quote(string=key, safe=""), quote(string=value, safe=""))
            for key, value in query_params
        )
        # key-value pairs must be in sorted order for their encoded forms.
        return "&".join(f"{key}={value}" for key, value in sorted(query_parts))

    async def _normalize_signing_fields(self, *, request: AWSRequest) -> dict[str, str]:
        normalized_fields = {
            field.name.lower(): field.as_string()
            for field in request.fields
            if self._is_signable_header(field.name.lower())
        }
        if "host" not in normalized_fields:
            normalized_fields["host"] = await self._normalize_host_field(
                uri=request.destination  # type: ignore - TODO(pyright)
            )

        return dict(sorted(normalized_fields.items()))

    def _is_signable_header(self, field_name: str):
        if field_name in HEADERS_EXCLUDED_FROM_SIGNING:
            return False
        return True

    async def _normalize_host_field(self, *, uri: URI) -> str:
        if uri.port is not None and DEFAULT_PORTS.get(uri.scheme) == uri.port:
            uri_dict = uri.to_dict()
            uri_dict.update({"port": None})
            uri = URI(**uri_dict)
        return uri.netloc

    async def _format_canonical_fields(self, *, fields: dict[str, str]) -> str:
        return "".join(
            f"{key}:{' '.join(value.split())}\n" for key, value in fields.items()
        )

    async def _should_sha256_sign_payload(
        self,
        *,
        request: AWSRequest,
        signing_properties: SigV4SigningProperties,
    ) -> bool:
        # All insecure connections should be signed
        if request.destination.scheme != "https":
            return True

        return signing_properties.get("payload_signing_enabled", True)

    async def _format_canonical_payload(
        self,
        *,
        request: AWSRequest,
        signing_properties: SigV4SigningProperties,
    ) -> str:
        if (
            "X-Amz-Content-SHA256" in request.fields
            and len(request.fields["X-Amz-Content-SHA256"].values) == 1
        ):
            return request.fields["X-Amz-Content-SHA256"].values[0]

        payload_hash = await self._compute_payload_hash(
            request=request, signing_properties=signing_properties
        )
        if signing_properties.get("content_checksum_enabled", False):
            request.fields.set_field(
                Field(name="X-Amz-Content-SHA256", values=[payload_hash])
            )
        return payload_hash

    async def _compute_payload_hash(
        self, *, request: AWSRequest, signing_properties: SigV4SigningProperties
    ) -> str:
        if not await self._should_sha256_sign_payload(
            request=request, signing_properties=signing_properties
        ):
            return UNSIGNED_PAYLOAD

        body = request.body

        if body is None:
            return EMPTY_SHA256_HASH

        if not isinstance(body, AsyncIterable):
            raise TypeError(
                "A sync body was attached to an asynchronous signer. Please use "
                "SigV4Signer for sync AWSRequests or ensure your body is "
                "of type AsyncIterable[bytes]."
            )
        warnings.warn(
            "Payload signing is enabled. This may result in "
            "decreased performance for large request bodies.",
            AWSSDKWarning,
        )

        checksum = sha256()
        if isinstance(body, AsyncSeekable) and iscoroutinefunction(body.seek):
            position = body.tell()
            async for chunk in body:
                checksum.update(chunk)
            await body.seek(position)
        else:
            buffer = io.BytesIO()
            async for chunk in body:
                buffer.write(chunk)
                checksum.update(chunk)
            buffer.seek(0)
            request.body = AsyncBytesReader(buffer)
        return checksum.hexdigest()


class AsyncEventSigner:
    def __init__(
        self,
        *,
        signing_properties: SigV4SigningProperties,
        identity: AWSCredentialIdentity,
        initial_signature: bytes,
    ):
        self._signing_properties = signing_properties
        self._identity = identity
        self._prior_signature = initial_signature
        self._signing_lock = asyncio.Lock()

    async def sign_event(
        self,
        *,
        event_message: "EventMessage",
        event_encoder_cls: type["EventHeaderEncoder"],
    ) -> "EventMessage":
        async with self._signing_lock:
            # Copy and prepopulate any missing values in the
            # signing properties.
            new_signing_properties = SigV4SigningProperties(  # type: ignore
                **self._signing_properties
            )
            # TODO: If date is in properties, parse a datetime from it.
            date_obj = datetime.datetime.now(datetime.UTC)
            if "date" not in new_signing_properties:
                new_signing_properties["date"] = date_obj.strftime(
                    SIGV4_TIMESTAMP_FORMAT
                )

            timestamp = new_signing_properties["date"]
            headers: dict[str, str | bytes | datetime.datetime] = {":date": date_obj}
            encoder = event_encoder_cls()
            encoder.encode_headers(headers)
            encoded_headers = encoder.get_result()

            payload = event_message.encode()

            string_to_sign = await self._event_string_to_sign(
                timestamp=timestamp,
                scope=self._scope(new_signing_properties),
                encoded_headers=encoded_headers,
                payload=payload,
                prior_signature=self._prior_signature,
            )
            event_signature = await self._sign_event(
                timestamp=timestamp,
                string_to_sign=string_to_sign,
                signing_properties=new_signing_properties,
            )
            headers[":chunk-signature"] = event_signature

            event_message.headers = headers
            event_message.payload = payload

            # set new prior signature before releasing the lock
            self._prior_signature = hexlify(event_signature)

        return event_message

    async def _event_string_to_sign(
        self,
        *,
        timestamp: str,
        scope: str,
        encoded_headers: bytes,
        payload: bytes,
        prior_signature: bytes,
    ) -> str:
        return (
            "AWS4-HMAC-SHA256-PAYLOAD\n"
            f"{timestamp}\n"
            f"{scope}\n"
            f"{prior_signature.decode('utf-8')}\n"
            f"{sha256(encoded_headers).hexdigest()}\n"
            f"{sha256(payload).hexdigest()}"
        )

    async def _sign_event(
        self,
        *,
        timestamp: str,
        string_to_sign: str,
        signing_properties: SigV4SigningProperties,
    ) -> bytes:
        key = self._identity.secret_access_key.encode("utf-8")
        today = timestamp[:8].encode("utf-8")
        k_date = self._hash(b"AWS4" + key, today)
        k_region = self._hash(k_date, signing_properties["region"].encode("utf-8"))
        k_service = self._hash(k_region, signing_properties["service"].encode("utf-8"))
        k_signing = self._hash(k_service, b"aws4_request")
        return self._hash(k_signing, string_to_sign.encode("utf-8"))

    def _hash(self, key: bytes, msg: bytes) -> bytes:
        return hmac.new(key, msg, sha256).digest()

    def _scope(self, signing_properties: SigV4SigningProperties) -> str:
        assert "date" in signing_properties
        formatted_date = signing_properties["date"][0:8]
        region = signing_properties["region"]
        service = signing_properties["service"]
        # Scope format: <YYYYMMDD>/<AWS Region>/<AWS Service>/aws4_request
        return f"{formatted_date}/{region}/{service}/aws4_request"


def _remove_dot_segments(path: str, remove_consecutive_slashes: bool = True) -> str:
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
