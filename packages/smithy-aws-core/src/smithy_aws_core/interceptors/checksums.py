#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import io
import logging
from collections.abc import Callable
from copy import copy, deepcopy
from dataclasses import replace
from inspect import isawaitable, iscoroutinefunction
from typing import Any, Protocol

from aws_sdk_signers.signers import SigV4ChunkSigner
from smithy_core._model_naming import member_field_name
from smithy_core.auth import RESOLVED_IDENTITY
from smithy_core.client import AUTH_SCHEME, OPERATION
from smithy_core.exceptions import SmithyError
from smithy_core.interceptors import (
    InputContext,
    Interceptor,
    RequestContext,
    ResponseContext,
)
from smithy_core.interfaces import TypedProperties
from smithy_core.schemas import APIOperation, Schema
from smithy_core.shapes import ShapeType
from smithy_core.traits import HTTPHeaderTrait, StreamingTrait
from smithy_core.types import PropertyKey
from smithy_http import Field, HTTPResponse
from smithy_http.interfaces import HTTPRequest
from smithy_http.interfaces import HTTPResponse as HTTPResponseInterface

from .._aws_chunked import AwsChunkedReader, ChunkSigner
from .._private.checksums import (
    DEFAULT_ALGORITHM,
    SUPPORTED_ALGORITHMS,
    assert_checksums_installed,
    checksum_header,
    checksum_header_algorithm,
    create_checksum,
    decode_checksum,
    encode_digest,
    response_validation_order,
)
from ..business_metrics import AwsFeatureId, register_feature_id
from ..checksums import ChecksumStream, UnsupportedChecksumAlgorithmError
from ..identity.components import AWSCredentialsIdentity
from ..traits import HTTPChecksumTrait, SigV4Trait

__all__ = [
    "AwsChunkedReaderFactory",
    "ChecksumStreamFactory",
    "FlexibleChecksumsInterceptor",
]

logger: logging.Logger = logging.getLogger(__name__)


class ChecksumStreamFactory(Protocol):
    """Wraps a response payload in a stream that validates its checksum."""

    def __call__(
        self, source: Any, /, *, checksum_algorithm: str, expected: bytes
    ) -> Any: ...


class AwsChunkedReaderFactory(Protocol):
    """Wraps a request payload in a reader that encodes it as ``aws-chunked``."""

    def __call__(
        self,
        source: Any,
        /,
        *,
        decoded_length: int,
        checksum_algorithm: str,
        checksum: bytes | None,
        on_checksum: Callable[[bytes], None],
        chunk_signer: ChunkSigner | None,
    ) -> Any:
        """Wrap ``source`` in a reader that encodes it as it's read."""
        ...


