# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from smithy_core._schema_compact import StaticSchema
from smithy_core.shapes import ShapeType
from smithy_test import verify_models

_REQUIRED: dict[str, object] = {"smithy.api#required": {}}
_STREAMING: dict[str, object] = {"smithy.api#streaming": {}}


def test_event_stream_members_are_not_model_fields(tmp_path: Path) -> None:
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
    stub.write_text(
        "from dataclasses import dataclass\n"
        "@dataclass\n"
        "class PublishEventsInput:\n"
        "    channel: str\n"
    )

    assert verify_models(models, schemas, codec=_Codec(), pyi_path=str(stub)) == 1
