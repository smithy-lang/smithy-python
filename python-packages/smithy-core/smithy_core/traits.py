from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .shapes import ShapeID
    from .types import Document


@dataclass(kw_only=True, frozen=True)
class Trait:
    """A component that can be attached to a schema to describe additional information
    about it.

    :param id: The ID of the trait.
    :param value: The document value of the trait.
    """

    id: "ShapeID"
    value: "Document"