class FlexibleChecksumsInterceptor(
    Interceptor[Any, Any, HTTPRequest, HTTPResponseInterface]
):
    """Adds and validates checksums for operations with the ``httpChecksum`` trait.

    Request checksums of streaming payloads are sent in an ``aws-chunked`` trailer,
    and others in a header. Over HTTP, a payload signed with SigV4 is signed as it's
    sent, chunk by chunk. When to calculate and validate them is
    read from the ``request_checksum_calculation`` and
    ``response_checksum_validation`` settings of each call's config, so plugins can
    change them per call. Operations without the trait are passed through unchanged.
    """

    def __init__(
        self,
        stream: ChecksumStreamFactory = ChecksumStream,
        chunked_reader: AwsChunkedReaderFactory | None = None,
    ) -> None:
        """Initialize the interceptor.

        Async clients use ``AsyncFlexibleChecksumsInterceptor`` instead, which passes
        the async stream and reader.

        :param stream: Wraps validated response payloads.
        :param chunked_reader: Encodes payloads that are read asynchronously with a
            trailing checksum. Without one, an asynchronous payload's checksum is sent
            in a header, if it can be calculated.
        :raises MissingDependencyError: If smithy-aws-checksums isn't installed.
        """
        assert_checksums_installed()
        self._stream = stream
        self._chunked_reader = chunked_reader

    def modify_before_serialization(self, context: InputContext[Any]) -> Any:
        operation = context.properties.get(OPERATION)
        if operation is None:
            return context.request
        trait = operation.schema.get_trait(HTTPChecksumTrait)
        if trait is None:
            return context.request
        algorithms = response_validation_order(trait.response_algorithms)
        field_name = _input_field_name(operation, trait.request_validation_mode_member)
        if not algorithms or field_name is None:
            return context.request

        # Feature IDs are only reported for operations the setting applies to.
        validation = _response_setting(context.properties)
        if (feature_id := _RESPONSE_SETTING_FEATURE_IDS.get(validation)) is not None:
            register_feature_id(context.properties, feature_id)

        request = context.request
        mode = getattr(request, field_name, None)
        if mode is None and validation == "when_supported":
            # Replace rather than mutate, so the caller's input isn't changed.
            request = replace(request, **{field_name: _VALIDATION_MODE_ENABLED})
            mode = _VALIDATION_MODE_ENABLED
        if mode is not None and str(mode) == _VALIDATION_MODE_ENABLED:
            context.properties[_RESPONSE_ALGORITHMS] = algorithms
        return request

    def modify_before_signing(
        self, context: RequestContext[Any, HTTPRequest]
    ) -> HTTPRequest:
        request = context.transport_request
        operation = context.properties.get(OPERATION)
        if operation is None:
            return request
        trait = operation.schema.get_trait(HTTPChecksumTrait)
        if trait is None or not (
            trait.request_checksum_required or trait.request_algorithm_member
        ):
            return request

        # Feature IDs are only reported for operations the setting applies to.
        calculation = _request_setting(context.properties)
        if (feature_id := _REQUEST_SETTING_FEATURE_IDS.get(calculation)) is not None:
            register_feature_id(context.properties, feature_id)

        # A checksum set by the caller is sent as is.
        provided = [checksum_header_algorithm(field.name) for field in request.fields]
        if any(provided):
            for algorithm in filter(None, provided):
                _register_algorithm_feature_id(context.properties, algorithm)
            return request

        # A retry reuses the algorithm and checksum, so a payload that changed is
        # rejected.
        chosen = None
        if (algorithm := context.properties.get(_REQUEST_ALGORITHM)) is None:
            chosen = _chosen_algorithm(context.request, operation, trait)
            algorithm = chosen
            if algorithm is None and (
                trait.request_checksum_required or calculation == "when_supported"
            ):
                algorithm = DEFAULT_ALGORITHM
            if algorithm is None:
                return request
            context.properties[_REQUEST_ALGORITHM] = algorithm

        # The request of each attempt shares its fields with the original, so copy
        # them before changing anything.
        request = copy(request)
        request.fields = deepcopy(request.fields)
        if (header := _algorithm_header(operation, trait)) is not None:
            if header not in request.fields:
                request.fields.set_field(Field(name=header, values=[algorithm]))

        if (
            _sends_trailer(operation, request)
            and self._chunked_reader_for(request.body) is not None
        ):
            # The checksum is calculated while the payload is sent, and sent after
            # it, so the payload is only read once.
            _set_trailer_fields(
                request, algorithm, signed=_signs_chunks(context.properties, request)
            )
            _register_algorithm_feature_id(context.properties, algorithm)
            return request

        if (value := context.properties.get(_REQUEST_CHECKSUM)) is None:
            value = _calculate(algorithm, request.body)
            if value is None:
                if chosen is not None or trait.request_checksum_required:
                    # A content length only helps if it lets the payload be encoded.
                    length_advice = (
                        "set the payload's content length, "
                        if "content-length" not in request.fields
                        and _can_send_trailer(operation, request)
                        and self._chunked_reader_for(request.body) is not None
                        else ""
                    )
                    raise SmithyError(
                        f"A {algorithm} request checksum can't be calculated for a "
                        f"payload of type {type(request.body).__name__}. Send bytes or a "
                        f"seekable file, {length_advice}or set the checksum on the "
                        "request."
                    )
                logger.debug(
                    "Skipping the request checksum: it can't be calculated for a "
                    "payload of type %s.",
                    type(request.body),
                )
                return context.transport_request
            context.properties[_REQUEST_CHECKSUM] = value

        request.fields.set_field(
            Field(name=checksum_header(algorithm), values=[encode_digest(value)])
        )
        _register_algorithm_feature_id(context.properties, algorithm)
        return request

    def modify_before_transmit(
        self, context: RequestContext[Any, HTTPRequest]
    ) -> HTTPRequest:
        """Encode the payload of a request that announces a trailing checksum."""
        request = context.transport_request
        properties = context.properties
        # Each attempt signs again and can take the header path, such as after its
        # endpoint changed, so only a request whose fields announce the trailer is
        # encoded.
        algorithm = properties.get(_REQUEST_ALGORITHM)
        if algorithm is None or not _announces_trailer(request, algorithm):
            return request

        def save(digest: bytes) -> None:
            properties[_REQUEST_CHECKSUM] = digest

        reader = self._chunked_reader_for(request.body)
        # Signing only chose a trailer for payloads with a reader.
        assert reader is not None  # noqa: S101
        chunk_signer = None
        if (
            "x-amz-content-sha256" in request.fields
            and request.fields["x-amz-content-sha256"].as_string()
            == _STREAMING_SIGNED_PAYLOAD_TRAILER
        ):
            # The request was signed without its payload, which is signed as it's
            # sent, continuing the signature of its headers.
            identity = properties[RESOLVED_IDENTITY]
            assert isinstance(identity, AWSCredentialsIdentity)  # noqa: S101
            chunk_signer = SigV4ChunkSigner.from_signed_request(request, identity)
        # Each attempt encodes the payload again, after the client rewound it.
        request = copy(request)
        # Exactly the length the fields declare is sent, so the body always matches
        # its framing.
        request.body = reader(
            request.body,
            decoded_length=int(
                request.fields["x-amz-decoded-content-length"].as_string()
            ),
            checksum_algorithm=algorithm,
            checksum=properties.get(_REQUEST_CHECKSUM),
            on_checksum=save,
            chunk_signer=chunk_signer,
        )
        return request

    def modify_before_deserialization(
        self, context: ResponseContext[Any, HTTPRequest, HTTPResponseInterface]
    ) -> HTTPResponseInterface:
        response = context.transport_response
        algorithms = context.properties.get(_RESPONSE_ALGORITHMS)
        if not algorithms or not 200 <= response.status < 300:
            return response

        for algorithm in algorithms:
            header = checksum_header(algorithm)
            if header not in response.fields:
                continue
            expected = decode_checksum(response.fields[header].as_string())
            if expected is None:
                # Empty, malformed, and composite (multipart) checksums can't be
                # validated, so try the next algorithm.
                continue
            # Build a new response, since not every transport's response allows
            # its body to be replaced.
            return HTTPResponse(
                status=response.status,
                fields=response.fields,
                reason=response.reason,
                body=self._stream(
                    response.body, checksum_algorithm=algorithm, expected=expected
                ),
            )

        logger.debug(
            "Skipping response checksum validation: the response has no valid "
            "checksum for any of the algorithms %s.",
            algorithms,
        )
        return response

    def _chunked_reader_for(self, body: object) -> AwsChunkedReaderFactory | None:
        if self._chunked_reader is None:
            # Without an async reader, only synchronous payloads can be encoded.
            return None if _reads_asynchronously(body) else AwsChunkedReader
        # A plain read() can return an awaitable, as an AwaitableBytesReader's does,
        # so only payloads known to read synchronously keep the sync reader, which
        # every HTTP client can stream. The async reader awaits what read() returns.
        if isinstance(body, bytes | bytearray | io.IOBase):
            return AwsChunkedReader
        return self._chunked_reader


