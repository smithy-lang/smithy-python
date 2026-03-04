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


@dataclass(init=False, frozen=True)
class RestJson1Trait(Trait, id=ShapeID("aws.protocols#restJson1")):
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
class AwsJson1_0Trait(Trait, id=ShapeID("aws.protocols#awsJson1_0")):
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
class SigV4Trait(Trait, id=ShapeID("aws.auth#sigv4")):
    def __post_init__(self):
        assert isinstance(self.document_value, Mapping)
        assert isinstance(self.document_value["name"], str)

    @property
    def name(self) -> str:
        return self.document_value["name"]  # type: ignore
