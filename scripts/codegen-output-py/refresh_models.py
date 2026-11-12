# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Refresh checked-in model inputs from a directory of assembled JSON ASTs.

The input directory contains <projection>/model/model.json. This maintenance
command does not assemble Smithy IDL or invoke a build system.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_INPUTS = Path(__file__).parent
_VECTOR_TRAITS = ("smithy.test#httpRequestTests", "smithy.test#httpResponseTests")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", type=Path, help="Directory of assembled projections.")
    args = parser.parse_args()
    build = json.loads((_ROOT / "codegen/protocol-test/smithy-build.json").read_text())
    projections: dict[str, Any] = {
        "types": {
            "model": "model.json",
            "service": "example#ExampleService",
            "package": "example_types",
            "version": "1.0.0",
            "description": "Example Python codegen output",
        },
        "partitioned-types": {
            "model": "models/partitioned-types.json",
            "service": "example#ExampleService",
            "package": "partitioned_types",
            "version": "1.0.0",
            "description": "Native schema and model stub partition stress fixture",
        },
    }
    provenance: dict[str, Any] = {}
    destination = _INPUTS / "models"
    destination.mkdir(exist_ok=True)
    (destination / "partitioned-types.json").write_text(
        json.dumps(_partition_model(), indent=2) + "\n"
    )
    for name, projection in sorted(build["projections"].items()):
        settings = projection["plugins"]["python-client-codegen"]
        source = (args.models / name / "model/model.json").read_bytes()
        model = json.loads(source)
        # Protocol vectors exercise the client artifact; model traits, documentation,
        # operation references, and member order remain intact.
        _remove_protocol_vectors(model)
        content = json.dumps(model, indent=2) + "\n"
        (destination / f"{name}.json").write_text(content)
        projections[name] = {
            "model": f"models/{name}.json",
            "service": settings["service"],
            "package": settings["module"],
            "version": settings["moduleVersion"],
            "description": f"Native Python types for the {name} projection",
        }
        provenance[name] = {
            "assembled_sha256": hashlib.sha256(source).hexdigest(),
            "fixture_sha256": hashlib.sha256(content.encode()).hexdigest(),
        }
    for name, data in (
        ("projections.json", projections),
        ("models/provenance.json", provenance),
    ):
        (_INPUTS / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _remove_protocol_vectors(model: dict[str, Any]) -> None:
    shapes: dict[str, dict[str, Any]] = model["shapes"]
    for trait in _VECTOR_TRAITS:
        shapes.pop(trait, None)
    for shape in shapes.values():
        _remove_vector_traits(shape)
        members: dict[str, dict[str, Any]] = shape.get("members", {})
        for member in members.values():
            _remove_vector_traits(member)
        for key in ("member", "key", "value"):
            if key in shape:
                _remove_vector_traits(shape[key])


def _remove_vector_traits(node: dict[str, Any]) -> None:
    traits: dict[str, Any] = node.get("traits", {})
    for trait in _VECTOR_TRAITS:
        traits.pop(trait, None)


def _partition_model() -> dict[str, Any]:
    model = json.loads((_INPUTS / "model.json").read_text())
    shapes = model["shapes"]
    shapes["example#GetExampleInput"]["members"]["partitioned"] = {
        "target": "example#PartitionItem000"
    }
    # Cross partition references, plus a recursive pair kept in one schema group.
    for index in range(260):
        next_index = index + 1 if index < 259 else 258
        shapes[f"example#PartitionItem{index:03d}"] = {
            "type": "structure",
            "members": {
                "value": {"target": "smithy.api#String"},
                "next": {"target": f"example#PartitionItem{next_index:03d}"},
            },
        }
    return model


if __name__ == "__main__":
    main()
