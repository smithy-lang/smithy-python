# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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
from datetime import datetime
from hashlib import sha256
from typing import Callable, Literal, NotRequired
from urllib.parse import parse_qsl, quote

from smithy_python import interfaces
from smithy_python._private import Field, Fields
from smithy_python._private.auth import HTTPSigner
from smithy_python._private.http import HTTPRequest
from smithy_python.exceptions import SmithyIdentityException
from smithy_python.interfaces.auth import SigningProperties
from smithy_python.interfaces.http import HTTPRequest as HTTPRequestInterface
from smithy_python.utils import remove_dot_segments

from aws_smithy_python.identity import AWSCredentialIdentity

REQUIRED_SIGNING_PROPERTIES: tuple[str, str] = ("region", "service")
UNSIGNED_PAYLOAD: Literal["UNSIGNED-PAYLOAD"] = "UNSIGNED-PAYLOAD"
STREAMING_UNSIGNED_PAYLOAD_TRAILER: Literal[
    "STREAMING-UNSIGNED-PAYLOAD-TRAILER"
] = "STREAMING-UNSIGNED-PAYLOAD-TRAILER"
SIGV4_TIMESTAMP_FORMAT: Literal["%Y%m%dT%H%M%SZ"] = "%Y%m%dT%H%M%SZ"
HEADERS_EXCLUDED_FROM_SIGNING: tuple[str, str, str, str, str] = (
    "authorization",
    "expect",
    "user-agent",
    "x-amz-content-sha256",
    "x-amzn-trace-id",
)
DISALLOWED_USER_PROVIDED_HEADERS: tuple[
    str, str, str, str, str, str, str
] = HEADERS_EXCLUDED_FROM_SIGNING + ("x-amz-date", "x-amz-security-token")

DEFAULT_EXPIRES: int = 3600
PAYLOAD_BUFFER: int = 1024**2
EMPTY_SHA256_HASH: Literal[
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
] = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class SigV4SigningProperties(SigningProperties):
    region: str
    service: str
    expires: NotRequired[int]
    payload_signing_enabled: NotRequired[bool]
    checksum: NotRequired[dict[str, dict[str, str]]]


