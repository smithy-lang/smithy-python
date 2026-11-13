# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest
from smithy_core._schema_compact import StaticSchema
from smithy_core.shapes import ShapeType
from smithy_test import verify_models
from smithy_test._private.conformance import ConformanceError

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


_THING_STUB = """
from dataclasses import dataclass
from typing import TypedDict

@dataclass
class Thing:
    name: str

class ThingParams(TypedDict, total=False):
    name: str | None
"""
_CHOICE_STUB = """
from typing import TypedDict, Union

class ChoiceTextParams(TypedDict):
    text: str

ChoiceParams = Union[ChoiceTextParams]
"""
_PARAMS_NAMES = frozenset({"ThingParams", "ChoiceTextParams", "ChoiceParams"})


def _write_params_stub(tmp_path: Path, partitioned: bool) -> Path:
    """Write the stub whole, or as a facade over two partitions that refer to it."""
    stub = tmp_path / "models.pyi"
    if not partitioned:
        stub.write_text(_THING_STUB + _CHOICE_STUB)
        return stub
    private = tmp_path / "_private"
    private.mkdir()
    # A partition imports what another declares through the facade, as generated
    # partitions do, so following the stub's imports has to stop at the cycle.
    (private / "models_0.pyi").write_text(
        "from ..models import ChoiceParams as ChoiceParams\n" + _THING_STUB
    )
    (private / "models_1.pyi").write_text(
        "from ..models import ThingParams as ThingParams\n" + _CHOICE_STUB
    )
    stub.write_text(
        "from ._private.models_0 import (\n"
        "    Thing as Thing,\n"
        "    ThingParams as ThingParams,\n"
        ")\n"
        "from ._private.models_1 import (\n"
        "    ChoiceParams as ChoiceParams,\n"
        "    ChoiceTextParams as ChoiceTextParams,\n"
        ")\n"
    )
    return stub


def _thing_modules() -> tuple[ModuleType, ModuleType]:
    schemas = ModuleType("example._private.schemas")
    schemas.THING = (  # type: ignore[attr-defined]
        ShapeType.STRUCTURE.value,
        "example",
        "Thing",
        0,
        ("name",),
        ((ShapeType.STRING.value, _REQUIRED),),
    )

    @dataclass
    class Thing:
        name: str

    models = ModuleType("example.models")
    models.Thing = Thing  # type: ignore[attr-defined]
    return models, schemas


@pytest.mark.parametrize("partitioned", [False, True])
def test_dictionary_forms_in_the_stub_are_dict_at_runtime(
    tmp_path: Path, partitioned: bool
) -> None:
    models, schemas = _thing_modules()
    for name in _PARAMS_NAMES:
        setattr(models, name, dict)
    stub = _write_params_stub(tmp_path, partitioned)

    assert verify_models(models, schemas, pyi_path=str(stub)) == 1


@pytest.mark.parametrize("partitioned", [False, True])
@pytest.mark.parametrize("missing", sorted(_PARAMS_NAMES))
def test_dictionary_form_missing_at_runtime_is_reported(
    tmp_path: Path, missing: str, partitioned: bool
) -> None:
    models, schemas = _thing_modules()
    for name in _PARAMS_NAMES - {missing}:
        setattr(models, name, dict)
    stub = _write_params_stub(tmp_path, partitioned)

    with pytest.raises(ConformanceError, match=f"{missing}: .*not `dict` at runtime"):
        verify_models(models, schemas, pyi_path=str(stub))


@pytest.mark.parametrize("partitioned", [False, True])
@pytest.mark.parametrize("wrong", sorted(_PARAMS_NAMES))
def test_dictionary_form_that_is_not_dict_at_runtime_is_reported(
    tmp_path: Path, wrong: str, partitioned: bool
) -> None:
    models, schemas = _thing_modules()
    for name in _PARAMS_NAMES:
        setattr(models, name, dict)
    # A class of its own would make the name a second model, not a dictionary.
    setattr(models, wrong, type(wrong, (), {}))
    stub = _write_params_stub(tmp_path, partitioned)

    with pytest.raises(ConformanceError, match=f"{wrong}: .*not `dict` at runtime"):
        verify_models(models, schemas, pyi_path=str(stub))


def test_serde_conformance_capitalizes_union_member_names() -> None:
    choice: StaticSchema = (
        ShapeType.UNION.value,
        "example",
        "Choice",
        0,
        ("myValue",),
        ((ShapeType.STRING.value, 0),),
    )
    request: StaticSchema = (
        ShapeType.STRUCTURE.value,
        "example",
        "Request",
        0,
        ("choice",),
        ((lambda: choice, _REQUIRED),),
    )
    schemas = ModuleType("example._private.schemas")
    schemas.CHOICE = choice  # type: ignore[attr-defined]
    schemas.REQUEST = request  # type: ignore[attr-defined]

    @dataclass
    class ChoiceMyValue:
        value: str

    @dataclass
    class Request:
        choice: ChoiceMyValue

    models = ModuleType("example.models")
    models.ChoiceMyValue = ChoiceMyValue  # type: ignore[attr-defined]
    models.Request = Request  # type: ignore[attr-defined]

    class _Codec:
        def serialize(self, value: Request) -> bytes:
            assert value.choice == ChoiceMyValue(value="x")
            return b""

        def deserialize(self, body: bytes, cls: type[Request]) -> Request:
            return cls(choice=ChoiceMyValue(value="x"))

    assert verify_models(models, schemas, codec=_Codec()) == 1
