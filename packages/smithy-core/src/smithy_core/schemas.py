#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, NotRequired, Required, Self, TypedDict, overload

from .exceptions import ExpectationNotMetException, SmithyException
from .shapes import ShapeID, ShapeType
from .traits import DynamicTrait, IdempotencyTokenTrait, StreamingTrait, Trait

if TYPE_CHECKING:
    from .deserializers import DeserializeableShape
    from .documents import TypeRegistry
    from .serializers import SerializeableShape


@dataclass(kw_only=True, frozen=True, init=False)
class Schema:
    """Describes a shape, its traits, and its members."""

    id: ShapeID
    shape_type: ShapeType
    traits: dict[ShapeID, "Trait | DynamicTrait"] = field(default_factory=dict)
    members: dict[str, "Schema"] = field(default_factory=dict)
    member_target: "Schema | None" = None
    member_index: int | None = None

    def __init__(
        self,
        *,
        id: ShapeID,
        shape_type: ShapeType,
        traits: list["Trait | DynamicTrait"]
        | dict[ShapeID, "Trait | DynamicTrait"]
        | None = None,
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
                f"member_name: {id.member!r}, member_target: "
                f"{member_target!r}, member_index: {member_index!r}"
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
                m: dict[str, Schema] = {}
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

    @overload
    def get_trait[T: "Trait"](self, t: type[T]) -> T | None: ...

    @overload
    def get_trait(self, t: ShapeID) -> "Trait | DynamicTrait | None": ...

    def get_trait(self, t: "type[Trait] | ShapeID") -> "Trait | DynamicTrait | None":
        """Get a trait based on its ShapeID or class.

        :returns: A Trait if the trait class is known, a DynamicTrait if it isn't, or
            None if the trait is not present on the Schema.
        """
        if isinstance(t, ShapeID):
            return self.traits.get(t)

        result = self.traits.get(t.id)

        # If the trait wasn't known when the schema was created, but is known now, go
        # ahead and convert it.
        if isinstance(result, DynamicTrait):
            result = t(result)
            self.traits[t.id] = result

        return result

    @overload
    def expect_trait[T: "Trait"](self, t: type[T]) -> T: ...

    @overload
    def expect_trait(self, t: ShapeID) -> "Trait | DynamicTrait": ...

    def expect_trait(self, t: "type[Trait] | ShapeID") -> "Trait | DynamicTrait":
        """Get a trait based on its ShapeID or class.

        :returns: A Trait if the trait class is known, a DynamicTrait if it isn't.
        """
        id = t if isinstance(t, ShapeID) else t.id
        return self.traits[id]

    def __contains__(self, item: Any):
        """Returns whether the schema has the given member or trait."""
        match item:
            case type():
                if issubclass(item, Trait):
                    return item.id in self.traits
                return False
            case ShapeID():
                if (member := item.member) is not None:
                    if self.id.with_member(member) == item:
                        return member in self.members
                    return False
                return item in self.traits
            case str():
                return item in self.members
            case _:
                return False

    @classmethod
    def collection(
        cls,
        *,
        id: ShapeID,
        shape_type: ShapeType = ShapeType.STRUCTURE,
        traits: list["Trait | DynamicTrait"] | None = None,
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
        struct_members: dict[str, Schema] = {}
        if members:
            for k in members.keys():
                struct_members[k] = cls.member(
                    id=id.with_member(k),
                    target=members[k]["target"],
                    index=members[k]["index"],
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
        target: "Schema",
        index: int,
        member_traits: list["Trait | DynamicTrait"] | None = None,
    ) -> "Schema":
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
    index: Required[int]
    traits: NotRequired[list["Trait | DynamicTrait"]]


@dataclass(kw_only=True, frozen=True)
class APIOperation[I: "SerializeableShape", O: "DeserializeableShape"]:
    """A modeled Smithy operation."""

    input: type[I]
    """The input type of the operation."""

    output: type[O]
    """The output type of the operation."""

    schema: Schema
    """The schema of the operation."""

    input_schema: Schema
    """The schema of the operation's input shape."""

    output_schema: Schema
    """The schema of the operation's output shape."""

    error_registry: "TypeRegistry"
    """A TypeRegistry used to create errors."""

    effective_auth_schemes: Sequence[ShapeID]
    """A list of effective auth schemes for the operation."""

    @property
    def idempotency_token_member(self) -> Schema | None:
        """The input schema member that serves as the idempotency token."""
        for member in self.input_schema.members.values():
            if member.get_trait(IdempotencyTokenTrait) is not None:
                return member
        return None

    @property
    def input_stream_member(self) -> Schema | None:
        """The input schema member that contains an event stream or data stream."""
        for member in self.input_schema.members.values():
            if member.get_trait(StreamingTrait) is not None:
                return member
        return None

    @property
    def output_stream_member(self) -> Schema | None:
        """The output schema member that contains an event stream or data stream."""
        for member in self.output_schema.members.values():
            if member.get_trait(StreamingTrait) is not None:
                return member
        return None
