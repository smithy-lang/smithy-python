# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import datetime
import hmac
from binascii import hexlify
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

from .eventstream import (
    HEADER_SERIALIZATION_VALUE,
    HEADERS_SERIALIZATION_DICT,
    EventStreamMessageSerializer,
)


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


@dataclass
class Credentials:
    access_key_id: str
    secret_access_key: str
    session_token: str | None


class EventSigner:
    _ISO8601_TIMESTAMP_FMT = "%Y%m%dT%H%M%SZ"
    _NOW_TYPE = Optional[Callable[[], datetime.datetime]]

    def __init__(
        self,
        signing_name: str,
        region: str,
        utc_now: _NOW_TYPE = None,
    ):
        self.signing_name = signing_name
        self.region = region
        self.serializer = EventStreamMessageSerializer()
        if utc_now is None:
            utc_now = _utc_now
        self._utc_now = utc_now

    def sign(
        self, payload: bytes, prior_signature: bytes, credentials: Credentials
    ) -> HEADERS_SERIALIZATION_DICT:
        now = self._utc_now()

        # pyright gets confused for some reason if we use
        # HEADERS_SERIALIZATION_DICT here. It gets convinced that the dict
        # can only have datetime values.
        headers: dict[str, HEADER_SERIALIZATION_VALUE] = {
            ":date": now,
        }

        timestamp = now.strftime(self._ISO8601_TIMESTAMP_FMT)
        string_to_sign = self._string_to_sign(
            timestamp, headers, payload, prior_signature
        )
        event_signature = self._sign_event(timestamp, string_to_sign, credentials)
        headers[":chunk-signature"] = event_signature
        return headers

    def _keypath(self, timestamp: str) -> str:
        parts = [
            timestamp[:8],  # Only using the YYYYMMDD
            self.region,
            self.signing_name,
            "aws4_request",
        ]
        return "/".join(parts)

    def _string_to_sign(
        self,
        timestamp: str,
        headers: HEADERS_SERIALIZATION_DICT,
        payload: bytes,
        prior_signature: bytes,
    ) -> str:
        encoded_headers = self.serializer.encode_headers(headers)
        parts = [
            "AWS4-HMAC-SHA256-PAYLOAD",
            timestamp,
            self._keypath(timestamp),
            hexlify(prior_signature).decode("utf-8"),
            sha256(encoded_headers).hexdigest(),
            sha256(payload).hexdigest(),
        ]
        return "\n".join(parts)

    def _hmac(self, key: bytes, msg: bytes) -> bytes:
        return hmac.new(key, msg, sha256).digest()

    def _sign_event(
        self, timestamp: str, string_to_sign: str, credentials: Credentials
    ) -> bytes:
        key = credentials.secret_access_key.encode("utf-8")
        today = timestamp[:8].encode("utf-8")  # Only using the YYYYMMDD
        k_date = self._hmac(b"AWS4" + key, today)
        k_region = self._hmac(k_date, self.region.encode("utf-8"))
        k_service = self._hmac(k_region, self.signing_name.encode("utf-8"))
        k_signing = self._hmac(k_service, b"aws4_request")
        return self._hmac(k_signing, string_to_sign.encode("utf-8"))
