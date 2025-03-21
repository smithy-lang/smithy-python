#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Shared schemas for shapes built into Smithy's prelude."""

from .schemas import Schema
from .shapes import ShapeID, ShapeType
from .traits import DefaultTrait, UnitTypeTrait

BLOB = Schema(
    id=ShapeID("smithy.api#Blob"),
    shape_type=ShapeType.BLOB,
)

BOOLEAN = Schema(
    id=ShapeID("smithy.api#Boolean"),
    shape_type=ShapeType.BOOLEAN,
)

STRING = Schema(
    id=ShapeID("smithy.api#String"),
    shape_type=ShapeType.STRING,
)

TIMESTAMP = Schema(
    id=ShapeID("smithy.api#Timestamp"),
    shape_type=ShapeType.TIMESTAMP,
)

BYTE = Schema(
    id=ShapeID("smithy.api#Byte"),
    shape_type=ShapeType.BYTE,
)

SHORT = Schema(
    id=ShapeID("smithy.api#Short"),
    shape_type=ShapeType.SHORT,
)

INTEGER = Schema(
    id=ShapeID("smithy.api#Integer"),
    shape_type=ShapeType.INTEGER,
)

LONG = Schema(
    id=ShapeID("smithy.api#Long"),
    shape_type=ShapeType.LONG,
)

FLOAT = Schema(
    id=ShapeID("smithy.api#Float"),
    shape_type=ShapeType.FLOAT,
)

DOUBLE = Schema(
    id=ShapeID("smithy.api#Double"),
    shape_type=ShapeType.DOUBLE,
)

BIG_INTEGER = Schema(
    id=ShapeID("smithy.api#BigInteger"),
    shape_type=ShapeType.BIG_INTEGER,
)

BIG_DECIMAL = Schema(
    id=ShapeID("smithy.api#BigDecimal"),
    shape_type=ShapeType.BIG_DECIMAL,
)

DOCUMENT = Schema(
    id=ShapeID("smithy.api#Document"),
    shape_type=ShapeType.DOCUMENT,
)

PRIMITIVE_BOOLEAN = Schema(
    id=ShapeID("smithy.api#PrimitiveBoolean"),
    shape_type=ShapeType.BOOLEAN,
    traits=[DefaultTrait(False)],
)

PRIMITIVE_BYTE = Schema(
    id=ShapeID("smithy.api#PrimitiveByte"),
    shape_type=ShapeType.BYTE,
    traits=[DefaultTrait(0)],
)

PRIMITIVE_SHORT = Schema(
    id=ShapeID("smithy.api#PrimitiveShort"),
    shape_type=ShapeType.SHORT,
    traits=[DefaultTrait(0)],
)

PRIMITIVE_INTEGER = Schema(
    id=ShapeID("smithy.api#PrimitiveInteger"),
    shape_type=ShapeType.INTEGER,
    traits=[DefaultTrait(0)],
)

PRIMITIVE_LONG = Schema(
    id=ShapeID("smithy.api#PrimitiveLong"),
    shape_type=ShapeType.LONG,
    traits=[DefaultTrait(0)],
)

PRIMITIVE_FLOAT = Schema(
    id=ShapeID("smithy.api#PrimitiveFloat"),
    shape_type=ShapeType.FLOAT,
    traits=[DefaultTrait(0)],
)

PRIMITIVE_DOUBLE = Schema(
    id=ShapeID("smithy.api#PrimitiveDouble"),
    shape_type=ShapeType.DOUBLE,
    traits=[DefaultTrait(0)],
)

UNIT = Schema(
    id=ShapeID("smithy.api#Unit"),
    shape_type=ShapeType.STRUCTURE,
    traits=[UnitTypeTrait()],
)
