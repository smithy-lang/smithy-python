#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# This ruff check warns against using the assert statement, which can be stripped out
# when running Python with certain (common) optimization settings. Assert is used here
# for trait values. Since these are always generated, we can be fairly confident that
# they're correct regardless, so it's okay if the checks are stripped out.
# ruff: noqa: S101

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from smithy_core.shapes import ShapeID
from smithy_core.traits import DocumentValue, DynamicTrait, Trait


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
        assert isinstance(self.document_value, Mapping)

        http_versions = self.document_value["http"]
        assert isinstance(http_versions, Sequence)
        for val in http_versions:
            assert isinstance(val, str)
        object.__setattr__(self, "http", tuple(http_versions))
        event_stream_http_versions = self.document_value.get("eventStreamHttp")
        if not event_stream_http_versions:
            object.__setattr__(self, "event_stream_http", self.http)
        else:
            assert isinstance(event_stream_http_versions, Sequence)
            for val in event_stream_http_versions:
                assert isinstance(val, str)
            object.__setattr__(
                self, "event_stream_http", tuple(event_stream_http_versions)
            )