class SigV4Signer(HTTPSigner[AWSCredentialIdentity, SigV4SigningProperties]):
    """Sign requests using the AWS Signature Version 4 algorithm."""

    def __init__(
        self, get_current_time: Callable[[], datetime] = datetime.utcnow
    ) -> None:
        """Initialize the SigV4Signer.

        :param get_current_time: A callable to get the current time when signing the
        request. Defaults to the current time in the UTC time zone. Any timezone
        information that may be present will be ignored and replaced with UTC.
        """
        self._get_current_time = get_current_time

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
        :param signing_properties: The properties to use for signing. Can indicate
        whether or not to sign the payload, the type of payload, region, service,
        and expiration where applicable.
        """
        (
            new_request,
            formatted_headers,
            signed_headers,
            date,
            scope,
        ) = await self._get_signature_args(http_request, identity, signing_properties)
        signature = await self._generate_signature(
            new_request,
            formatted_headers,
            signed_headers,
            identity.secret_key_id,
            signing_properties,
            date,
            scope,
        )
        credential_scope = f"Credential={identity.access_key_id}/{scope}"
        auth_header = self._authorization_header(
            signature, credential_scope, signed_headers
        )
        new_request.fields.set_field(auth_header)
        return new_request

    async def generate_presigned_url(
        self,
        http_request: HTTPRequestInterface,
        identity: AWSCredentialIdentity,
        signing_properties: SigV4SigningProperties,
    ) -> str:
        """Sign a request using query parameters.

        Specifications can be found at:
        https://docs.aws.amazon.com/general/latest/gr/create-signed-request.html

        :param http_request: The request to sign.
        :param identity: The identity to use for signing. Contains authentication
        credentials.
        :param signing_properties: The properties to use for signing. Can indicate
        whether or not to sign the payload, the type of payload, region, service,
        and expiration where applicable.
        """
        if not identity.session_token:
            raise SmithyIdentityException(
                "A session token is required for presigned URLs."
            )
        (
            new_request,
            formatted_headers,
            signed_headers,
            date,
            scope,
        ) = await self._get_signature_args(http_request, identity, signing_properties)
        expires = signing_properties.get("expires", DEFAULT_EXPIRES)
        credential_scope = f"{identity.access_key_id}/{scope}"
        # All query parameters besides `X-Amz-Signature` must be included in
        # the canonical request and string to sign.
        url_query = self._generate_url_query_params(
            new_request,
            date,
            credential_scope,
            expires,
            signed_headers,
        )
        # add the query params before signing
        new_request.destination.query = url_query
        signature = await self._generate_signature(
            new_request,
            formatted_headers,
            signed_headers,
            identity.secret_key_id,
            signing_properties,
            date,
            scope,
            True,
        )
        new_request.destination.query += f"&X-Amz-Signature={signature}"
        return new_request.destination.build()

    async def _get_signature_args(
        self,
        http_request: HTTPRequestInterface,
        identity: AWSCredentialIdentity,
        signing_properties: SigV4SigningProperties,
    ) -> tuple[HTTPRequest, dict[str, str], str, str, str]:
        """Get the arguments needed to generate a signature.

        Check that the identity and signing properties are valid, generate the headers
        to add to the request, create a new request with the headers added, format the
        headers for signing, and generate the scope.
        """

        self._validate_identity_and_signing_properties(identity, signing_properties)
        headers_to_add = self._headers_to_add(identity)
        new_request = await self._generate_new_request_before_signing(
            http_request, headers_to_add
        )
        formatted_headers = self._format_headers_for_signing(new_request)
        # Signed headers are comprised of just the header keys delimited by
        # a semicolon.
        signed_headers = ";".join(formatted_headers)
        date = new_request.fields.get_field("X-Amz-Date").as_string()
        scope = self._scope(date, signing_properties)
        return new_request, formatted_headers, signed_headers, date, scope

    def _validate_identity_and_signing_properties(
        self,
        identity: AWSCredentialIdentity,
        signing_properties: SigV4SigningProperties,
    ) -> None:
        if not all(key in signing_properties for key in REQUIRED_SIGNING_PROPERTIES):
            raise SmithyIdentityException(
                f"The signing properties {', '.join(REQUIRED_SIGNING_PROPERTIES)} are "
                f"required for SigV4 auth, but found: {', '.join(signing_properties)}."
            )
        if not isinstance(identity, AWSCredentialIdentity):
            raise SmithyIdentityException(
                "Invalid identity type. Expected AWSCredentialIdentity, "
                f"but received {type(identity)}."
            )

    def _headers_to_add(self, identity: AWSCredentialIdentity) -> Fields:
        headers_to_add = Fields(
            [
                Field(
                    name="X-Amz-Date",
                    values=[self._get_current_time().strftime(SIGV4_TIMESTAMP_FORMAT)],
                )
            ]
        )
        if identity.session_token:
            headers_to_add.set_field(
                Field(name="X-Amz-Security-Token", values=[identity.session_token])
            )
        return headers_to_add

    async def _generate_new_request_before_signing(
        self,
        http_request: HTTPRequestInterface,
        headers_to_add: Fields,
    ) -> HTTPRequest:
        """Generate a new request with only allowed headers.

        Remove headers that are excluded from SigV4 signature computation. Adds
        additional headers if provided.
        """
        fields = http_request.fields
        to_delete = []
        for field in fields:
            if field.name.lower() in DISALLOWED_USER_PROVIDED_HEADERS:
                # cannot modify `OrderedDict` while iterating over it`
                to_delete.append(field.name)
        for name in to_delete:
            fields.remove_field(name)
        fields.extend(headers_to_add)
        return HTTPRequest(
            method=http_request.method,
            destination=http_request.destination,
            fields=fields,
            body=http_request.body,
        )

    async def _payload(
        self,
        http_request: HTTPRequestInterface,
        signing_properties: SigV4SigningProperties,
        for_url_presigning: bool = False,
    ) -> str:
        """Generate the value for the `X-Amz-Content-SHA256` header."""
        if self._is_streaming_checksum_payload(signing_properties):
            return STREAMING_UNSIGNED_PAYLOAD_TRAILER
        elif (
            not self._should_sha256_sign_payload(http_request, signing_properties)
            or for_url_presigning  # noqa: W503
        ):
            return UNSIGNED_PAYLOAD

        if request_body := await http_request.consume_body():
            return sha256(request_body).hexdigest()

        return EMPTY_SHA256_HASH

    def _is_streaming_checksum_payload(
        self, signing_properties: SigV4SigningProperties
    ) -> bool:
        checksum = signing_properties.get("checksum", {})
        algorithm = checksum.get("request_algorithm", {})
        return algorithm.get("in") == "trailer"

    def _should_sha256_sign_payload(
        self,
        http_request: HTTPRequestInterface,
        signing_properties: SigV4SigningProperties,
    ) -> bool:
        # All insecure connections should be signed
        if http_request.destination.scheme != "https":
            return True

        return signing_properties.get("payload_signing_enabled", True)

    def _format_headers_for_signing(
        self, http_request: HTTPRequestInterface
    ) -> dict[str, str]:
        """Format headers for signing http requests.

        Only use headers that aren't excluded, add `host` header if not present and
        return as a sorted dictionary. Both canonical and signed headers are expected in
        alphabetical order.
        """
        formatted_headers = {}
        for field in http_request.fields:
            l_key = field.name.lower()
            if l_key not in HEADERS_EXCLUDED_FROM_SIGNING:
                value = ",".join(field.values)
                formatted_headers[l_key] = value
        if "host" not in formatted_headers:
            formatted_headers["host"] = http_request.destination.netloc
        return dict(sorted(formatted_headers.items()))

    def _scope(self, date: str, signing_properties: SigV4SigningProperties) -> str:
        """Binds the signature to a specific date, AWS region, and service.

        It takes the following form:

        <YYYYMMDD>/<AWS Region>/<AWS Service>/aws4_request
        """
        return (
            f"{date[0:8]}/{signing_properties['region']}/"
            f"{signing_properties['service']}/aws4_request"
        )

    def _generate_url_query_params(
        self,
        http_request: HTTPRequestInterface,
        date: str,
        credential_scope: str,
        expires: int,
        signed_headers: str,
    ) -> str:
        """Add all required query parameters to the request URI in alphabetical order by
        key."""
        if (query := http_request.destination.query) is not None and len(query) > 0:
            query += "&"
        else:
            query = ""
        query += "X-Amz-Algorithm=AWS4-HMAC-SHA256&"
        # URI encode forward slashes
        query += f"X-Amz-Credential={quote(credential_scope, safe='')}&"
        query += f"X-Amz-Date={date}&"
        query += f"X-Amz-Expires={expires}&"
        session_token = http_request.fields.get_field(
            "X-Amz-Security-Token"
        ).as_string()
        query += f"X-Amz-Security-Token={quote(session_token, safe='')}&"
        query += f"X-Amz-SignedHeaders={signed_headers}"
        return query

    async def _generate_signature(
        self,
        http_request: HTTPRequestInterface,
        formatted_headers: dict[str, str],
        signed_headers: str,
        secret_key_id: str,
        signing_properties: SigV4SigningProperties,
        date: str,
        scope: str,
        for_presigning: bool = False,
    ) -> str:
        """Generate the signature for a request.

        :param http_request: The request to sign.
        :param formatted_headers: The formatted header keys and values to sign.
        :param signed_headers: The semicolon-delimited header keys to sign.
        :param secret_key_id: The secret key ID to use in the signature.
        :param signing_properties: The signing properties to use in signing. Can
        indicate whether or not to sign the payload, the type of payload, region,
        service, and expiration where applicable.
        :param date: The date to use in the signature in `%Y%m%dT%H%M%SZ` format.
        :param scope: The scope to use in the signature. See `_scope` for more info.
        :param for_presigning: Whether or not the signature is being generated for URL
        presigning.
        """
        canonical_request = await self._canonical_request(
            http_request,
            formatted_headers,
            signed_headers,
            signing_properties,
            for_presigning,
        )
        string_to_sign = self._string_to_sign(canonical_request, date, scope)
        print(string_to_sign)
        return self._signature(string_to_sign, date, secret_key_id, signing_properties)

    async def _canonical_request(
        self,
        http_request: HTTPRequestInterface,
        formatted_headers: dict[str, str],
        signed_headers: str,
        signing_properties: SigV4SigningProperties,
        for_presigning: bool = False,
    ) -> str:
        """Generate the canonical request string.

        This is a string comprised of several components separated by newlines.
        This is its format:

        <HTTPMethod>\n <CanonicalURI>\n <CanonicalQueryString>\n <CanonicalHeaders>\n
        <SignedHeaders>\n <HashedPayload>
        """
        cr = f"{http_request.method.upper()}\n"
        path = http_request.destination.path or "/"
        quoted_path = quote(remove_dot_segments(path), safe="/%")
        cr += f"{quoted_path}\n"
        cr += f"{self._canonical_query_string(http_request.destination)}\n"
        cr += f"{self._canonical_headers(formatted_headers)}\n"
        cr += f"{signed_headers}\n"
        try:
            cr += http_request.fields.get_field("X-Amz-Content-SHA256").as_string()
        except KeyError:
            cr += await self._payload(http_request, signing_properties, for_presigning)
        return cr

    def _canonical_query_string(self, url: interfaces.URI) -> str:
        """Specifies the URI-encoded query string parameters.

        After encoding, the parameters are sorted in alphabetical order by key name then
        value.
        """
        if not (query := url.query):
            return ""

        query_parts = []
        query_params = parse_qsl(query)
        for key, value in query_params:
            # URI encode all characters including `/` and `=`
            query_parts.append((quote(key, safe=""), quote(value, safe="")))
        # Unfortunately, keys and values must be sorted separately and only
        # after they have been encoded.
        return "&".join([f"{key}={value}" for key, value in sorted(query_parts)])

    def _canonical_headers(self, headers: dict[str, str]) -> str:
        """Format headers as a newline delimited string.

        Keys must be lower case and values must be trimmed.
        """
        # canonical headers should contain a trailing newline character `\n`
        return "".join(f"{key}:{self.trim(value)}\n" for key, value in headers.items())

    def trim(self, value: str) -> str:
        """Remove excess whitespace before and after value then convert sequential
        spaces to a single space."""
        return " ".join(value.split())

    def _string_to_sign(self, canonical_request: str, date: str, scope: str) -> str:
        """The string that will ultimately be passed to the `signature` function for
        signing.

        It is a concatenation of the following strings:

        "AWS4-HMAC-SHA256" + "\n" + timeStampISO8601Format + "\n" + <Scope> + "\n" +
        Hex(SHA256Hash(<CanonicalRequest>))
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

        In SigV4, instead of using AWS access keys to sign a
        request, a signing key is created that is scoped to a specific region and
        service. The date, region, service and resulting signing key are individually
        hashed, then the composite hash is used to sign the string to sign.

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

        "AWS4-HMAC-SHA256" + "," + <SignedHeaders> + "," + <Signature>
        """
        auth_str = f"AWS4-HMAC-SHA256 {credential_scope}, "
        auth_str += f"SignedHeaders={signed_headers}, "
        auth_str += f"Signature={signature}"
        return Field(name="Authorization", values=[auth_str])
