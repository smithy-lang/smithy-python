# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest
from smithy_core._schema_compact import StaticSchema
from smithy_core.shapes import ShapeType
from smithy_test import verify_models

_REQUIRED: dict[str, object] = {"smithy.api#required": {}}
_STREAMING: dict[str, object] = {"smithy.api#streaming": {}}


@pytest.mark.parametrize("partitioned", [False, True])
def test_event_stream_members_are_not_model_fields(
    tmp_path: Path, partitioned: bool
) -> None:
    events: StaticSchema = (
        ShapeType.UNION.value,
        "example",
        "Events",
        _STREAMING,
        ("message",),
        ((ShapeType.STRING.value, 0),),
    )
    input_schema: StaticSchema = (
        ShapeType.STRUCTURE.value,
        "example",
        "PublishEventsInput",
        0,
        ("channel", "events"),
        (
            (ShapeType.STRING.value, _REQUIRED),
            (lambda: events, _REQUIRED),
        ),
    )
    schemas = ModuleType("example._private.schemas")
    schemas.EVENTS = events  # type: ignore[attr-defined]
    schemas.PUBLISH_EVENTS_INPUT = input_schema  # type: ignore[attr-defined]

    @dataclass
    class PublishEventsInput:
        channel: str

    models = ModuleType("example.models")
    models.PublishEventsInput = PublishEventsInput  # type: ignore[attr-defined]

    class _Codec:
        def serialize(self, value: PublishEventsInput) -> bytes:
            assert value.channel == "x"
            return b""

        def deserialize(
            self, body: bytes, cls: type[PublishEventsInput]
        ) -> PublishEventsInput:
            return cls(channel="x")

    stub = tmp_path / "models.pyi"
    declaration = (
        "from dataclasses import dataclass\n"
        "@dataclass\n"
        "class PublishEventsInput:\n"
        "    channel: str\n"
    )
    if partitioned:
        private = tmp_path / "_private"
        private.mkdir()
        (private / "models_0.pyi").write_text(declaration)
        stub.write_text(
            "from ._private.models_0 import PublishEventsInput as PublishEventsInput\n"
        )
    else:
        stub.write_text(declaration)

    assert verify_models(models, schemas, codec=_Codec(), pyi_path=str(stub)) == 1
