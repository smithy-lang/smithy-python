from collections.abc import Mapping, Sequence
from typing import TypeAlias

Document: TypeAlias = (
    Mapping[str, "Document"] | Sequence["Document"] | str | int | float | bool | None
)
