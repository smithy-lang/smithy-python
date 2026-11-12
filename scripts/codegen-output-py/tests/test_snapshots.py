# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import importlib
import json
import re
import sys
import tomllib
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import fields, is_dataclass
from enum import EnumType
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple

import pytest
from smithy_cbor import CBORCodec
from smithy_core._schema_compact import hydrate
from smithy_core.documents import Document
from smithy_core.schemas import Schema
from smithy_core.shapes import ShapeType
from smithy_json import JSONCodec
from smithy_python.model import OperationShape, Shape, load_model
from smithy_test import verify_models

_ROOT = Path(__file__).resolve().parents[3]
_INPUTS = _ROOT / "scripts/codegen-output-py"
_PROJECTIONS: dict[str, Any] = json.loads((_INPUTS / "projections.json").read_text())
_COUNTS = {
    # Data schemas and public model exports, including ServiceError.
    "aws-json-1-0": (44, 48),
    "aws-json-1-1": (53, 41),
    "aws-query": (73, 44),
    "ec2-query": (56, 35),
    "my-handwritten-json-model": (10, 17),
    "my-handwritten-model": (20, 33),
    "non-query-compatible-rpcv2-cbor": (0, 1),
    "partitioned-types": (270, 276),
    "query-compatible-aws-json-1-0": (2, 3),
    "query-compatible-rpcv2-cbor": (2, 3),
    "rest-json-1": (205, 197),
    "rest-xml": (144, 124),
    "rest-xml-with-namespace": (3, 4),
    "rpcv2-cbor": (56, 37),
    "rpcv2-json": (57, 31),
    "types": (10, 16),
}
_SOURCE_TRAITS = {
    "smithy.api#required",
    "smithy.api#sensitive",
    "smithy.api#default",
    "smithy.api#sparse",
    "smithy.api#enumValue",
    "smithy.api#jsonName",
    "smithy.api#timestampFormat",
    "smithy.api#mediaType",
    "smithy.api#xmlAttribute",
    "smithy.api#xmlFlattened",
    "smithy.api#xmlName",
    "smithy.api#xmlNamespace",
    "smithy.api#streaming",
    "smithy.api#error",
    "smithy.api#httpError",
    "smithy.api#httpHeader",
    "smithy.api#httpQuery",
    "smithy.api#httpLabel",
    "smithy.api#httpPayload",
    "smithy.api#httpPrefixHeaders",
    "smithy.api#httpQueryParams",
    "smithy.api#httpResponseCode",
    "smithy.api#idempotencyToken",
    "smithy.api#eventHeader",
    "smithy.api#eventPayload",
}


class Projection(NamedTuple):
    name: str
    package: str
    settings: dict[str, Any]

    @property
    def output(self) -> Path:
        return _ROOT / "codegen-output-py" / self.name

    @property
    def model(self) -> dict[str, Any]:
        return json.loads((_INPUTS / self.settings["model"]).read_text())


@pytest.fixture(params=sorted(_PROJECTIONS))
def projection(request: pytest.FixtureRequest) -> Projection:
    name: str = request.param
    settings = _PROJECTIONS[name]
    return Projection(name, settings["package"], settings)


@contextmanager
def _import_package(
    source: Path, package: str
) -> Iterator[tuple[ModuleType, ModuleType]]:
    # Both snapshot trees deliberately use the same package names. Isolate imports
    # so a warm Java package cannot satisfy a native import, or vice versa.
    saved = {
        name: module
        for name, module in sys.modules.items()
        if name == package or name.startswith(package + ".")
    }
    for name in saved:
        del sys.modules[name]
    sys.path.insert(0, str(source))
    try:
        models = importlib.import_module(f"{package}.models")
        schemas = importlib.import_module(f"{package}._private.schemas")
        yield models, schemas
    finally:
        sys.path.remove(str(source))
        for name in tuple(sys.modules):
            if name == package or name.startswith(package + "."):
                del sys.modules[name]
        sys.modules.update(saved)


@pytest.fixture
def generated(projection: Projection) -> Iterator[tuple[ModuleType, ModuleType]]:
    with _import_package(projection.output / "src", projection.package) as modules:
        yield modules


def _schemas_by_id(schemas: ModuleType) -> dict[str, Schema]:
    result: dict[str, Schema] = {}
    for name in dir(schemas):
        if name.isupper() and not name.startswith("_"):
            value = getattr(schemas, name)
            if isinstance(value, tuple):
                schema = hydrate(value)
                result[str(schema.id)] = schema
    return result


def _traits(schema: Schema) -> dict[str, Any]:
    return {str(id_): trait.document_value for id_, trait in schema.traits.items()}


