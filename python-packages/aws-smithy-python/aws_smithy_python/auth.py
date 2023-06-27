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
from datetime import datetime
from hashlib import sha256
from typing import Required, TypedDict
from urllib.parse import parse_qsl, quote

from smithy_python import interfaces
from smithy_python._private import URI, Field
from smithy_python._private.auth import HTTPSigner
from smithy_python._private.http import HTTPRequest
from smithy_python.async_utils import async_list
from smithy_python.exceptions import SmithyHTTPException, SmithyIdentityException
from smithy_python.interfaces.auth import SigningProperties
from smithy_python.interfaces.blobs import AsyncBytesReader
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
EMPTY_SHA256_HASH: str = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)
DEFAULT_PORTS: dict[str, int] = {"https": 443, "http": 80}


class SigV4SigningProperties(SigningProperties, total=False):
    region: Required[str]
    service: Required[str]
    date: str
    expires: int
    payload_signing_enabled: bool


class SignatureKwargs(TypedDict):
    http_request: HTTPRequest
    signed_headers: str
    scope: str


class _TempDate(str):
    """Sentinel value for temporary date."""

    def __new__(cls, content: str) -> "_TempDate":
        return super().__new__(cls, content)


class SigV4Signer(
    HTTPSigner[HTTPRequest, AWSCredentialIdentity, SigV4SigningProperties]
):
    """Sign requests using the AWS Signature Version 4 algorithm."""

    async def sign(
        self,
        *,
        http_request: HTTPRequest,
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
        date = signing_properties.get("date")
        if date is None or isinstance(date, _TempDate):
            # Override ephemeral _TempDates from previous runs to
            # ensure we're always signing with a current date.
            signing_properties["date"] = _TempDate(
                datetime.utcnow().strftime(SIGV4_TIMESTAMP_FORMAT)
            )
        signature_kwargs = self._get_signature_kwargs(
            http_request=http_request,
            identity=identity,
            signing_properties=signing_properties,
        )
        signature = await self._generate_signature(
            http_request=signature_kwargs["http_request"],
            signing_properties=signing_properties,
            secret_access_key=identity.secret_access_key,
        )
        credential_scope = (
            f"Credential={identity.access_key_id}/{signature_kwargs['scope']}"
        )
        auth_header = self._authorization_header(
            credential_scope=credential_scope,
            signed_headers=signature_kwargs["signed_headers"],
            signature=signature,
        )
        new_request = signature_kwargs["http_request"]
        new_request.fields.set_field(field=auth_header)
        return new_request

    def _get_signature_kwargs(
        self,
        http_request: HTTPRequest,
        identity: AWSCredentialIdentity,
        signing_properties: SigV4SigningProperties,
    ) -> SignatureKwargs:
        """Get the arguments needed to generate a signature.

        Check that the identity and signing properties are valid, generate the headers
        to add to the request, create a new request with the headers added, get the
        signed headers, and generate the scope.
        """
        self._validate_identity_and_signing_properties(
            identity=identity, signing_properties=signing_properties
        )
        new_request = self._generate_new_request(
            http_request=http_request,
            identity=identity,
            date=signing_properties["date"],
        )
        signed_headers = ";".join(
            self._format_headers_for_signing(http_request=new_request)
        )
        scope = self._scope(signing_properties=signing_properties)
        return {
            "http_request": new_request,
            "signed_headers": signed_headers,
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

    def _generate_new_request(
        self,
        http_request: HTTPRequest,
        identity: AWSCredentialIdentity,
        date: str,
    ) -> HTTPRequest:
        """Generate a new request.

        Inject the `X-Amz-Date` header and `X-Amz-Security-Token` header if the identity
        has a session token.
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

        return new_request

    def _format_headers_for_signing(self, http_request: HTTPRequest) -> dict[str, str]:
        """Format headers for signing.

        Ignore any headers that should not be signed, and add the host header if not
        already present.
        """
        fields = http_request.fields
        formatted_headers = {
            field.name.lower(): field.as_string(delimiter=",")
            for field in fields
            if field.name.lower() not in HEADERS_EXCLUDED_FROM_SIGNING
        }
        if "host" not in formatted_headers:
            uri = http_request.destination
            if uri.port is not None and DEFAULT_PORTS.get(uri.scheme) == uri.port:
                # remove port from netloc
                uri = self._generate_new_uri(uri=uri, params={"port": None})
            formatted_headers["host"] = uri.netloc
        return dict(sorted(formatted_headers.items()))

    def _generate_new_uri(
        self, uri: interfaces.URI, params: interfaces.URIParameters
    ) -> URI:
        """Generate a new URI with kwargs."""
        uri_dict = uri.to_dict()
        uri_dict.update(params)
        return URI(**uri_dict)

    def _scope(self, signing_properties: SigV4SigningProperties) -> str:
        """Binds the signature to a specific date, AWS region, and service in the
        following format:

        <YYYYMMDD>/<AWS Region>/<AWS Service>/aws4_request
        """
        return (
            f"{signing_properties['date'][0:8]}/{signing_properties['region']}/"
            f"{signing_properties['service']}/aws4_request"
        )

    async def _generate_signature(
        self,
        http_request: HTTPRequest,
        signing_properties: SigV4SigningProperties,
        secret_access_key: str,
    ) -> str:
        """Generate the signature for a request.

        :param http_request: The request to sign.
        :param signing_properties: The signing properties to use in signing.
        :param secret_access_key: The secret access key to use in the signature.
        """
        canonical_request = await self.canonical_request(
            http_request=http_request,
            signing_properties=signing_properties,
        )
        string_to_sign = self.string_to_sign(
            canonical_request=canonical_request, signing_properties=signing_properties
        )
        return self._signature(
            string_to_sign=string_to_sign,
            secret_key=secret_access_key,
            signing_properties=signing_properties,
        )

    async def canonical_request(
        self,
        *,
        http_request: HTTPRequest,
        signing_properties: SigV4SigningProperties,
    ) -> str:
        """Generate the canonical request string.

        :param http_request: The request to sign. It contains most of the
        components that are used to generate the canonical request.
        :param signing_properties: The signing properties to use in signing.
        """
        path = http_request.destination.path or "/"
        formatted_path = remove_dot_segments(path=path, remove_consecutive_slashes=True)
        quoted_path = quote(string=formatted_path, safe="/%")
        formatted_headers = self._format_headers_for_signing(http_request=http_request)
        payload = await self._payload(
            http_request=http_request, signing_properties=signing_properties
        )

        return (
            f"{http_request.method.upper()}\n"
            f"{quoted_path}\n"
            f"{self._canonical_query_string(uri=http_request.destination)}\n"
            f"{self._canonical_headers(headers=formatted_headers)}\n"
            f"{';'.join(formatted_headers)}\n"
            f"{payload}"
        )

    def _canonical_query_string(self, uri: interfaces.URI) -> str:
        """Specifies the URI-encoded query string parameters.

        After encoding, the parameters are sorted in alphabetical order by key then
        value.
        """
        if not uri.query:
            return ""

        query_params = parse_qsl(qs=uri.query)
        # URI encode all characters including `/` and `=`
        query_parts = [
            (quote(string=key, safe=""), quote(string=value, safe=""))
            for key, value in query_params
        ]
        # Keys and values must be sorted separately and only after they have
        # been encoded.
        return "&".join(f"{key}={value}" for key, value in sorted(query_parts))

    def _canonical_headers(self, headers: dict[str, str]) -> str:
        """Format headers as a newline delimited string.

        Keys must be lower case and values must be trimmed.
        """
        # canonical headers should contain a trailing newline character `\n`
        return "".join(
            f"{key}:{self._trim(value=value)}\n" for key, value in headers.items()
        )

    def _trim(self, value: str) -> str:
        """Trim a header value.

        Remove excess whitespace before and after value then convert sequential spaces
        to a single space.
        """
        return " ".join(value.split())

    async def _payload(
        self,
        http_request: HTTPRequest,
        signing_properties: SigV4SigningProperties,
    ) -> str:
        """Generate the value for the `X-Amz-Content-SHA256` header.

        If the body is seekable, reset the position after reading it. If not, read the
        body into a buffer and reset the body to the buffer.
        """
        # TODO: Add check for streaming checksum payload after checksum implementation
        # is complete

        # TODO: Need to add configuration in `signing_properties` to not sign large
        # request bodies because of performance issues. Exact size limit TBD.
        if not self._should_sha256_sign_payload(
            http_request=http_request, signing_properties=signing_properties
        ):
            return UNSIGNED_PAYLOAD

        warnings.warn(
            "Payload signing is enabled. This may cause "
            "performance issues for large request bodies."
        )
        checksum = sha256()
        body = http_request.body
        if hasattr(body, "seek") and hasattr(body, "tell"):
            position = body.tell()
            async for chunk in body:
                checksum.update(chunk)
            await body.seek(position)
        else:
            buffer = []
            async for chunk in body:
                buffer.append(chunk)
                checksum.update(chunk)
            http_request.body = AsyncBytesReader(data=async_list(lst=buffer))
        return checksum.hexdigest()

    def _should_sha256_sign_payload(
        self,
        http_request: HTTPRequest,
        signing_properties: SigV4SigningProperties,
    ) -> bool:
        # All insecure connections should be signed
        if http_request.destination.scheme != "https":
            return True

        return signing_properties.get("payload_signing_enabled", True)

    def string_to_sign(
        self, *, canonical_request: str, signing_properties: SigV4SigningProperties
    ) -> str:
        """The string to sign.

        :param canonical_request: The canonical request string. See
        `canonical_request` for more info.
        :signing_properties: The signing properties to use in signing.
        """
        date = signing_properties.get("date")
        if date is None:
            signing_properties["date"] = _TempDate(
                datetime.utcnow().strftime(SIGV4_TIMESTAMP_FORMAT)
            )
        return (
            "AWS4-HMAC-SHA256\n"
            f"{signing_properties['date']}\n"
            f"{self._scope(signing_properties=signing_properties)}\n"
            f"{sha256(canonical_request.encode()).hexdigest()}"
        )

    def _signature(
        self,
        string_to_sign: str,
        secret_key: str,
        signing_properties: SigV4SigningProperties,
    ) -> str:
        """Sign the string to sign.

        In SigV4, a signing key is created that is scoped to a specific region and
        service. The date, region, service and resulting signing key are individually
        hashed, then the composite hash is used to sign the string to sign.

        DateKey              = HMAC-SHA256("AWS4"+"<SecretAccessKey>", "<YYYYMMDD>")
        DateRegionKey        = HMAC-SHA256(<DateKey>, "<aws-region>")
        DateRegionServiceKey = HMAC-SHA256(<DateRegionKey>, "<aws-service>")
        SigningKey           = HMAC-SHA256(<DateRegionServiceKey>, "aws4_request")
        """
        k_date = self._hash(
            key=f"AWS4{secret_key}".encode(), value=signing_properties["date"][0:8]
        )
        k_region = self._hash(key=k_date, value=signing_properties["region"])
        k_service = self._hash(key=k_region, value=signing_properties["service"])
        k_signing = self._hash(key=k_service, value="aws4_request")
        return self._hash(key=k_signing, value=string_to_sign).hex()

    def _hash(self, key: bytes, value: str) -> bytes:
        return hmac.new(key=key, msg=value.encode(), digestmod=sha256).digest()

    def _authorization_header(
        self, credential_scope: str, signed_headers: str, signature: str
    ) -> Field:
        """Generate the `Authorization` header.

        This is a string formatted as:

        "AWS4-HMAC-SHA256" + ", " + <SignedHeaders> + ", " + <Signature>
        """
        auth_str = f"AWS4-HMAC-SHA256 {credential_scope}, "
        auth_str += f"SignedHeaders={signed_headers}, "
        auth_str += f"Signature={signature}"
        return Field(name="Authorization", values=[auth_str])