_VALIDATION_MODE_ENABLED = "ENABLED"

_RESPONSE_ALGORITHMS = PropertyKey(
    key="response_checksum_algorithms", value_type=tuple[str, ...]
)
"""The algorithms to validate the response with, fastest first, if it's validated."""

_REQUEST_ALGORITHM = PropertyKey(key="request_checksum_algorithm", value_type=str)
"""The algorithm of the request checksum, kept to be reused on retries."""

_REQUEST_CHECKSUM = PropertyKey(key="request_checksum", value_type=bytes)
"""The request payload's digest, reused on a retry so a changed payload is rejected.

A trailing checksum is only saved once the payload was read to the end.
"""

_STREAMING_UNSIGNED_PAYLOAD_TRAILER = "STREAMING-UNSIGNED-PAYLOAD-TRAILER"
_STREAMING_SIGNED_PAYLOAD_TRAILER = "STREAMING-AWS4-HMAC-SHA256-PAYLOAD-TRAILER"

_READ_CHUNK_SIZE = 64 * 1024

_REQUEST_SETTING_FEATURE_IDS = {
    "when_supported": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_WHEN_SUPPORTED,
    "when_required": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_WHEN_REQUIRED,
}

_RESPONSE_SETTING_FEATURE_IDS = {
    "when_supported": AwsFeatureId.FLEXIBLE_CHECKSUMS_RES_WHEN_SUPPORTED,
    "when_required": AwsFeatureId.FLEXIBLE_CHECKSUMS_RES_WHEN_REQUIRED,
}

