#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# This ruff check warns against using the assert statement, which can be stripped out
# when running Python with certain (common) optimization settings. Assert is used here
# for trait values. Since these are always generated, we can be fairly confident that
# they're correct regardless, so it's okay if the checks are stripped out.
# ruff: noqa: S101

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from smithy_core.documents import DocumentValue
from smithy_core.shapes import ShapeID
from smithy_core.traits import DynamicTrait, Trait

__all__ = [
    "AwsJson1_0Trait",
    "AwsJson1_1Trait",
    "AwsQueryErrorTrait",
    "AwsQueryTrait",
    "Ec2QueryNameTrait",
    "Ec2QueryTrait",
    "HTTPChecksumTrait",
    "RestJson1Trait",
    "RestXmlTrait",
    "SigV4Trait",
]


@dataclass(init=False, frozen=True)
class RestJson1Trait(Trait, id=ShapeID("aws.protocols#restJson1")):
    """The ``aws.protocols#restJson1`` protocol trait."""

    http: Sequence[str] = field(
        repr=False, hash=False, compare=False, default_factory=tuple
    )
    event_stream_http: Sequence[str] = field(
        repr=False, hash=False, compare=False, default_factory=tuple
    )

    def __init__(self, value: DocumentValue | DynamicTrait = None):
        super().__init__(value)
        http, event_stream_http = _parse_http_protocol_values(value)
        object.__setattr__(self, "http", http)
        object.__setattr__(self, "event_stream_http", event_stream_http)


@dataclass(init=False, frozen=True)
class RestXmlTrait(Trait, id=ShapeID("aws.protocols#restXml")):
    """The ``aws.protocols#restXml`` protocol trait."""


@dataclass(init=False, frozen=True)
class AwsJson1_0Trait(Trait, id=ShapeID("aws.protocols#awsJson1_0")):
    """The ``aws.protocols#awsJson1_0`` protocol trait."""

    http: Sequence[str] = field(
        repr=False, hash=False, compare=False, default_factory=tuple
    )
    event_stream_http: Sequence[str] = field(
        repr=False, hash=False, compare=False, default_factory=tuple
    )

    def __init__(self, value: DocumentValue | DynamicTrait = None):
        super().__init__(value)
        http, event_stream_http = _parse_http_protocol_values(value)
        object.__setattr__(self, "http", http)
        object.__setattr__(self, "event_stream_http", event_stream_http)


@dataclass(init=False, frozen=True)
class AwsJson1_1Trait(Trait, id=ShapeID("aws.protocols#awsJson1_1")):
    """The ``aws.protocols#awsJson1_1`` protocol trait."""

    http: Sequence[str] = field(
        repr=False, hash=False, compare=False, default_factory=tuple
    )
    event_stream_http: Sequence[str] = field(
        repr=False, hash=False, compare=False, default_factory=tuple
    )

    def __init__(self, value: DocumentValue | DynamicTrait = None):
        super().__init__(value)
        http, event_stream_http = _parse_http_protocol_values(value)
        object.__setattr__(self, "http", http)
        object.__setattr__(self, "event_stream_http", event_stream_http)


@dataclass(frozen=True)
class AwsQueryTrait(Trait, id=ShapeID("aws.protocols#awsQuery")):
    """The ``aws.protocols#awsQuery`` protocol trait."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class AwsQueryErrorTrait(Trait, id=ShapeID("aws.protocols#awsQueryError")):
    """Sets the error code and HTTP status an awsQuery error is returned with."""

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, Mapping)
        assert isinstance(self.document_value.get("code"), str)
        assert isinstance(self.document_value.get("httpResponseCode"), int)

    @property
    def code(self) -> str:
        """The error code the service returns for the error."""
        return self.document_value["code"]  # type: ignore

    @property
    def http_response_code(self) -> int:
        """The HTTP status code the service returns for the error."""
        return self.document_value["httpResponseCode"]  # type: ignore


@dataclass(frozen=True)
class Ec2QueryTrait(Trait, id=ShapeID("aws.protocols#ec2Query")):
    """The ``aws.protocols#ec2Query`` protocol trait."""

    def __post_init__(self) -> None:
        assert self.document_value is None


@dataclass(init=False, frozen=True)
class Ec2QueryNameTrait(Trait, id=ShapeID("aws.protocols#ec2QueryName")):
    """Overrides the name a member is serialized under in ec2Query requests."""

    document_value: str | None = None

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, str)

    @property
    def value(self) -> str:
        """The serialized member name."""
        return self.document_value  # type: ignore


@dataclass(init=False, frozen=True)
class HTTPChecksumTrait(Trait, id=ShapeID("aws.protocols#httpChecksum")):
    """Indicates that an operation supports checksums of its HTTP payloads.

    See the `httpChecksum trait documentation
    <https://smithy.io/2.0/aws/aws-core.html#aws-protocols-httpchecksum-trait>`_.
    """

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, Mapping)

    @property
    def request_checksum_required(self) -> bool:
        """Whether a checksum of the request payload must be sent."""
        return self.document_value.get("requestChecksumRequired", False)  # type: ignore

    @property
    def request_algorithm_member(self) -> str | None:
        """The input member that names the request checksum algorithm."""
        return self.document_value.get("requestAlgorithmMember")  # type: ignore

    @property
    def request_validation_mode_member(self) -> str | None:
        """The input member that enables validation of the response checksum."""
        return self.document_value.get("requestValidationModeMember")  # type: ignore

    @property
    def response_algorithms(self) -> tuple[str, ...]:
        """The algorithms the service may use for response checksums."""
        return tuple(self.document_value.get("responseAlgorithms", ()))  # type: ignore


@dataclass(init=False, frozen=True)
class SigV4Trait(Trait, id=ShapeID("aws.auth#sigv4")):
    """Configures SigV4 signing for a service."""

    def __post_init__(self) -> None:
        assert isinstance(self.document_value, Mapping)
        assert isinstance(self.document_value["name"], str)

    @property
    def name(self) -> str:
        """The signing name of the service."""
        return self.document_value["name"]  # type: ignore


def _parse_http_protocol_values(
    value: DocumentValue | DynamicTrait | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Parse aws.protocols HTTP settings from a trait document.

    The input is expected to be shaped like {"http": [...], "eventStreamHttp": [...]}
    and returns (http_versions, event_stream_http_versions). If "eventStreamHttp"
    is absent, event streams use the same versions as "http". If "http" is absent,
    it defaults to ("http/1.1",).
    """
    document_value = value or {}
    assert isinstance(document_value, Mapping)

    http_versions_raw = document_value.get("http", ["http/1.1"])
    assert isinstance(http_versions_raw, Sequence)
    http_versions_list: list[str] = []
    for entry in http_versions_raw:
        assert isinstance(entry, str)
        http_versions_list.append(entry)
    http_versions = tuple(http_versions_list)

    event_stream_http_versions_raw = document_value.get("eventStreamHttp")
    if not event_stream_http_versions_raw:
        return http_versions, http_versions

    assert isinstance(event_stream_http_versions_raw, Sequence)
    event_stream_http_versions_list: list[str] = []
    for entry in event_stream_http_versions_raw:
        assert isinstance(entry, str)
        event_stream_http_versions_list.append(entry)

    return http_versions, tuple(event_stream_http_versions_list)
