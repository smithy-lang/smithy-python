# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""The embedded subset of the Smithy prelude.

Only the shapes that model members and relationships can target are embedded.
Trait-definition shapes are intentionally omitted: trait keys are not resolved
as references, and later stages never generate or inspect trait definitions.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Final

_P: Final = "smithy.api#"

_SIMPLE: Final = (
    ("String", "string"),
    ("Blob", "blob"),
    ("BigInteger", "bigInteger"),
    ("BigDecimal", "bigDecimal"),
    ("Timestamp", "timestamp"),
    ("Document", "document"),
    ("Boolean", "boolean"),
    ("Byte", "byte"),
    ("Short", "short"),
    ("Integer", "integer"),
    ("Long", "long"),
    ("Float", "float"),
    ("Double", "double"),
)

_PRIMITIVE: Final = (
    ("PrimitiveBoolean", "boolean", False),
    ("PrimitiveByte", "byte", 0),
    ("PrimitiveShort", "short", 0),
    ("PrimitiveInteger", "integer", 0),
    ("PrimitiveLong", "long", 0),
    ("PrimitiveFloat", "float", 0),
    ("PrimitiveDouble", "double", 0),
)


def prelude_ast() -> Mapping[str, Mapping[str, Any]]:
    """Return a fresh JSON AST ``shapes`` mapping for the embedded prelude."""
    shapes: dict[str, Mapping[str, Any]] = {}
    for name, type_name in _SIMPLE:
        shapes[_P + name] = {"type": type_name}
    for name, type_name, default in _PRIMITIVE:
        shapes[_P + name] = {
            "type": type_name,
            "traits": {_P + "default": default},
        }
    shapes[_P + "Unit"] = {
        "type": "structure",
        "members": {},
        "traits": {_P + "unitType": {}},
    }
    return MappingProxyType(shapes)
