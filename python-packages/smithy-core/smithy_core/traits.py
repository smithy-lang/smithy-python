from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .documents import DocumentValue
    from .shapes import ShapeID


@dataclass(kw_only=True, frozen=True)
class Trait:
    """A component that can be attached to a schema to describe additional information
    about it.

    :param id: The ID of the trait.
    :param value: The document value of the trait.
    """

    id: "ShapeID"
    value: "DocumentValue" = field(default_factory=dict)
