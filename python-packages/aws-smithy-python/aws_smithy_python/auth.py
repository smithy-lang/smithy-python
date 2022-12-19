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

from io import BytesIO
from typing import Any

from awscrt import auth as awscrt_auth
from awscrt import http as awscrt_http
from smithy_python._private.auth import HttpSigner
from smithy_python.exceptions import SmithyIdentityException
from smithy_python.interfaces import http as http_interface
from smithy_python.interfaces import identity as identity_interface
from smithy_python.utils import host_from_url

from aws_smithy_python.identity import AwsCredentialIdentity

UNSIGNED_PAYLOAD: str = "UNSIGNED-PAYLOAD"
STREAMING_UNSIGNED_PAYLOAD_TRAILER: str = "STREAMING-UNSIGNED-PAYLOAD-TRAILER"
SIGNED_HEADERS_BLACKLIST: list[str] = [
    "expect",
    "user-agent",
    "x-amzn-trace-id",
]
PRESIGNED_HEADERS_BLACKLIST: list[str] = [
    "Authorization",
    "X-Amz-Date",
    "X-Amz-Content-SHA256",
    "X-Amz-Security-Token",
]
DEFAULT_EXPIRES: int = 3600


class AwsSigner(HttpSigner):
    """A base class for signing AWS requests."""

    SIGNATURE_TYPE: awscrt_auth.AwsSignatureType
    ALGORITHM: awscrt_auth.AwsSigningAlgorithm
    USE_DOUBLE_URI_ENCODE: bool
    SHOULD_NORMALIZE_URI_PATH: bool
    SHOULD_GET_EXISTING_SHA256: bool
    SHOULD_EXPIRE: bool

    def get_credentials_provider(
        self, identity: AwsCredentialIdentity
    ) -> awscrt_auth.AwsCredentialsProvider:
        return awscrt_auth.AwsCredentialsProvider.new_static(
            access_key_id=identity.access_key_id,
            secret_access_key=identity.secret_key_id,
            session_token=identity.session_token,
        )

    def sign(
        self,
        http_request: http_interface.Request,
        identity: identity_interface.Identity,
        signing_properties: dict[str, Any],
    ) -> http_interface.Request:

        if not isinstance(identity, AwsCredentialIdentity):
            raise SmithyIdentityException(
                "Invalid identity type. Must be AwsCredentialIdentity."
            )

        if "region" not in signing_properties or "service" not in signing_properties:
            raise SmithyIdentityException(
                "Must provide region and service in signing properties."
            )

        existing_sha256 = self._get_existing_sha256(http_request)
        credentials_provider = self.get_credentials_provider(identity)
        self._modify_request_before_signing(http_request)

        # the unsigned payload constants are of type str but explicit_payload
        # can be None as well. this declaration allows the block to comply
        # with mypy type checking
        explicit_payload: None | str
        if self._is_streaming_checksum_payload(signing_properties):
            explicit_payload = STREAMING_UNSIGNED_PAYLOAD_TRAILER
        elif self._should_sha256_sign_payload(signing_properties, http_request):
            explicit_payload = existing_sha256
        else:
            explicit_payload = UNSIGNED_PAYLOAD

        if self._should_add_content_sha256_header(explicit_payload):
            body_header = awscrt_auth.AwsSignedBodyHeaderType.X_AMZ_CONTENT_SHA_256
        else:
            body_header = awscrt_auth.AwsSignedBodyHeaderType.NONE

        if self.SHOULD_EXPIRE:
            expiration_in_seconds = signing_properties.get(
                "expires_in", DEFAULT_EXPIRES
            )
        else:
            expiration_in_seconds = None

        signing_config = awscrt_auth.AwsSigningConfig(
            algorithm=self.ALGORITHM,
            signature_type=self.SIGNATURE_TYPE,
            credentials_provider=credentials_provider,
            region=signing_properties["region"],
            service=signing_properties["service"],
            should_sign_header=self._should_sign_header,
            use_double_uri_encode=self.USE_DOUBLE_URI_ENCODE,
            should_normalize_uri_path=self.SHOULD_NORMALIZE_URI_PATH,
            signed_body_value=explicit_payload,
            signed_body_header_type=body_header,
            expiration_in_seconds=expiration_in_seconds,
        )
        crt_request = self._crt_request_from_smithy_request(http_request)
        future = awscrt_auth.aws_sign_request(crt_request, signing_config)
        future.result()
        self._apply_signing_changes(http_request, crt_request)
        return http_request

    def _modify_request_before_signing(self, request: http_interface.Request) -> None:
        request.headers = [
            (key, value)
            for key, value in request.headers
            if key not in PRESIGNED_HEADERS_BLACKLIST
        ]
        if not self._get_header(request.headers, "host"):
            request.headers.append(("host", host_from_url(request.url)))

    def _crt_request_from_smithy_request(
        self, request: http_interface.Request
    ) -> awscrt_http.HttpRequest:
        crt_path = request.url.path if request.url.path else "/"
        if request.url.query:
            crt_path += f"?{request.url.query}"

        crt_headers = awscrt_http.HttpHeaders(request.headers)

        if request.body is None or isinstance(request.body, BytesIO):
            crt_body_stream = request.body
        else:
            crt_body_stream = BytesIO(request.body)

        return awscrt_http.HttpRequest(
            method=request.method,
            path=crt_path,
            headers=crt_headers,
            body_stream=crt_body_stream,
        )

    def _get_header(self, headers: http_interface.HeadersList, name: str) -> str | None:
        for key, value in headers:
            if key.lower() == name.lower():
                return value
        return None

    def _is_streaming_checksum_payload(
        self, signing_properties: dict[str, Any]
    ) -> bool:
        checksum = signing_properties.get("checksum", {})
        algorithm = checksum.get("request_algorithm")
        return isinstance(algorithm, dict) and algorithm.get("in") == "trailer"

    def _get_existing_sha256(self, request: http_interface.Request) -> str | None:
        if self.SHOULD_GET_EXISTING_SHA256:
            return self._get_header(request.headers, "X-Amz-Content-SHA256")
        return None

    def _should_sign_header(self, name: str, **kwargs: dict[str, Any]) -> bool:
        return name.lower() not in SIGNED_HEADERS_BLACKLIST

    def _apply_signing_changes(
        self, aws_request: http_interface.Request, crt_request: awscrt_http.HttpRequest
    ) -> None:
        aws_request.headers = list(crt_request.headers)

    def _should_sha256_sign_payload(
        self, signing_properties: dict[str, Any], request: http_interface.Request
    ) -> bool:
        raise NotImplementedError()

    def _should_add_content_sha256_header(self, explicit_payload: str | None) -> bool:
        raise NotImplementedError()


class AwsSigV4Signer(AwsSigner):
    """AWS request signer implementing the signature version 4 algorithm."""

    SIGNATURE_TYPE: awscrt_auth.AwsSignatureType = (
        awscrt_auth.AwsSignatureType.HTTP_REQUEST_HEADERS
    )
    ALGORITHM: awscrt_auth.AwsSigningAlgorithm = awscrt_auth.AwsSigningAlgorithm.V4
    USE_DOUBLE_URI_ENCODE: bool = True
    SHOULD_NORMALIZE_URI_PATH: bool = True
    SHOULD_GET_EXISTING_SHA256: bool = True
    SHOULD_EXPIRE: bool = False

    def _should_sha256_sign_payload(
        self, signing_properties: dict[str, Any], request: http_interface.Request
    ) -> bool:
        # Payloads will always be signed over insecure connections.
        if not request.url.build().startswith("https"):
            return True

        return signing_properties.get("payload_signing_enabled", True)

    def _should_add_content_sha256_header(self, explicit_payload: str | None) -> bool:
        return explicit_payload is not None
