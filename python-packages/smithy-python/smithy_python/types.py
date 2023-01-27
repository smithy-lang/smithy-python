from typing import Mapping, Sequence, TypeAlias

Document: TypeAlias = (
    Mapping[str, "Document"] | Sequence["Document"] | str | int | float | bool | None
)
