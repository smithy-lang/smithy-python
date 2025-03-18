#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# This ruff check warns against using the assert statement, which can be stripped out
# when running Python with certain (common) optimization settings. Assert is used here
# for trait values. Since these are always generated, we can be fairly confident that
# they're correct regardless, so it's okay if the checks are stripped out.
# ruff: noqa: S101

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from smithy_core.shapes import ShapeID
from smithy_core.traits import Trait, DocumentValue, DynamicTrait


@dataclass(init=False, frozen=True)
class RestJson1Trait(Trait, id=ShapeID("aws.protocols#restJson1")):
    http: set[str] = field(repr=False, hash=False, compare=False, default_factory=set)
    eventStreamHttp: set[str] = field(
        repr=False, hash=False, compare=False, default_factory=set
    )

    def __init__(self, value: DocumentValue | DynamicTrait = None):
        super().__init__(value)
        assert isinstance(self.document_value, Mapping)

        assert isinstance(self.document_value["http"], Sequence)
        for val in self.document_value["http"]:
            assert isinstance(val, str)
            self.http.add(val)

        if vals := self.document_value.get("eventStreamHttp") is None:
            object.__setattr__(self, "eventStreamHttp", self.http)
        else:
            # check that eventStreamHttp is a subset of http
            assert isinstance(vals, Sequence)
            for val in self.document_value["eventStreamHttp"]:
                assert val in self.http
                assert isinstance(val, str)
                self.eventStreamHttp.add(val)
