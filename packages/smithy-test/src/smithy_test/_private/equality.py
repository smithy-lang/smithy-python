#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import cast


def deep_equal(a: object, b: object) -> bool:
    """Structural equality for deserialized shapes that treats ``NaN == NaN``."""
    if isinstance(a, float) and isinstance(b, float):
        return a == b or (math.isnan(a) and math.isnan(b))
    if dataclasses.is_dataclass(a) and dataclasses.is_dataclass(b):
        if type(a) is not type(b):
            return False
        return all(
            deep_equal(getattr(a, f.name), getattr(b, f.name))
            for f in dataclasses.fields(a)
        )
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        a_seq = cast(Sequence[object], a)
        b_seq = cast(Sequence[object], b)
        return len(a_seq) == len(b_seq) and all(
            deep_equal(x, y) for x, y in zip(a_seq, b_seq)
        )
    if isinstance(a, dict) and isinstance(b, dict):
        a_map = cast(Mapping[object, object], a)
        b_map = cast(Mapping[object, object], b)
        return a_map.keys() == b_map.keys() and all(
            deep_equal(a_map[k], b_map[k]) for k in a_map
        )
    # bool subclasses int; the subclass check would admit 1 == True without this.
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return (isinstance(a, type(b)) or isinstance(b, type(a))) and a == b  # pyright: ignore[reportUnknownArgumentType]