_ALGORITHM_FEATURE_IDS = {
    "CRC32": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_CRC32,
    "CRC32C": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_CRC32C,
    "CRC64NVME": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_CRC64,
    "SHA1": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_SHA1,
    "SHA256": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_SHA256,
    "SHA512": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_SHA512,
    "MD5": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_MD5,
    "XXHASH64": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_XXHASH64,
    "XXHASH3": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_XXHASH3,
    "XXHASH128": AwsFeatureId.FLEXIBLE_CHECKSUMS_REQ_XXHASH128,
}


def _request_setting(properties: TypedProperties) -> str:
    config = properties.get("config")
    return getattr(config, "request_checksum_calculation", None) or "when_supported"


def _response_setting(properties: TypedProperties) -> str:
    config = properties.get("config")
    return getattr(config, "response_checksum_validation", None) or "when_supported"


def _chosen_algorithm(
    request: Any, operation: APIOperation[Any, Any], trait: HTTPChecksumTrait
) -> str | None:
    field_name = _input_field_name(operation, trait.request_algorithm_member)
    chosen = getattr(request, field_name, None) if field_name else None
    if chosen is None:
        return None
    chosen = str(getattr(chosen, "value", chosen))
    if chosen.upper() not in SUPPORTED_ALGORITHMS:
        raise UnsupportedChecksumAlgorithmError(chosen)
    return chosen.upper()


def _calculate(algorithm: str, source: Any) -> bytes | None:
    """Calculate the payload's digest, if it can be read synchronously.

    Interceptor hooks are synchronous, so only bytes and seekable synchronous
    streams can be read here. The stream is returned to where it started.
    """
    if isinstance(source, bytes | bytearray):
        checksum = create_checksum(algorithm)
        checksum.update(source)
        return checksum.digest()

    read = getattr(source, "read", None)
    if read is None or iscoroutinefunction(read) or not _is_seekable(source):
        return None
    checksum = create_checksum(algorithm)
    start = source.tell()
    try:
        while chunk := read(_READ_CHUNK_SIZE):
            if isawaitable(chunk):
                # A plain read() that returns an awaitable can't be read in a hook.
                if (close := getattr(chunk, "close", None)) is not None:
                    close()
                return None
            checksum.update(chunk)
    finally:
        source.seek(start)
    return checksum.digest()


