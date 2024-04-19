from enum import Enum
from typing import Self

from .exceptions import ExpectationNotMetException, SmithyException


class ShapeID:
    """An identifier for a Smithy shape."""

    _id: str
    _namespace: str
    _name: str
    _member: str | None = None

    def __init__(self, id: str) -> None:
        """Initialize a ShapeID.

        :param id: The string representation of the ID.
        """
        self._id = id
        if "#" not in id:
            raise SmithyException(f"Invalid shape id: {id}")
        self._namespace, self._name = id.split("#", 1)
        if not self.namespace or not self._name:
            raise SmithyException(f"Invalid shape id: {id}")

        if len(split_name := self._name.split("$", 1)) > 1:
            self._name, self._member = split_name
            if not self._name or not self._member:
                raise SmithyException(f"Invalid shape id: {id}")

    @property
    def namespace(self) -> str:
        """The namespace of the shape."""
        return self._namespace

    @property
    def name(self) -> str:
        """The name of the shape, or the name of the containing shape if the shape is a
        member."""
        return self._name

    @property
    def member(self) -> str | None:
        """The member name of the shape.

        This is only set for member shapes.
        """
        return self._member

    def expect_member(self) -> str:
        """Assert the member name is set and get it.

        :raises ExpectationNotMetException: If member wasn't set.
        :returns: Returns the member name.
        """
        if self.member is None:
            raise ExpectationNotMetException("Expected member to be set, but was None.")
        return self.member

    def with_member(self, member: str) -> "ShapeID":
        """Create a new shape id from the current id with the given member name.

        :param member: The member name to use on the new shape id.
        """
        return ShapeID.from_parts(
            namespace=self.namespace,
            name=self.name,
            member=member,
        )

    def __str__(self) -> str:
        return self._id

    def __repr__(self) -> str:
        return f"ShapeId({self._id})"

    def __eq__(self, other: object) -> bool:
        return self._id == str(other)

    def __hash__(self) -> int:
        return hash(self._id)

    @classmethod
    def from_parts(
        cls, *, namespace: str, name: str, member: str | None = None
    ) -> Self:
        """Initialize a ShapeID from component parts instead of a string whole.

        :param namesapce: The shape's namespace.
        :param name: The shape's individual name.
        :param member: The shape member's name. Only set for member shapes.
        """
        if member is not None:
            return cls(f"{namespace}#{name}${member}")
        return cls(f"{namespace}#{name}")


class ShapeType(Enum):
    """The type of data that a shape represents."""

    BLOB = 1
    BOOLEAN = 2
    STRING = 3
    TIMESTAMP = 4
    BYTE = 5
    SHORT = 6
    INTEGER = 7
    LONG = 8
    FLOAT = 9
    DOUBLE = 10
    BIG_INTEGER = 11
    BIG_DECIMAL = 12
    DOCUMENT = 13
    ENUM = 14
    INT_ENUM = 15

    LIST = 16
    MAP = 17
    STRUCTURE = 18
    UNION = 19

    MEMBER = 20

    # We won't acutally be using these, probably
    # SERVICE = 21
    # RESOURCE = 22
    # OPERATION = 23
