# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import hmac
import warnings
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from typing import AsyncGenerator, NotRequired, TypedDict
from urllib.parse import parse_qsl, quote

from smithy_python import interfaces
from smithy_python._private import URI, Field
from smithy_python._private.auth import HTTPSigner
from smithy_python._private.http import HTTPRequest
from smithy_python.async_utils import async_list
from smithy_python.exceptions import SmithyHTTPException, SmithyIdentityException
from smithy_python.interfaces.auth import SigningProperties
from smithy_python.interfaces.http import HTTPRequest as HTTPRequestInterface
from smithy_python.utils import remove_dot_segments

from aws_smithy_python.identity import AWSCredentialIdentity

REQUIRED_SIGNING_PROPERTIES: tuple[str, ...] = ("region", "service")
UNSIGNED_PAYLOAD: str = "UNSIGNED-PAYLOAD"
STREAMING_UNSIGNED_PAYLOAD_TRAILER: str = "STREAMING-UNSIGNED-PAYLOAD-TRAILER"
SIGV4_TIMESTAMP_FORMAT: str = "%Y%m%dT%H%M%SZ"
HEADERS_EXCLUDED_FROM_SIGNING: tuple[str, ...] = (
    "authorization",
    "expect",
    "user-agent",
    "x-amz-content-sha256",
    "x-amzn-trace-id",
)
DEFAULT_EXPIRES: int = 3600
PAYLOAD_BUFFER: int = 1024**2
EMPTY_SHA256_HASH: str = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)
DEFAULT_PORTS: dict[str, int] = {"https": 443, "http": 80}


class SigV4SigningProperties(SigningProperties):
    region: str
    service: str
    expires: NotRequired[int]
    payload_signing_enabled: NotRequired[bool]
    checksum: NotRequired[dict[str, dict[str, str]]]


class SignatureKwargs(TypedDict):
    http_request: HTTPRequest
    formatted_headers: dict[str, str]
    signed_headers: str
    date: str
    scope: str