def _is_seekable(source: Any) -> bool:
    # Streams without seekable() are treated as seekable if they can seek, as the
    # retry of a request does.
    seek = getattr(source, "seek", None)
    tell = getattr(source, "tell", None)
    if seek is None or tell is None or iscoroutinefunction(seek):
        return False
    if (seekable := getattr(source, "seekable", None)) is None:
        return True
    return not iscoroutinefunction(seekable) and bool(seekable())


def _sends_trailer(operation: APIOperation[Any, Any], request: HTTPRequest) -> bool:
    # Services need to know the payload's length, so a payload of unknown length
    # isn't encoded.
    return "content-length" in request.fields and _can_send_trailer(operation, request)


def _can_send_trailer(operation: APIOperation[Any, Any], request: HTTPRequest) -> bool:
    return any(
        StreamingTrait in member and member.shape_type is ShapeType.BLOB
        for member in operation.input_schema.members.values()
    )


def _signs_chunks(properties: TypedProperties, request: HTTPRequest) -> bool:
    # Payloads sent over HTTP are signed so they can't be changed on the way, and
    # payloads sent over HTTPS or without SigV4, such as anonymously, aren't.
    if request.destination.scheme == "https":
        return False
    scheme = properties.get(AUTH_SCHEME)
    return getattr(scheme, "scheme_id", None) == SigV4Trait.id and isinstance(
        properties.get(RESOLVED_IDENTITY), AWSCredentialsIdentity
    )


def _set_trailer_fields(request: HTTPRequest, algorithm: str, *, signed: bool) -> None:
    fields = request.fields
    # The encoded payload is sent with chunked transfer encoding rather than a
    # content length, and its decoded length, which S3 requires, in its own header.
    fields.set_field(
        Field(
            name="x-amz-decoded-content-length",
            values=[fields["content-length"].as_string()],
        )
    )
    del fields["content-length"]
    fields.set_field(Field(name="transfer-encoding", values=["chunked"]))
    fields.set_field(Field(name="x-amz-trailer", values=[checksum_header(algorithm)]))
    payload_hash = (
        _STREAMING_SIGNED_PAYLOAD_TRAILER
        if signed
        else _STREAMING_UNSIGNED_PAYLOAD_TRAILER
    )
    fields.set_field(Field(name="x-amz-content-sha256", values=[payload_hash]))
    # aws-chunked is applied after any other encoding, such as compression.
    encodings = (
        fields["content-encoding"].values if "content-encoding" in fields else []
    )
    fields.set_field(Field(name="content-encoding", values=[*encodings, "aws-chunked"]))


def _announces_trailer(request: HTTPRequest, algorithm: str) -> bool:
    fields = request.fields
    return (
        "x-amz-trailer" in fields
        and fields["x-amz-trailer"].values == [checksum_header(algorithm)]
        and "x-amz-decoded-content-length" in fields
    )


def _reads_asynchronously(body: object) -> bool:
    if hasattr(body, "__aiter__"):
        return True
    return iscoroutinefunction(getattr(body, "read", None))


def _algorithm_header(
    operation: APIOperation[Any, Any], trait: HTTPChecksumTrait
) -> str | None:
    member = _input_member(operation, trait.request_algorithm_member)
    if member is None or (http_header := member.get_trait(HTTPHeaderTrait)) is None:
        return None
    return http_header.key


def _register_algorithm_feature_id(properties: TypedProperties, algorithm: str) -> None:
    if (feature_id := _ALGORITHM_FEATURE_IDS.get(algorithm)) is not None:
        register_feature_id(properties, feature_id)


def _input_member(
    operation: APIOperation[Any, Any], member_name: str | None
) -> Schema | None:
    if member_name is None:
        return None
    return operation.input_schema.members.get(member_name)


def _input_field_name(
    operation: APIOperation[Any, Any], member_name: str | None
) -> str | None:
    if (member := _input_member(operation, member_name)) is None:
        return None
    return member_field_name(
        member.expect_member_name(),
        is_error=False,
        carries_response_metadata=False,
        is_enum=False,
    )