def _describe(schema: Schema) -> dict[str, Any]:
    return {
        "type": schema.shape_type,
        "traits": _traits(schema),
        "members": [
            {
                "id": str(member.id),
                "type": member.shape_type,
                "index": member.expect_member_index(),
                "target": str(member.expect_member_target().id),
                "traits": _traits(member),
            }
            for member in schema.members_by_index
        ],
    }


def test_projection_set_matches_java_configuration() -> None:
    projections = json.loads(
        (_ROOT / "codegen/protocol-test/smithy-build.json").read_text()
    )["projections"]
    assert set(_PROJECTIONS) == set(projections) | {"types", "partitioned-types"}
    for name, projection in projections.items():
        settings = projection["plugins"]["python-client-codegen"]
        assert _PROJECTIONS[name]["package"] == settings["module"]
        assert _PROJECTIONS[name]["service"] == settings["service"]
        assert _PROJECTIONS[name]["version"] == settings["moduleVersion"]
    provenance = json.loads((_INPUTS / "models/provenance.json").read_text())
    assert set(provenance) == set(projections)
    for name, hashes in provenance.items():
        content = (_INPUTS / _PROJECTIONS[name]["model"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == hashes["fixture_sha256"]


def test_artifact_contains_only_supported_files(projection: Projection) -> None:
    source = projection.output / "src" / projection.package
    manifest = json.loads(
        (projection.output / ".smithy-python-manifest.json").read_text()
    )
    expected = {
        "README.md",
        "pyproject.toml",
        f"src/{projection.package}/__init__.py",
        f"src/{projection.package}/models.py",
        f"src/{projection.package}/models.pyi",
        f"src/{projection.package}/py.typed",
        f"src/{projection.package}/_private/__init__.py",
        f"src/{projection.package}/_private/schemas.py",
    }
    partitions = {
        f"src/{projection.package}/_private/{path.name}"
        for path in (source / "_private").iterdir()
        if re.fullmatch(r"(schemas_\d+\.py|models_\d+\.pyi)", path.name)
    }
    assert set(manifest["files"]) == expected | partitions
    for path, hash_ in manifest["files"].items():
        assert (
            hashlib.sha256((projection.output / path).read_bytes()).hexdigest() == hash_
        )
    metadata = tomllib.loads((projection.output / "pyproject.toml").read_text())
    assert metadata["project"]["name"] == projection.package
    assert metadata["project"]["version"] == projection.settings["version"]
    assert metadata["project"]["description"] == projection.settings["description"]
    assert all(
        dependency.startswith("smithy-core")
        for dependency in metadata["project"]["dependencies"]
    )
    assert (source / "py.typed").read_bytes() == b""


def test_public_models_load_lazily_and_match_stubs(
    projection: Projection, generated: tuple[ModuleType, ModuleType]
) -> None:
    models, schemas = generated
    exports: tuple[str, ...] = models.__all__
    assert exports[0] == "ServiceError"
    assert len(exports) == _COUNTS[projection.name][1]
    assert len(exports) == len(set(exports))
    for name in exports[1:]:
        assert name in dir(models)
        assert name not in vars(models)
    pyi = projection.output / "src" / projection.package / "models.pyi"
    verify_models(models, schemas, pyi_path=str(pyi))
    # Data streams need a transport serializer; a JSON document codec cannot
    # represent them. Their serializer/deserializer dispatch is checked separately.
    verify_models(models, _document_schemas(schemas), codec=JSONCodec())
    namespace: dict[str, Any] = {}
    exec(f"from {projection.package}.models import *", namespace)
    for name in exports:
        value = getattr(models, name)
        assert namespace[name] is value
        assert getattr(models, name) is value
        if isinstance(value, type):
            assert value.__module__ == models.__name__
    with pytest.raises(AttributeError):
        getattr(models, "NotAModel")


def test_schema_ids_types_traits_and_member_order_match_ast(
    projection: Projection, generated: tuple[ModuleType, ModuleType]
) -> None:
    _, schemas = generated
    native = _schemas_by_id(schemas)
    assert len(native) == _COUNTS[projection.name][0]
    model = load_model(projection.model)
    operations = tuple(model.iter_shapes(OperationShape))
    inputs = {str(operation.input) for operation in operations}
    outputs = {str(operation.output) for operation in operations}
    for id_, schema in native.items():
        source = model.get_shape(id_)
        assert schema.shape_type.name == source.type.name
        assert schema.shape_type.name not in ("SERVICE", "OPERATION", "RESOURCE")
        _assert_source_traits(schema, source)
        if schema.shape_type is ShapeType.STRUCTURE:
            assert ("smithy.api#input" in _traits(schema)) == (
                id_ in inputs or source.has_trait("input")
            )
            assert ("smithy.api#output" in _traits(schema)) == (
                id_ in outputs or source.has_trait("output")
            )
        members = source.members
        assert tuple(schema.members) == tuple(members)
        assert tuple(m.expect_member_name() for m in schema.members_by_index) == tuple(
            members
        )
        for index, (name, member_source) in enumerate(members.items()):
            member = schema.members[name]
            assert str(member.id) == f"{id_}${name}"
            assert member.expect_member_index() == index
            assert str(member.expect_member_target().id) == str(member_source.target)
            _assert_source_traits(member, member_source)


def _assert_source_traits(schema: Schema, source: Shape) -> None:
    actual = _traits(schema)
    for trait_id, value in source.traits.items():
        id_ = str(trait_id)
        if id_ in _SOURCE_TRAITS:
            assert id_ in actual, (schema.id, id_)
            expected = None if value == {} and id_ != "smithy.api#default" else value
            assert actual[id_] == expected, (schema.id, id_)
    assert "smithy.api#documentation" not in actual
    assert "smithy.test#httpRequestTests" not in actual
    assert "smithy.test#httpResponseTests" not in actual


def _document_schemas(schemas: ModuleType) -> ModuleType:
    result = ModuleType(schemas.__name__)
    for name in dir(schemas):
        if name.isupper() and not name.startswith("_"):
            value = getattr(schemas, name)
            if isinstance(value, tuple) and not _has_data_stream(hydrate(value)):
                setattr(result, name, value)
    return result


def _has_data_stream(root: Schema) -> bool:
    visited: set[str] = set()
    pending = [root]
    while pending:
        schema = pending.pop()
        if str(schema.id) in visited:
            continue
        visited.add(str(schema.id))
        if schema.shape_type is ShapeType.BLOB and "smithy.api#streaming" in _traits(
            schema
        ):
            return True
        pending.extend(
            member.expect_member_target() for member in schema.members.values()
        )
    return False


def test_partition_facade_is_lazy_and_preserves_identity(
    projection: Projection, generated: tuple[ModuleType, ModuleType]
) -> None:
    _, schemas = generated
    partitions = sorted(
        (projection.output / "src" / projection.package / "_private").glob(
            "schemas_*.py"
        )
    )
    if not partitions:
        assert "_SCHEMA_PARTITIONS" not in vars(schemas)
        return
    prefix = f"{projection.package}._private.schemas_"
    assert not any(name.startswith(prefix) for name in sys.modules)
    exports = tuple(
        name for name in dir(schemas) if name.isupper() and not name.startswith("_")
    )
    assert exports
    assert all(name in dir(schemas) and name not in vars(schemas) for name in exports)
    first = getattr(schemas, exports[0])
    assert getattr(schemas, exports[0]) is first
    assert sum(name.startswith(prefix) for name in sys.modules) == 1
    for name in exports:
        value = getattr(schemas, name)
        owners = [
            module
            for module_name, module in tuple(sys.modules.items())
            if module_name.startswith(prefix) and name in vars(module)
        ]
        assert len(owners) == 1
        assert getattr(owners[0], name) is value
    with pytest.raises(AttributeError):
        getattr(schemas, "NOT_A_SCHEMA")


def test_common_java_model_and_schema_behavior(projection: Projection) -> None:
    if projection.name in ("types", "partitioned-types"):
        return
    with _import_package(projection.output / "src", projection.package) as (
        models,
        schemas,
    ):
        native = {
            id_: _describe(schema) for id_, schema in _schemas_by_id(schemas).items()
        }
        surface = _model_surface(models)
    java_source = _ROOT / "codegen-output" / projection.name / "src"
    with _import_package(java_source, projection.package) as (models, schemas):
        java = {
            id_: _describe(schema) for id_, schema in _schemas_by_id(schemas).items()
        }
        java_surface = _model_surface(models)
    common = native.keys() & java.keys()
    # Dedicated client I/O structures have different IDs. Shared types can carry
    # input/output markers in native types but not Java's normalized client model.
    # AWS query error metadata is provided by Java's AWS integration.
    assert common or not native
    for id_ in common:
        assert _common_metadata(native[id_]) == _common_metadata(java[id_]), id_
    for name in surface.keys() & java_surface.keys():
        assert surface[name] == java_surface[name], name


def _common_metadata(description: dict[str, Any]) -> dict[str, Any]:
    excluded = {
        "smithy.api#input",
        "smithy.api#output",
        "aws.protocols#awsQueryError",
    }
    return {
        **description,
        "traits": {
            id_: value
            for id_, value in description["traits"].items()
            if id_ not in excluded
        },
        "members": [
            {
                **member,
                "traits": {
                    id_: value
                    for id_, value in member["traits"].items()
                    if id_ not in excluded
                },
            }
            for member in description["members"]
        ],
    }


def _model_surface(models: ModuleType) -> dict[str, Any]:
    surface: dict[str, Any] = {}
    for name in models.__all__:
        value = getattr(models, name)
        if isinstance(value, EnumType):
            surface[name] = {member.name: member.value for member in value}
        elif is_dataclass(value):
            surface[name] = tuple(field.name for field in fields(value))
    return surface


def test_rpcv2_cbor_models_round_trip_without_a_client() -> None:
    with _import_package(_ROOT / "codegen-output-py/rpcv2-cbor/src", "rpcv2cbor") as (
        models,
        schemas,
    ):
        count = verify_models(models, schemas, codec=CBORCodec())
        assert count > 20
        value = models.RecursiveShapesInputOutputNested1(
            foo="first",
            nested=models.RecursiveShapesInputOutputNested2(bar="second"),
        )
        codec = CBORCodec()
        assert codec.deserialize(codec.serialize(value), type(value)) == value


def test_partitioned_models_resolve_cross_partition_and_recursive_targets() -> None:
    with _import_package(
        _ROOT / "codegen-output-py/partitioned-types/src", "partitioned_types"
    ) as (models, schemas):
        private = (
            _ROOT / "codegen-output-py/partitioned-types/src/partitioned_types/_private"
        )
        assert len(list(private.glob("models_*.pyi"))) == 2
        assert len(list(private.glob("schemas_*.py"))) == 3
        left = models.PartitionItem000(
            value="first", next=models.PartitionItem001(value="second")
        )
        assert JSONCodec().deserialize(JSONCodec().serialize(left), type(left)) == left
        cycle = hydrate(schemas.PARTITION_ITEM258)
        other = cycle.members["next"].expect_member_target()
        assert str(other.id) == "example#PartitionItem259"
        assert other.members["next"].expect_member_target() is cycle


def test_original_types_cover_renames_enums_unions_and_streaming_members() -> None:
    with _import_package(_ROOT / "codegen-output-py/types/src", "example_types") as (
        models,
        schemas,
    ):
        assert "RenamedExample" in models.__all__
        assert "Example" not in models.__all__
        assert models.Status.ACTIVE == "active"
        assert models.Status("future").value == "future"
        assert models.Code.OK == 200
        union = models.ExampleValueEmpty(value=models.Unit())
        assert JSONCodec().serialize(union) == b'{"empty":{}}'
        assert models.ExampleValueUnknown(tag="future").tag == "future"
        example = models.RenamedExample(
            name="sample",
            count=3,
            tags=["one", "two"],
            attributes={"answer": Document(42)},
            choice=models.ExampleValueText(value="selected"),
            status=models.Status.ACTIVE,
            code=models.Code.OK,
        )
        codec = JSONCodec()
        body = codec.serialize(example)
        assert json.loads(body) == {
            "name": "sample",
            "count": 3,
            "tags": ["one", "two"],
            "attributes": {"answer": 42},
            "choice": {"text": "selected"},
            "status": "active",
            "code": 200,
        }
        decoded = codec.deserialize(body, models.RenamedExample)
        assert codec.serialize(decoded) == body
        assert decoded.status is models.Status.ACTIVE
        output = models.GetExampleOutput()
        assert not hasattr(output, "events")
        assert "events" in hydrate(schemas.GET_EXAMPLE_OUTPUT).members


def test_streaming_blob_serde_uses_stream_dispatch() -> None:
    with _import_package(_ROOT / "codegen-output-py/rest-json-1/src", "restjson") as (
        models,
        schemas,
    ):
        payload = b"stream"
        value = models.StreamingTraitsInputOutput(blob=payload)

        class Serializer:
            def write_data_stream(self, schema: Schema, value: Any) -> None:
                assert schema.expect_member_name() == "blob"
                assert value is payload
                self.written = True

        class Deserializer:
            def read_struct(self, schema: Schema, consumer: Any) -> None:
                consumer(schema.members["blob"], self)

            def read_data_stream(self, schema: Schema) -> bytes:
                assert schema.expect_member_name() == "blob"
                return payload

        serializer = Serializer()
        value.serialize_members(serializer)
        assert serializer.written
        decoded = models.StreamingTraitsInputOutput.deserialize(Deserializer())
        assert decoded.blob is payload
        assert str(hydrate(schemas.STREAMING_TRAITS_INPUT_OUTPUT).id).endswith(
            "#StreamingTraitsInputOutput"
        )
