# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import datetime
import hmac
import threading
from binascii import hexlify
from hashlib import sha256
from typing import TYPE_CHECKING

from ._http import AWSRequest
from ._program import run_program
from ._sigv4 import (
    DEFAULT_PORTS,
    EMPTY_SHA256_HASH,
    EVENT_STREAM_CONTENT_TYPE,
    EVENT_STREAM_HASH,
    HEADERS_EXCLUDED_FROM_SIGNING,
    SIGV4_TIMESTAMP_FORMAT,
    UNSIGNED_PAYLOAD,
    SigV4SignerBase,
    SigV4SigningProperties,
    credential_scope,
    hash_sync_body,
    signing_key,
)
from .exceptions import ResourceLifecycleError
from .interfaces.identity import AWSCredentialsIdentity as _AWSCredentialsIdentity

if TYPE_CHECKING:
    from .interfaces.events import EventHeaderEncoder, EventMessage

__all__ = (
    "DEFAULT_PORTS",
    "EMPTY_SHA256_HASH",
    "EVENT_STREAM_CONTENT_TYPE",
    "EVENT_STREAM_HASH",
    "HEADERS_EXCLUDED_FROM_SIGNING",
    "SIGV4_TIMESTAMP_FORMAT",
    "UNSIGNED_PAYLOAD",
    "EventSigner",
    "SigV4Signer",
    "SigV4SigningProperties",
)


class SigV4Signer(SigV4SignerBase):
    """Request signer for applying the AWS Signature Version 4 algorithm."""

    def sign(
        self,
        *,
        request: AWSRequest,
        identity: _AWSCredentialsIdentity,
        properties: SigV4SigningProperties,
    ) -> AWSRequest:
        """Generate and apply a SigV4 Signature to a copy of the supplied request.

        :param request: An AWSRequest to sign prior to sending to the service.
        :param identity: A set of credentials representing an AWS Identity or role
            capacity.
        :param properties: SigV4SigningProperties to define signing primitives such as
            the target service, region, and date.
        """
        return run_program(self._sign(request, identity, properties))

    def canonical_request(
        self, *, signing_properties: SigV4SigningProperties, request: AWSRequest
    ) -> str:
        """The canonical request is a standardized string laying out the components used
        in the SigV4 signing algorithm. This is useful to quickly compare inputs to find
        signature mismatches and unintended variances.

        The SigV4 specification defines the canonical request to be:
            <HTTPMethod>\\n
            <CanonicalURI>\\n
            <CanonicalQueryString>\\n
            <CanonicalHeaders>\\n
            <SignedHeaders>\\n
            <HashedPayload>

        :param signing_properties:
            SigV4SigningProperties to define signing primitives such as
            the target service, region, and date.
        :param request:
            An AWSRequest to use for generating a SigV4 signature.
        """
        return run_program(self._canonical_request(signing_properties, request))

    def _hash_body(self, request: AWSRequest) -> str:
        return hash_sync_body(request)


class EventSigner:
    """Signs the messages of an Amazon Event Stream, chaining each signature.

    Thread-safe, so one signer can serve a stream shared across threads or tasks.
    """

    def __init__(
        self,
        *,
        initial_signature: bytes,
        event_encoder_cls: type["EventHeaderEncoder"],
    ):
        self._prior_signature = initial_signature
        self._signing_lock = threading.Lock()
        self._event_encoder_cls = event_encoder_cls
        self._is_finalized = False

    def sign(
        self,
        *,
        event: "EventMessage",
        identity: _AWSCredentialsIdentity,
        properties: SigV4SigningProperties,
    ) -> "EventMessage":
        """Sign an Amazon Event Stream message, wrapping it as the payload."""
        return self._sign_payload(
            event=event,
            payload=event.encode(),
            identity=identity,
            properties=properties,
        )

    def sign_empty(
        self,
        *,
        event: "EventMessage",
        identity: _AWSCredentialsIdentity,
        properties: SigV4SigningProperties,
    ) -> "EventMessage":
        """Sign an Amazon Event Stream final empty message.

        The supplied ``event`` must have no headers and an empty payload.
        Calling ``sign`` with an empty event message is not equivalent because
        ``sign`` wraps the encoded event message as the payload.

        The returned message contains ``:date`` and ``:chunk-signature``
        headers and advances the running signature chain. After this method
        returns, the signer cannot sign additional event stream messages.
        """
        if event.headers or event.payload:
            raise ValueError(
                "sign_empty requires an event with no headers and an empty payload."
            )

        return self._sign_payload(
            event=event,
            payload=b"",
            identity=identity,
            properties=properties,
            is_final=True,
        )

    def _sign_payload(
        self,
        *,
        event: "EventMessage",
        payload: bytes,
        identity: _AWSCredentialsIdentity,
        properties: SigV4SigningProperties,
        is_final: bool = False,
    ) -> "EventMessage":
        with self._signing_lock:
            if self._is_finalized:
                raise ResourceLifecycleError(
                    "Cannot sign event stream messages after the final empty event "
                    "has been signed."
                )

            new_signing_properties = SigV4SigningProperties(**properties)
            # TODO: If date is in properties, parse a datetime from it.
            date_obj = datetime.datetime.now(datetime.UTC)
            if "date" not in new_signing_properties:
                new_signing_properties["date"] = date_obj.strftime(
                    SIGV4_TIMESTAMP_FORMAT
                )

            timestamp = new_signing_properties["date"]
            headers: dict[str, str | bytes | datetime.datetime] = {":date": date_obj}
            encoder = self._event_encoder_cls()
            encoder.encode_headers(headers)
            encoded_headers = encoder.get_result()

            string_to_sign = (
                "AWS4-HMAC-SHA256-PAYLOAD\n"
                f"{timestamp}\n"
                f"{credential_scope(new_signing_properties)}\n"
                f"{self._prior_signature.decode('utf-8')}\n"
                f"{sha256(encoded_headers).hexdigest()}\n"
                f"{sha256(payload).hexdigest()}"
            )
            event_signature = hmac.new(
                signing_key(identity.secret_access_key, new_signing_properties),
                string_to_sign.encode("utf-8"),
                sha256,
            ).digest()
            headers[":chunk-signature"] = event_signature

            event.headers = headers
            event.payload = payload

            self._prior_signature = hexlify(event_signature)
            if is_final:
                self._is_finalized = True

        return event
