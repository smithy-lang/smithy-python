#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Shared schemas for shapes built into Smithy's prelude."""

from .schemas import Schema
from .shapes import ShapeID, ShapeType
from .traits import Trait

BLOB = Schema(
    id=ShapeID("smithy.api#Blob"),
    type=ShapeType.BLOB,
)

BOOLEAN = Schema(
    id=ShapeID("smithy.api#Boolean"),
    type=ShapeType.BOOLEAN,
)

STRING = Schema(
    id=ShapeID("smithy.api#String"),
    type=ShapeType.STRING,
)

TIMESTAMP = Schema(
    id=ShapeID("smithy.api#Timestamp"),
    type=ShapeType.TIMESTAMP,
)

BYTE = Schema(
    id=ShapeID("smithy.api#Byte"),
    type=ShapeType.BYTE,
)

SHORT = Schema(
    id=ShapeID("smithy.api#Short"),
    type=ShapeType.SHORT,
)

INTEGER = Schema(
    id=ShapeID("smithy.api#Integer"),
    type=ShapeType.INTEGER,
)

LONG = Schema(
    id=ShapeID("smithy.api#Long"),
    type=ShapeType.LONG,
)

FLOAT = Schema(
    id=ShapeID("smithy.api#Float"),
    type=ShapeType.FLOAT,
)

DOUBLE = Schema(
    id=ShapeID("smithy.api#Double"),
    type=ShapeType.DOUBLE,
)

BIG_INTEGER = Schema(
    id=ShapeID("smithy.api#BigInteger"),
    type=ShapeType.BIG_INTEGER,
)

BIG_DECIMAL = Schema(
    id=ShapeID("smithy.api#BigDecimal"),
    type=ShapeType.BIG_DECIMAL,
)

DOCUMENT = Schema(
    id=ShapeID("smithy.api#Document"),
    type=ShapeType.DOCUMENT,
)


_DEFAULT = ShapeID("smithy.api#default")


PRIMITIVE_BOOLEAN = Schema(
    id=ShapeID("smithy.api#PrimitiveBoolean"),
    type=ShapeType.BOOLEAN,
    traits=[Trait(id=_DEFAULT, value=False)],
)

PRIMITIVE_BYTE = Schema(
    id=ShapeID("smithy.api#PrimitiveByte"),
    type=ShapeType.BYTE,
    traits=[Trait(id=_DEFAULT, value=0)],
)

PRIMITIVE_SHORT = Schema(
    id=ShapeID("smithy.api#PrimitiveShort"),
    type=ShapeType.SHORT,
    traits=[Trait(id=_DEFAULT, value=0)],
)

PRIMITIVE_INTEGER = Schema(
    id=ShapeID("smithy.api#PrimitiveInteger"),
    type=ShapeType.INTEGER,
    traits=[Trait(id=_DEFAULT, value=0)],
)

PRIMITIVE_LONG = Schema(
    id=ShapeID("smithy.api#PrimitiveLong"),
    type=ShapeType.LONG,
    traits=[Trait(id=_DEFAULT, value=0)],
)

PRIMITIVE_FLOAT = Schema(
    id=ShapeID("smithy.api#PrimitiveFloat"),
    type=ShapeType.FLOAT,
    traits=[Trait(id=_DEFAULT, value=0.0)],
)

PRIMITIVE_DOUBLE = Schema(
    id=ShapeID("smithy.api#PrimitiveDouble"),
    type=ShapeType.DOUBLE,
    traits=[Trait(id=_DEFAULT, value=0.0)],
)

UNIT = Schema(
    id=ShapeID("smithy.api#Unit"),
    type=ShapeType.DOUBLE,
    traits=[Trait(id=ShapeID("smithy.api#UnitTypeTrait"))],
)
