#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Shared schemas for shapes built into Smithy's prelude."""

from .schemas import Schema
from .shapes import ShapeID, ShapeType
from .traits import DefaultTrait, UnitTypeTrait

__all__ = [
    "BIG_DECIMAL",
    "BIG_INTEGER",
    "BLOB",
    "BOOLEAN",
    "BYTE",
    "DOCUMENT",
    "DOUBLE",
    "FLOAT",
    "INTEGER",
    "LONG",
    "PRIMITIVE_BOOLEAN",
    "PRIMITIVE_BYTE",
    "PRIMITIVE_DOUBLE",
    "PRIMITIVE_FLOAT",
    "PRIMITIVE_INTEGER",
    "PRIMITIVE_LONG",
    "PRIMITIVE_SHORT",
    "SHORT",
    "STRING",
    "TIMESTAMP",
    "UNIT",
]

BLOB = Schema(
    id=ShapeID("smithy.api#Blob"),
    shape_type=ShapeType.BLOB,
)
"""Schema of the ``smithy.api#Blob`` prelude shape."""

BOOLEAN = Schema(
    id=ShapeID("smithy.api#Boolean"),
    shape_type=ShapeType.BOOLEAN,
)
"""Schema of the ``smithy.api#Boolean`` prelude shape."""

STRING = Schema(
    id=ShapeID("smithy.api#String"),
    shape_type=ShapeType.STRING,
)
"""Schema of the ``smithy.api#String`` prelude shape."""

TIMESTAMP = Schema(
    id=ShapeID("smithy.api#Timestamp"),
    shape_type=ShapeType.TIMESTAMP,
)
"""Schema of the ``smithy.api#Timestamp`` prelude shape."""

BYTE = Schema(
    id=ShapeID("smithy.api#Byte"),
    shape_type=ShapeType.BYTE,
)
"""Schema of the ``smithy.api#Byte`` prelude shape."""

SHORT = Schema(
    id=ShapeID("smithy.api#Short"),
    shape_type=ShapeType.SHORT,
)
"""Schema of the ``smithy.api#Short`` prelude shape."""

INTEGER = Schema(
    id=ShapeID("smithy.api#Integer"),
    shape_type=ShapeType.INTEGER,
)
"""Schema of the ``smithy.api#Integer`` prelude shape."""

LONG = Schema(
    id=ShapeID("smithy.api#Long"),
    shape_type=ShapeType.LONG,
)
"""Schema of the ``smithy.api#Long`` prelude shape."""

FLOAT = Schema(
    id=ShapeID("smithy.api#Float"),
    shape_type=ShapeType.FLOAT,
)
"""Schema of the ``smithy.api#Float`` prelude shape."""

DOUBLE = Schema(
    id=ShapeID("smithy.api#Double"),
    shape_type=ShapeType.DOUBLE,
)
"""Schema of the ``smithy.api#Double`` prelude shape."""

BIG_INTEGER = Schema(
    id=ShapeID("smithy.api#BigInteger"),
    shape_type=ShapeType.BIG_INTEGER,
)
"""Schema of the ``smithy.api#BigInteger`` prelude shape."""

BIG_DECIMAL = Schema(
    id=ShapeID("smithy.api#BigDecimal"),
    shape_type=ShapeType.BIG_DECIMAL,
)
"""Schema of the ``smithy.api#BigDecimal`` prelude shape."""

DOCUMENT = Schema(
    id=ShapeID("smithy.api#Document"),
    shape_type=ShapeType.DOCUMENT,
)
"""Schema of the ``smithy.api#Document`` prelude shape."""

PRIMITIVE_BOOLEAN = Schema(
    id=ShapeID("smithy.api#PrimitiveBoolean"),
    shape_type=ShapeType.BOOLEAN,
    traits=[DefaultTrait(False)],
)
"""Schema of the ``smithy.api#PrimitiveBoolean`` prelude shape."""

PRIMITIVE_BYTE = Schema(
    id=ShapeID("smithy.api#PrimitiveByte"),
    shape_type=ShapeType.BYTE,
    traits=[DefaultTrait(0)],
)
"""Schema of the ``smithy.api#PrimitiveByte`` prelude shape."""

PRIMITIVE_SHORT = Schema(
    id=ShapeID("smithy.api#PrimitiveShort"),
    shape_type=ShapeType.SHORT,
    traits=[DefaultTrait(0)],
)
"""Schema of the ``smithy.api#PrimitiveShort`` prelude shape."""

PRIMITIVE_INTEGER = Schema(
    id=ShapeID("smithy.api#PrimitiveInteger"),
    shape_type=ShapeType.INTEGER,
    traits=[DefaultTrait(0)],
)
"""Schema of the ``smithy.api#PrimitiveInteger`` prelude shape."""

PRIMITIVE_LONG = Schema(
    id=ShapeID("smithy.api#PrimitiveLong"),
    shape_type=ShapeType.LONG,
    traits=[DefaultTrait(0)],
)
"""Schema of the ``smithy.api#PrimitiveLong`` prelude shape."""

PRIMITIVE_FLOAT = Schema(
    id=ShapeID("smithy.api#PrimitiveFloat"),
    shape_type=ShapeType.FLOAT,
    traits=[DefaultTrait(0)],
)
"""Schema of the ``smithy.api#PrimitiveFloat`` prelude shape."""

PRIMITIVE_DOUBLE = Schema(
    id=ShapeID("smithy.api#PrimitiveDouble"),
    shape_type=ShapeType.DOUBLE,
    traits=[DefaultTrait(0)],
)
"""Schema of the ``smithy.api#PrimitiveDouble`` prelude shape."""

UNIT = Schema(
    id=ShapeID("smithy.api#Unit"),
    shape_type=ShapeType.STRUCTURE,
    traits=[UnitTypeTrait()],
)
"""Schema of the ``smithy.api#Unit`` prelude shape."""
