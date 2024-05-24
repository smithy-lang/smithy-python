from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, NotRequired, Required, Self, TypedDict

from .exceptions import ExpectationNotMetException, SmithyException
from .shapes import ShapeID, ShapeType

if TYPE_CHECKING:
    from .traits import Trait


@dataclass(kw_only=True, frozen=True, init=False)
class Schema:
    """Describes a shape, its traits, and its members."""

    id: ShapeID
    shape_type: ShapeType
    traits: dict[ShapeID, "Trait"] = field(default_factory=dict)
    members: dict[str, "Schema"] = field(default_factory=dict)
    member_target: "Schema | None" = None
    member_index: int | None = None

    def __init__(
        self,
        *,
        id: ShapeID,
        shape_type: ShapeType,
        traits: list["Trait"] | dict[ShapeID, "Trait"] | None = None,
        members: list["Schema"] | dict[str, "Schema"] | None = None,
        member_target: "Schema | None" = None,
        member_index: int | None = None,
    ) -> None:
        """Initialize a schema.

        :param id: The ID of the shape.
        :param shape_type: The type of the shape.
        :param traits: Traits applied to the shape, which describe additional metadata.
        :param members: Members of the shape. These correspond to list contents,
            dataclass properties, map keys/values, and union variants.
        :param member_target: The schema that the member points to, if the shape is the
            MEMBER type.
        :param member_index: The index of the member, if the shape is the MEMBER type.
            This is used for faster match checks when all members of a shape are known.
        """
        _member_props = [
            id.member is not None,
            member_target is not None,
            member_index is not None,
        ]
        if any(_member_props) and not all(_member_props):
            raise SmithyException(
                "If any member property is set, all member properties must be set. "
                f"member_name: {repr(id.member)}, member_target: "
                f"{repr(member_target)}, member_index: {repr(member_index)}"
            )

        # setattr is required because the class is frozen
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "shape_type", shape_type)

        if traits:
            if isinstance(traits, list):
                traits = {t.id: t for t in traits}
        else:
            traits = {}
        object.__setattr__(self, "traits", traits)

        if members:
            if isinstance(members, list):
                m: dict[str, "Schema"] = {}
                for member in members:
                    m[member.expect_member_name()] = member
                members = m
        else:
            members = {}
        object.__setattr__(self, "members", members)

        if member_target is not None:
            object.__setattr__(self, "member_target", member_target)

        if member_index is not None:
            object.__setattr__(self, "member_index", member_index)

    @property
    def member_name(self) -> str | None:
        """The name of the member, if the shape is the MEMBER type."""
        return self.id.member

    def expect_member_name(self) -> str:
        """Assert the schema is a member schema and return its member name.

        :raises ExpectationNotMetException: If member_name wasn't set.
        :returns: Returns the member name.
        """
        return self.id.expect_member()

    def expect_member_target(self) -> "Schema":
        """Assert the schema is a member schema and return its target.

        If the target is a class containing a schema, the schema is extracted and
        returned.

        :raises ExpectationNotMetException: If member_target wasn't set.
        :returns: Returns the target schema.
        """
        if self.member_target is None:
            raise ExpectationNotMetException(
                "Expected member_target to be set, but was None."
            )
        return self.member_target

    def expect_member_index(self) -> int:
        """Assert the schema is a member schema and return its member index.

        :raises ExpectationNotMetException: If member_index wasn't set.
        :returns: Returns the member index.
        """
        if self.member_index is None:
            raise ExpectationNotMetException(
                "Expected member_index to be set, but was None."
            )
        return self.member_index

    @classmethod
    def collection(
        cls,
        *,
        id: ShapeID,
        shape_type: ShapeType = ShapeType.STRUCTURE,
        traits: list["Trait"] | None = None,
        members: Mapping[str, "MemberSchema"] | None = None,
    ) -> Self:
        """Create a schema for a collection shape.

        :param id: The ID of the shape.
        :param shape_type: The type of the shape. Defaults to STRUCTURE.
        :param traits: Traits applied to the shape, which describe additional metadata.
        :param members: Members of the shape. These correspond to list contents, dataclass
            properties, map keys/values, and union variants. In contrast to the main
            constructor, this is a dict of member names to a simplified dict containing
            only ``traits`` and a ``target``. Member schemas will be generated from this.
        """
        struct_members: dict[str, "Schema"] = {}
        if members:
            for i, k in enumerate(members.keys()):
                struct_members[k] = cls.member(
                    id=id.with_member(k),
                    target=members[k]["target"],
                    index=i,
                    member_traits=members[k].get("traits"),
                )

        result = cls(
            id=id,
            shape_type=shape_type,
            traits=traits,
            members=struct_members,
        )
        return result

    @classmethod
    def member(
        cls,
        id: ShapeID,
        target: Self,
        index: int,
        member_traits: list["Trait"] | None = None,
    ) -> Self:
        """Create a schema for a member shape.

        Member schemas are largely copies of the schemas they target to make it easier
        to use them. They contain all the members of the target and all of the traits of
        the target. Any traits provided to this method, will override traits of the same
        type on the member schema.

        :param id: The member's id.
        :param target: The schema the member is targeting.
        :param index: The member's index.
        """
        id.expect_member()
        if target.member_target is not None:
            raise ExpectationNotMetException("Member targets must not be members.")
        resolved_traits = target.traits.copy()
        if member_traits:
            resolved_traits.update({t.id: t for t in member_traits})
        return replace(
            target,
            id=id,
            traits=resolved_traits,
            member_target=target,
            member_index=index,
        )


class MemberSchema(TypedDict):
    """A simplified schema for members.

    This is only used for :ref:`Schema.collection`.

    :param target: The target of the member.
    :param traits: An optional list of traits for the member.
    """

    target: Required[Schema]
    traits: NotRequired[list["Trait"]]