class SigV4Signer(HTTPSigner[AWSCredentialIdentity, SigV4SigningProperties]):
    """Sign requests using the AWS Signature Version 4 algorithm."""

    async def sign(
        self,
        *,
        http_request: HTTPRequestInterface,
        identity: AWSCredentialIdentity,
        signing_properties: SigV4SigningProperties,
    ) -> HTTPRequest:
        """Sign a request using the `Authorization` header.

        Specifications can be found at:
        https://docs.aws.amazon.com/general/latest/gr/create-signed-request.html

        :param http_request: The request to sign.
        :param identity: The identity to use for signing. Contains authentication
        credentials.
        :param signing_properties: The properties to use for signing.
        """
        signature_kwargs = await self._get_signature_kwargs(
            http_request, identity, signing_properties
        )
        signature = await self._generate_signature(
            secret_access_key=identity.secret_access_key,
            signing_properties=signing_properties,
            **signature_kwargs,
        )
        credential_scope = (
            f"Credential={identity.access_key_id}/{signature_kwargs['scope']}"
        )
        auth_header = self._authorization_header(
            signature, credential_scope, signature_kwargs["signed_headers"]
        )
        new_request = signature_kwargs["http_request"]
        new_request.fields.set_field(auth_header)
        return new_request

    async def _get_signature_kwargs(
        self,
        http_request: HTTPRequestInterface,
        identity: AWSCredentialIdentity,
        signing_properties: SigV4SigningProperties,
    ) -> SignatureKwargs:
        """Get the arguments needed to generate a signature.

        Check that the identity and signing properties are valid, generate the headers
        to add to the request, create a new request with the headers added, format the
        headers for signing, and generate the scope.
        """

        self._validate_identity_and_signing_properties(identity, signing_properties)
        date = datetime.now(tz=timezone.utc).strftime(SIGV4_TIMESTAMP_FORMAT)
        (
            new_request,
            formatted_headers,
        ) = await self._generate_new_request_and_format_headers_for_signing(
            http_request, identity, date
        )
        # Signed headers are comprised of just the header keys delimited by
        # a semicolon.
        signed_headers = ";".join(formatted_headers)
        scope = self._scope(date, signing_properties)
        return {
            "http_request": new_request,
            "formatted_headers": formatted_headers,
            "signed_headers": signed_headers,
            "date": date,
            "scope": scope,
        }

    def _validate_identity_and_signing_properties(
        self,
        identity: AWSCredentialIdentity,
        signing_properties: SigV4SigningProperties,
    ) -> None:
        if not all(key in signing_properties for key in REQUIRED_SIGNING_PROPERTIES):
            raise SmithyHTTPException(
                f"The signing properties {', '.join(REQUIRED_SIGNING_PROPERTIES)} are "
                f"required for SigV4 auth, but found: {', '.join(signing_properties)}."
            )
        if not isinstance(identity, AWSCredentialIdentity):
            raise SmithyIdentityException(
                "Invalid identity type. Expected AWSCredentialIdentity, "
                f"but received {type(identity)}."
            )

    async def _generate_new_request_and_format_headers_for_signing(
        self,
        http_request: HTTPRequestInterface,
        identity: AWSCredentialIdentity,
        date: str,
    ) -> tuple[HTTPRequest, dict[str, str]]:
        """Generate a new request with only allowed headers.

        Also format allowed headers for signing. Remove headers that are excluded from
        SigV4 signature computation.
        """
        new_request = deepcopy(http_request)
        fields = new_request.fields
        # Use `set_field `to overwrite any existing headers instead of `extend`
        # which appends to the existing header.
        fields.set_field(Field(name="X-Amz-Date", values=[date]))
        if identity.session_token:
            fields.set_field(
                Field(name="X-Amz-Security-Token", values=[identity.session_token])
            )
        elif "X-Amz-Security-Token" in fields:
            fields.remove_field("X-Amz-Security-Token")

        formatted_headers = {}
        # copy the fields to avoid mutating the original ordered dict
        for field in list(fields):
            l_key = field.name.lower()
            if l_key in HEADERS_EXCLUDED_FROM_SIGNING:
                fields.remove_field(field.name)
            else:
                value = field.as_string(delimiter=",")
                formatted_headers[l_key] = value
        if "host" not in formatted_headers:
            uri = new_request.destination
            if uri.port is not None and DEFAULT_PORTS.get(uri.scheme) == uri.port:
                # remove port from netloc
                uri = self._generate_new_uri(uri, {"port": None})
                new_request.destination = uri
            formatted_headers["host"] = uri.netloc
            fields.set_field(Field(name="Host", values=[uri.netloc]))
        sorted_formatted_headers = dict(sorted(formatted_headers.items()))
        return new_request, sorted_formatted_headers

    def _scope(self, date: str, signing_properties: SigV4SigningProperties) -> str:
        """Binds the signature to a specific date, AWS region, and service in the
        following format:

        <YYYYMMDD>/<AWS Region>/<AWS Service>/aws4_request
        """
        return (
            f"{date[0:8]}/{signing_properties['region']}/"
            f"{signing_properties['service']}/aws4_request"
        )

    def _generate_new_uri(
        self, uri: interfaces.URI, params: interfaces.URIParameters
    ) -> URI:
        """Generate a new URI with kwargs."""
        uri_dict = uri.to_dict()
        uri_dict.update(params)
        return URI(**uri_dict)

    async def _generate_signature(
        self,
        http_request: HTTPRequestInterface,
        formatted_headers: dict[str, str],
        signed_headers: str,
        secret_access_key: str,
        signing_properties: SigV4SigningProperties,
        date: str,
        scope: str,
        payload: str | None = None,
    ) -> str:
        """Generate the signature for a request.

        :param http_request: The request to sign.
        :param formatted_headers: The formatted header keys and values to sign.
        :param signed_headers: The semicolon-delimited header keys to sign.
        :param secret_access_key: The secret access key to use in the signature.
        :param signing_properties: The signing properties to use in signing.
        :param date: The date to use in the signature in `%Y%m%dT%H%M%SZ` format.
        :param scope: The scope to use in the signature. See `_scope` for more info.
        :param payload: Optional payload to sign. If not provided, the payload will
        be generated from the request body.
        """
        canonical_request = await self.canonical_request(
            http_request=http_request,
            formatted_headers=formatted_headers,
            signed_headers=signed_headers,
            signing_properties=signing_properties,
            payload=payload,
        )
        string_to_sign = self.string_to_sign(
            canonical_request=canonical_request, date=date, scope=scope
        )
        return self._signature(
            string_to_sign, date, secret_access_key, signing_properties
        )

    async def canonical_request(
        self,
        *,
        http_request: HTTPRequestInterface,
        formatted_headers: dict[str, str],
        signed_headers: str,
        signing_properties: SigV4SigningProperties,
        payload: str | None = None,
    ) -> str:
        """Generate the canonical request string.

        This is a string comprised of several components separated by newlines in the
        following format:

        <HTTPMethod>\n <CanonicalURI>\n <CanonicalQueryString>\n <CanonicalHeaders>\n
        <SignedHeaders>\n <HashedPayload>

        :param http_request: The request to sign. It contains most of the components
        that are used to generate the canonical request.
        :param formatted_headers: The formatted header keys and values to sign.
        :param signed_headers: The semicolon-delimited header keys to sign.
        :param signing_properties: The signing properties to use in signing.
        :param payload: Optional payload to sign. If not provided, the payload will be
        generated from the request body.
        """
        cr = f"{http_request.method.upper()}\n"
        path = http_request.destination.path or "/"
        quoted_path = quote(remove_dot_segments(path, True), safe="/%")
        cr += f"{quoted_path}\n"
        cr += f"{self._canonical_query_string(http_request.destination)}\n"
        cr += f"{self._canonical_headers(formatted_headers)}\n"
        cr += f"{signed_headers}\n"
        if payload is None:
            cr += await self._payload(http_request, signing_properties)
        else:
            cr += payload
        return cr

    def _canonical_query_string(self, url: interfaces.URI) -> str:
        """Specifies the URI-encoded query string parameters.

        After encoding, the parameters are sorted in alphabetical order by key then
        value.
        """
        if not (query := url.query):
            return ""

        query_params = parse_qsl(query)
        # URI encode all characters including `/` and `=`
        query_parts = [
            (quote(key, safe=""), quote(value, safe="")) for key, value in query_params
        ]
        # Unfortunately, keys and values must be sorted separately and only
        # after they have been encoded.
        return "&".join(f"{key}={value}" for key, value in sorted(query_parts))

    def _canonical_headers(self, headers: dict[str, str]) -> str:
        """Format headers as a newline delimited string.

        Keys must be lower case and values must be trimmed.
        """
        # canonical headers should contain a trailing newline character `\n`
        return "".join(f"{key}:{self._trim(value)}\n" for key, value in headers.items())

    def _trim(self, value: str) -> str:
        """Remove excess whitespace before and after value then convert sequential
        spaces to a single space."""
        return " ".join(value.split())

    async def _payload(
        self,
        http_request: HTTPRequestInterface,
        signing_properties: SigV4SigningProperties,
    ) -> str:
        """Generate the value for the `X-Amz-Content-SHA256` header."""
        # TODO: Add _is_streaming_checksum_payload after checksum implementation is
        # complete

        # TODO: Need to add configuration in `signing_properties` to not sign large
        # request bodies because of performance issues. Exact size limit TBD.
        if not self._should_sha256_sign_payload(http_request, signing_properties):
            return UNSIGNED_PAYLOAD

        warnings.warn(
            "Payload signing is enabled. This may cause "
            "performance issues for large request bodies."
        )
        checksum = sha256()
        buffer = []
        async for chunk in self._read_request_body(http_request):
            checksum.update(chunk)
            buffer.append(chunk)
        # reset request body iterable to be read again later
        http_request.body = async_list(buffer)
        return checksum.hexdigest()

    def _is_streaming_checksum_payload(
        self, signing_properties: SigV4SigningProperties
    ) -> bool:
        # TODO: Implement this after checksum implementation is complete
        raise NotImplementedError()

    def _should_sha256_sign_payload(
        self,
        http_request: HTTPRequestInterface,
        signing_properties: SigV4SigningProperties,
    ) -> bool:
        # All insecure connections should be signed
        if http_request.destination.scheme != "https":
            return True

        return signing_properties.get("payload_signing_enabled", True)

    async def _read_request_body(
        self, http_request: HTTPRequestInterface
    ) -> AsyncGenerator[bytes, None]:
        """Read the request body into smaller chunks."""
        body = http_request.body
        async for chunk in body:
            stream = BytesIO(chunk)
            while True:
                # Create smaller chunks in case the chunk is too large
                if not (sub_chunk := stream.read(PAYLOAD_BUFFER)):
                    break
                yield sub_chunk

    def string_to_sign(self, *, canonical_request: str, date: str, scope: str) -> str:
        """The string to sign.

        It is a concatenation of the following strings:

        "AWS4-HMAC-SHA256" + "\n" + timeStampISO8601Format + "\n" + <Scope> + "\n" +
        Hex(SHA256Hash(<CanonicalRequest>))

        :param canonical_request: The canonical request string. For more information see
        `canonical_request` method.
        :param date: The date to use in the signature in `%Y%m%dT%H%M%SZ` format.
        :param scope: The scope to use in the signature. It takes the form of
        "<YYYYMMDD>/<AWS Region>/<AWS Service>/aws4_request".
        """
        return (
            "AWS4-HMAC-SHA256\n"
            f"{date}\n"
            f"{scope}\n"
            f"{sha256(canonical_request.encode()).hexdigest()}"
        )

    def _signature(
        self,
        string_to_sign: str,
        date: str,
        secret_key: str,
        signing_properties: SigV4SigningProperties,
    ) -> str:
        """Sign the string to sign.

        In SigV4, instead of using AWS access keys to sign a request, a signing key is
        created that is scoped to a specific region and service. The date, region,
        service and resulting signing key are individually hashed, then the composite
        hash is used to sign the string to sign.

        DateKey              = HMAC-SHA256("AWS4"+"<SecretAccessKey>", "<YYYYMMDD>")
        DateRegionKey        = HMAC-SHA256(<DateKey>, "<aws-region>")
        DateRegionServiceKey = HMAC-SHA256(<DateRegionKey>, "<aws-service>")
        SigningKey           = HMAC-SHA256(<DateRegionServiceKey>, "aws4_request")
        """
        k_date = self._hash(f"AWS4{secret_key}", date[0:8])
        k_region = self._hash(k_date, signing_properties["region"])
        k_service = self._hash(k_region, signing_properties["service"])
        k_signing = self._hash(k_service, "aws4_request")
        return self._hash(k_signing, string_to_sign).hex()

    def _hash(self, key: str | bytes, value: str) -> bytes:
        if isinstance(key, str):
            key = key.encode()
        return hmac.new(key, value.encode(), sha256).digest()

    def _authorization_header(
        self, signature: str, credential_scope: str, signed_headers: str
    ) -> Field:
        """Generate the `Authorization` header.

        This is a string formatted as:

        "AWS4-HMAC-SHA256" + ", " + <SignedHeaders> + ", " + <Signature>
        """
        auth_str = f"AWS4-HMAC-SHA256 {credential_scope}, "
        auth_str += f"SignedHeaders={signed_headers}, "
        auth_str += f"Signature={signature}"
        return Field(name="Authorization", values=[auth_str])
