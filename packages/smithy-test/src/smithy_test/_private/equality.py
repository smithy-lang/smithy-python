#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
import dataclasses
import math
from typing import Any


def deep_equal(a: object, b: object) -> bool:
    """Structural equality for deserialized shapes that treats ``NaN == NaN``.

    Protocol-test response vectors can carry NaN/Infinity floats, where plain ``==``
    reports a spurious inequality (``float('nan') != float('nan')``). Recurses through
    dataclasses, sequences, and mappings; falls back to ``==`` for everything else.
    """
    if isinstance(a, float) and isinstance(b, float):
        return a == b or (math.isnan(a) and math.isnan(b))
    if dataclasses.is_dataclass(a) and dataclasses.is_dataclass(b):
        if type(a) is not type(b):
            return False
        for f in dataclasses.fields(a):
            av: object = getattr(a, f.name)
            bv: object = getattr(b, f.name)
            if not deep_equal(av, bv):
                return False
        return True
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        a_seq: tuple[Any, ...] = tuple(a)  # type: ignore[arg-type]
        b_seq: tuple[Any, ...] = tuple(b)  # type: ignore[arg-type]
        if len(a_seq) != len(b_seq):
            return False
        return all(deep_equal(x, y) for x, y in zip(a_seq, b_seq))
    if isinstance(a, dict) and isinstance(b, dict):
        a_map: dict[Any, Any] = a  # type: ignore[assignment]
        b_map: dict[Any, Any] = b  # type: ignore[assignment]
        if a_map.keys() != b_map.keys():
            return False
        return all(deep_equal(a_map[k], b_map[k]) for k in a_map)
    return a == b
