from typing import TypeAlias

Document: TypeAlias = (
    dict[str, "Document"] | list["Document"] | str | int | float | bool | None
)
