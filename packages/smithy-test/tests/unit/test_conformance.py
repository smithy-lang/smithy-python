#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
# pyright: reportPrivateUsage=false
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from smithy_core._dynamic_models import ModelRegistry
from smithy_core._schema_compact import StaticSchema
from smithy_core.schemas import APIOperation
from smithy_core.shapes import ShapeType
from smithy_test import ConformanceError, verify_client, verify_models

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


NS = "ns.example"
STRING = ShapeType.STRING.value
REQUIRED = 1

TAG = (ShapeType.STRUCTURE.value, NS, "Tag", 0, ("Key",), ((STRING, REQUIRED),))
CONTENT = (ShapeType.UNION.value, NS, "Content", 0, ("text",), ((STRING, 0),))
OUTPUT = (ShapeType.STRUCTURE.value, NS, "PutOutput", {"smithy.api#output": None})
EVENTS = (
    ShapeType.UNION.value,
    NS,
    "Events",
    {"smithy.api#streaming": None},
    ("ping",),
    ((STRING, 0),),
)
INPUT = (
    ShapeType.STRUCTURE.value,
    NS,
    "PutInput",
    {"smithy.api#input": None},
    ("Name", "Tag", "Content", "Stream"),
    ((STRING, REQUIRED), (TAG, 0), (CONTENT, 0), (EVENTS, REQUIRED)),
)
EMPTY_INPUT = (
    ShapeType.STRUCTURE.value,
    NS,
    "ListInput",
    {"smithy.api#input": None},
)
LIST_OPERATION = (ShapeType.OPERATION.value, NS, "List", 0, EMPTY_INPUT, OUTPUT, ())
OPERATION = (ShapeType.OPERATION.value, NS, "Put", 0, INPUT, OUTPUT, ())

PARAMS_PYI = """
class TagParams(TypedDict, total=False):
    key: Required[str]

class ContentTextParams(TypedDict):
    text: str

ContentParams = ContentTextParams

class ListInputParams(TypedDict):
    pass

class PutInputParams(TypedDict, total=False):
    name: Required[str]
    tag: Tag | TagParams | None
    content: Content | ContentParams | None
"""

CLIENT_PYI = """
class Client:
    def __init__(self, config: Any = None) -> None: ...
    async def put(
        self, *, name: str, tag: Any = None, content: Any = None, plugins: Any = None
    ) -> Any: ...
"""


def _models() -> tuple[ModuleType, ModuleType, APIOperation[Any, Any]]:
    schemas = ModuleType("ns.example._private.schemas")
    schemas.TAG = TAG  # type: ignore[attr-defined]
    schemas.CONTENT = CONTENT  # type: ignore[attr-defined]
    schemas.PUT_INPUT = INPUT  # type: ignore[attr-defined]
    schemas.PUT_OUTPUT = OUTPUT  # type: ignore[attr-defined]
    schemas.EVENTS = EVENTS  # type: ignore[attr-defined]
    schemas.LIST_INPUT = EMPTY_INPUT  # type: ignore[attr-defined]
    registry = ModelRegistry(schemas)
    models = ModuleType("ns.example.models")
    operation: APIOperation[Any, Any] = APIOperation(
        static_schema=OPERATION, model_registry=registry
    )
    models._registry = registry  # type: ignore[attr-defined]
    models.PUT = operation  # type: ignore[attr-defined]
    models.LIST = APIOperation(  # type: ignore[attr-defined]
        static_schema=LIST_OPERATION, model_registry=registry
    )
    models.__getattr__ = registry.build  # type: ignore[attr-defined]
    return models, schemas, operation


class Client:
    def __init__(self, config: Any = None) -> None:
        pass

    async def put(
        self, *, name: str, tag: Any = None, content: Any = None, plugins: Any = None
    ) -> Any:
        pass


def test_verify_models_checks_params_stub(tmp_path: Path) -> None:
    models, schemas, _ = _models()
    path = tmp_path / "_params.pyi"
    path.write_text(PARAMS_PYI)
    verify_models(models, schemas, params_pyi_path=str(path))

    path.write_text(PARAMS_PYI.replace("key: Required[str]", "key: str | None"))
    with pytest.raises(ConformanceError, match="TagParams"):
        verify_models(models, schemas, params_pyi_path=str(path))

    path.write_text(PARAMS_PYI.replace("class TagParams", "class Tag_Params"))
    with pytest.raises(ConformanceError, match="missing \\['TagParams'\\]"):
        verify_models(models, schemas, params_pyi_path=str(path))


def test_verify_client(tmp_path: Path) -> None:
    _, _, operation = _models()
    path = tmp_path / "client.pyi"
    path.write_text(CLIENT_PYI)
    assert verify_client(Client, {"put": operation}, pyi_path=str(path)) == 1

    path.write_text(CLIENT_PYI.replace("tag: Any = None, ", ""))
    with pytest.raises(ConformanceError, match=r"client\.pyi parameters"):
        verify_client(Client, {"put": operation}, pyi_path=str(path))


def test_verify_client_rejects_mismatched_parameters() -> None:
    _, _, operation = _models()

    class Optional:
        async def put(
            self,
            *,
            name: str = "",
            tag: Any = None,
            content: Any = None,
            plugins: Any = None,
        ) -> Any:
            pass

    with pytest.raises(ConformanceError, match="required parameters"):
        verify_client(Optional, {"put": operation})

    class Misnamed:
        async def put(
            self,
            *,
            name: str,
            tags: Any = None,
            content: Any = None,
            plugins: Any = None,
        ) -> Any:
            pass

    with pytest.raises(ConformanceError, match="input members"):
        verify_client(Misnamed, {"put": operation})

    with pytest.raises(ConformanceError, match="operations given"):
        verify_client(Client, {})


def test_verify_models_checks_union_aliases_and_runtime_names(tmp_path: Path) -> None:
    models, schemas, _ = _models()
    path = tmp_path / "_params.pyi"
    path.write_text(
        PARAMS_PYI.replace(
            "ContentParams = ContentTextParams", "ContentParams = TagParams"
        )
    )
    with pytest.raises(ConformanceError, match="union aliases"):
        verify_models(models, schemas, params_pyi_path=str(path))

    path.write_text(PARAMS_PYI)
    registry = models._registry  # type: ignore[attr-defined]
    models.__getattr__ = lambda name: (  # type: ignore[attr-defined]
        None if name == "TagParams" else registry.build(name)
    )
    with pytest.raises(ConformanceError, match="TagParams: not importable"):
        verify_models(models, schemas, params_pyi_path=str(path))
