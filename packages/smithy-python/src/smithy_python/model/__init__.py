# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""The Smithy semantic model used by the Python code generator.

Use :func:`load_model` to parse a Smithy JSON AST into a :class:`Model`. The
loaded model is mixin-flattened, has ``apply`` entries merged, includes the
embedded Smithy prelude, and preserves the order of everything in the input.
"""

from ..exceptions import InvalidShapeIdError, ModelError, ShapeNotFoundError
from ._loader import load_model
from ._model import Model
from ._shape_id import ShapeId
from ._shapes import (
    EnumShape,
    IntEnumShape,
    ListShape,
    MapShape,
    MemberShape,
    Node,
    OperationShape,
    ResourceShape,
    ServiceShape,
    Shape,
    ShapeType,
    SimpleShape,
    StructureShape,
    UnionShape,
)

__all__ = [
    "EnumShape",
    "IntEnumShape",
    "InvalidShapeIdError",
    "ListShape",
    "MapShape",
    "MemberShape",
    "Model",
    "ModelError",
    "Node",
    "OperationShape",
    "ResourceShape",
    "ServiceShape",
    "Shape",
    "ShapeId",
    "ShapeNotFoundError",
    "ShapeType",
    "SimpleShape",
    "StructureShape",
    "UnionShape",
    "load_model",
]
