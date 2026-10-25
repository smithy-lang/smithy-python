# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Smithy selector parsing and evaluation."""

from __future__ import annotations

import re
from collections import deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Final, NoReturn, Self, cast

from .exceptions import SelectorSyntaxError
from .model import (
    EnumShape,
    IntEnumShape,
    MemberShape,
    Model,
    Node,
    OperationShape,
    ResourceShape,
    ServiceShape,
    Shape,
    ShapeId,
    ShapeType,
)

type _Receiver = Callable[[Shape], bool]
type _ValueData = (
    None
    | bool
    | int
    | float
    | str
    | Shape
    | ShapeId
    | tuple[Node, ...]
    | tuple[_Value, ...]
    | Mapping[str, Node]
)

_IDENTIFIER: Final = re.compile(r"(?:[A-Za-z]|_+[A-Za-z0-9])[A-Za-z0-9_]*")
_NUMBER: Final = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")
_NUMBERS: Final = frozenset(
    {
        ShapeType.BYTE,
        ShapeType.SHORT,
        ShapeType.INTEGER,
        ShapeType.LONG,
        ShapeType.FLOAT,
        ShapeType.DOUBLE,
        ShapeType.BIG_DECIMAL,
        ShapeType.BIG_INTEGER,
    }
)
_SIMPLE: Final = frozenset(
    {
        ShapeType.BLOB,
        ShapeType.BOOLEAN,
        ShapeType.STRING,
        ShapeType.TIMESTAMP,
        ShapeType.BYTE,
        ShapeType.SHORT,
        ShapeType.INTEGER,
        ShapeType.LONG,
        ShapeType.FLOAT,
        ShapeType.DOCUMENT,
        ShapeType.DOUBLE,
        ShapeType.BIG_DECIMAL,
        ShapeType.BIG_INTEGER,
        ShapeType.ENUM,
        ShapeType.INT_ENUM,
    }
)
_AGGREGATE: Final = frozenset(
    {ShapeType.LIST, ShapeType.MAP, ShapeType.STRUCTURE, ShapeType.UNION}
)
_SERVICE: Final = frozenset(
    {ShapeType.SERVICE, ShapeType.RESOURCE, ShapeType.OPERATION}
)
_TOPDOWN_RELATIONSHIPS: Final = frozenset(
    {
        "operation",
        "resource",
        "collectionOperation",
        "create",
        "put",
        "read",
        "update",
        "delete",
        "list",
    }
)
_ENUM_TRAIT: Final = ShapeId("smithy.api", "enum")
_TRAIT_TRAIT: Final = ShapeId("smithy.api", "trait")
_AUTH_DEFINITION_TRAIT: Final = ShapeId("smithy.api", "authDefinition")
_PRELUDE_AUTH_TRAITS: Final = frozenset(
    {
        ShapeId("smithy.api", "httpApiKeyAuth"),
        ShapeId("smithy.api", "httpBasicAuth"),
        ShapeId("smithy.api", "httpBearerAuth"),
        ShapeId("smithy.api", "httpDigestAuth"),
    }
)
_PRELUDE_TRAIT_TYPES: Final[Mapping[ShapeId, ShapeType]] = {
    ShapeId("smithy.api", name): shape_type
    for shape_type, names in (
        (
            ShapeType.STRING,
            (
                "documentation",
                "httpHeader",
                "httpPrefixHeaders",
                "httpQuery",
                "jsonName",
                "mediaType",
                "pattern",
                "resourceIdentifier",
                "since",
                "title",
                "xmlName",
            ),
        ),
        (
            ShapeType.LIST,
            (
                "auth",
                "createsResources",
                "deletesResources",
                "enum",
                "examples",
                "putsResources",
                "readsResources",
                "references",
                "suppress",
                "tags",
                "updatesResources",
            ),
        ),
        (
            ShapeType.MAP,
            ("externalDocumentation", "traitValidators", "unstableFeatures"),
        ),
        (ShapeType.DOCUMENT, ("default", "enumValue")),
        (ShapeType.ENUM, ("error", "timestampFormat")),
        (ShapeType.INTEGER, ("httpError",)),
    )
    for name in names
}


@dataclass(frozen=True, slots=True)
class Selector:
    """An immutable parsed Smithy selector."""

    source: str
    _expression: _Expression
    _roots: tuple[_Expression, ...] = ()
    _variable_names: tuple[str, ...] = ()

    @classmethod
    def identity(cls) -> Self:
        """Return a selector that retains every starting shape."""
        return cls("*", _IDENTITY)

    @classmethod
    def parse(cls, source: str) -> Self:
        """Parse a Smithy selector expression."""
        return cast(Self, _Parser(source).parse(cls))

    def select(self, model: Model) -> frozenset[ShapeId]:
        """Evaluate this selector and return the matching shape IDs."""
        graph = _Graph(model)
        roots: list[frozenset[Shape]] = []
        for expression in self._roots:
            context = _Context(graph, roots, self._variable_names)
            roots.append(
                context.collect(expression, graph.shapes, reset_variables=True)
            )

        context = _Context(graph, roots, self._variable_names)
        return frozenset(
            shape.id
            for shape in context.collect(
                self._expression, graph.shapes, reset_variables=True
            )
        )

    @property
    def is_identity(self) -> bool:
        """Whether this selector retains every starting shape."""
        return self._expression is _IDENTITY and not self._roots

    def __str__(self) -> str:
        return self.source


class _Expression:
    __slots__ = ()

    def push(
        self, context: _Context, shape: Shape, receiver: _Receiver
    ) -> bool:  # pragma: no cover - abstract dispatch
        raise NotImplementedError


class _Identity(_Expression):
    __slots__ = ()

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        return receiver(shape)


_IDENTITY: Final = _Identity()


@dataclass(frozen=True, slots=True)
class _SequenceExpression(_Expression):
    expressions: tuple[_Expression, ...]

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        def apply(index: int, current: Shape) -> bool:
            if index == len(self.expressions):
                return receiver(current)
            return self.expressions[index].push(
                context, current, lambda result: apply(index + 1, result)
            )

        return apply(0, shape)


@dataclass(frozen=True, slots=True)
class _TypeExpression(_Expression):
    types: frozenset[ShapeType]
    aliases: frozenset[ShapeType] = frozenset()

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        if shape.type in self.types or shape.type in self.aliases:
            return receiver(shape)
        return False


_TYPE_EXPRESSIONS: Final[Mapping[str, _TypeExpression]] = {
    **{
        shape_type.value: _TypeExpression(frozenset({shape_type}))
        for shape_type in ShapeType
    },
    "number": _TypeExpression(_NUMBERS),
    "simpleType": _TypeExpression(_SIMPLE),
    "collection": _TypeExpression(frozenset({ShapeType.LIST})),
    "set": _TypeExpression(frozenset({ShapeType.LIST})),
    "aggregateType": _TypeExpression(_AGGREGATE),
    "serviceType": _TypeExpression(_SERVICE),
    "dataType": _TypeExpression(_SIMPLE | _AGGREGATE),
    "string": _TypeExpression(
        frozenset({ShapeType.STRING}), frozenset({ShapeType.ENUM})
    ),
    "integer": _TypeExpression(
        frozenset({ShapeType.INTEGER}), frozenset({ShapeType.INT_ENUM})
    ),
}


@dataclass(frozen=True, slots=True)
class _AnyExpression(_Expression):
    expressions: tuple[_Expression, ...]

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        for expression in self.expressions:
            if expression.push(context, shape, receiver):
                return True
        return False


@dataclass(frozen=True, slots=True)
class _TestExpression(_Expression):
    expressions: tuple[_Expression, ...]

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        if any(context.receives(expression, shape) for expression in self.expressions):
            return receiver(shape)
        return False


@dataclass(frozen=True, slots=True)
class _NotExpression(_Expression):
    expression: _Expression

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        if not context.receives(self.expression, shape):
            return receiver(shape)
        return False


@dataclass(frozen=True, slots=True)
class _InExpression(_Expression):
    expression: _Expression

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        matched = False

        def find(result: Shape) -> bool:
            nonlocal matched
            matched = result is shape
            return matched

        self.expression.push(context, shape, find)
        return receiver(shape) if matched else False


@dataclass(frozen=True, slots=True)
class _VariableStoreExpression(_Expression):
    slot: int
    expression: _Expression

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        context.variables[self.slot] = context.collect(self.expression, (shape,))
        return receiver(shape)


@dataclass(frozen=True, slots=True)
class _VariableGetExpression(_Expression):
    slot: int

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        return any(receiver(result) for result in context.variable(self.slot))


@dataclass(frozen=True, slots=True)
class _RootExpression(_Expression):
    index: int

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        return any(receiver(result) for result in context.roots[self.index])


@dataclass(frozen=True, slots=True)
class _NeighborExpression(_Expression):
    forward: bool
    labels: frozenset[str] = frozenset()

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        for edge in context.graph.neighbors(
            shape, forward=self.forward, include_traits="trait" in self.labels
        ):
            if (not self.labels or edge.label in self.labels) and receiver(edge.target):
                return True
        return False


class _RecursiveNeighborExpression(_Expression):
    __slots__ = ()

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        visited = {shape}
        pending = deque([shape])
        while pending:
            current = pending.popleft()
            for edge in context.graph.neighbors(
                current, forward=True, include_traits=False
            ):
                result = edge.target
                if result in visited:
                    continue
                visited.add(result)
                if receiver(result):
                    return True
                pending.append(result)
        return False


_RECURSIVE_NEIGHBOR: Final = _RecursiveNeighborExpression()


@dataclass(frozen=True, slots=True)
class _RecursiveExpression(_Expression):
    expression: _Expression

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        visited: set[Shape] = set()
        pending = deque([shape])
        while pending:
            current = pending.popleft()

            def enqueue(result: Shape) -> bool:
                if result in visited:
                    return False
                visited.add(result)
                if receiver(result):
                    return True
                pending.append(result)
                return False

            if self.expression.push(context, current, enqueue):
                return True
        return False


@dataclass(frozen=True, slots=True)
class _TopDownExpression(_Expression):
    qualifier: _Expression
    disqualifier: _Expression | None

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        if shape.type not in _SERVICE:
            return False
        visited: set[tuple[Shape, bool]] = set()
        pending = [(shape, False)]
        while pending:
            current, qualified = pending.pop()
            state = (current, qualified)
            if state in visited:
                continue
            visited.add(state)
            if not qualified and context.receives(self.qualifier, current):
                qualified = True
            if (
                qualified
                and self.disqualifier is not None
                and context.receives(self.disqualifier, current)
            ):
                qualified = False
            if qualified and receiver(current):
                return True
            children = [
                edge.target
                for edge in context.graph.neighbors(
                    current, forward=True, include_traits=False
                )
                if edge.label in _TOPDOWN_RELATIONSHIPS
            ]
            pending.extend((child, qualified) for child in reversed(children))
        return False


@dataclass(frozen=True, slots=True)
class _AttributeExpression(_Expression):
    path: tuple[str, ...]
    comparator: str | None
    expected: tuple[str, ...] = ()
    insensitive: bool = False

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        actual = _Value("shape", shape, context).path(self.path)
        matches = (
            actual.present
            if self.comparator is None
            else any(
                _compare(
                    self.comparator,
                    actual,
                    _Value.literal(value),
                    self.insensitive,
                )
                for value in self.expected
            )
        )
        return receiver(shape) if matches else False


@dataclass(frozen=True, slots=True)
class _ScopedOperand:
    path: tuple[str, ...] | None = None
    literal: str | None = None

    def resolve(self, scope: _Value) -> _Value:
        if self.path is not None:
            return scope.path(self.path)
        assert self.literal is not None  # noqa: S101 - parser invariant
        return _Value.literal(self.literal)


@dataclass(frozen=True, slots=True)
class _ScopedAssertion:
    lhs: _ScopedOperand
    comparator: str
    rhs: tuple[_ScopedOperand, ...]
    insensitive: bool


@dataclass(frozen=True, slots=True)
class _ScopedAttributeExpression(_Expression):
    path: tuple[str, ...]
    assertions: tuple[_ScopedAssertion, ...]

    def push(self, context: _Context, shape: Shape, receiver: _Receiver) -> bool:
        value = _Value("shape", shape, context).path(self.path)
        if not value.present:
            return False
        for scope in value.flatten():
            if all(
                any(
                    _compare(
                        assertion.comparator,
                        assertion.lhs.resolve(scope),
                        rhs.resolve(scope),
                        assertion.insensitive,
                    )
                    for rhs in assertion.rhs
                )
                for assertion in self.assertions
            ):
                return receiver(shape)
        return False


@dataclass(frozen=True, slots=True)
class _Edge:
    target: Shape
    label: str


class _Graph:
    __slots__ = ("_forward", "_reverse", "_trait_forward", "_trait_reverse", "shapes")

    def __init__(self, model: Model) -> None:
        shapes: list[Shape] = []
        for shape in model.iter_shapes(include_prelude=True):
            shapes.append(shape)
            shapes.extend(shape.members.values())
        virtual_traits = _virtual_trait_shapes(model, shapes)
        self.shapes = (*shapes, *virtual_traits.values())
        self._forward: dict[Shape, tuple[_Edge, ...]] = {}
        reverse: dict[Shape, list[_Edge]] = {}
        trait_forward: dict[Shape, list[_Edge]] = {}
        trait_reverse: dict[Shape, list[_Edge]] = {}

        for shape in self.shapes:
            edges = (
                ()
                if shape.id in virtual_traits
                else tuple(self._shape_edges(model, shape))
            )
            self._forward[shape] = edges
            for edge in edges:
                reverse.setdefault(edge.target, []).append(_Edge(shape, edge.label))
            for trait_id in _trait_ids(shape):
                target = model.find_shape(trait_id) or virtual_traits.get(trait_id)
                if target is None:
                    continue
                trait_forward.setdefault(shape, []).append(_Edge(target, "trait"))
                trait_reverse.setdefault(target, []).append(_Edge(shape, "trait"))

        self._reverse = {shape: tuple(reverse.get(shape, ())) for shape in self.shapes}
        self._trait_forward = {
            shape: tuple(trait_forward.get(shape, ())) for shape in self.shapes
        }
        self._trait_reverse = {
            shape: tuple(trait_reverse.get(shape, ())) for shape in self.shapes
        }

    def neighbors(
        self, shape: Shape, *, forward: bool, include_traits: bool
    ) -> tuple[_Edge, ...]:
        direct = self._forward[shape] if forward else self._reverse[shape]
        if not include_traits:
            return direct
        traits = self._trait_forward[shape] if forward else self._trait_reverse[shape]
        return (*direct, *traits)

    @staticmethod
    def _shape_edges(model: Model, shape: Shape) -> Iterable[_Edge]:
        for mixin in shape.mixins:
            target = model.find_shape(mixin)
            if target is not None and not isinstance(shape, MemberShape):
                yield _Edge(target, "mixin")
        if isinstance(shape, MemberShape):
            container = model.get_shape(shape.container)
            if not isinstance(container, EnumShape | IntEnumShape):
                yield _Edge(model.get_shape(shape.target), "")
            return
        if isinstance(shape, ServiceShape):
            for target in shape.operations:
                yield _Edge(model.get_shape(target), "operation")
            for target in shape.resources:
                yield _Edge(model.get_shape(target), "resource")
            for target in shape.errors:
                yield _Edge(model.get_shape(target), "error")
            return
        if isinstance(shape, ResourceShape):
            for target in shape.identifiers.values():
                yield _Edge(model.get_shape(target), "identifier")
            for target in shape.properties.values():
                yield _Edge(model.get_shape(target), "property")
            for target in shape.resources:
                yield _Edge(model.get_shape(target), "resource")
            for label in ("list", "create", "put", "read", "update", "delete"):
                target_id = getattr(shape, label)
                if target_id is not None:
                    yield _Edge(model.get_shape(target_id), label)
            for target in shape.operations:
                yield _Edge(model.get_shape(target), "operation")
            for target in shape.collection_operations:
                yield _Edge(model.get_shape(target), "collectionOperation")
            return
        if isinstance(shape, OperationShape):
            if shape.input != ShapeId("smithy.api", "Unit"):
                yield _Edge(model.get_shape(shape.input), "input")
            if shape.output != ShapeId("smithy.api", "Unit"):
                yield _Edge(model.get_shape(shape.output), "output")
            for target in shape.errors:
                yield _Edge(model.get_shape(target), "error")
            return
        for member in shape.members.values():
            yield _Edge(member, "member")


class _Context:
    __slots__ = ("_variable_indices", "graph", "roots", "variables")

    def __init__(
        self,
        graph: _Graph,
        roots: Sequence[frozenset[Shape]],
        variable_names: tuple[str, ...],
    ) -> None:
        self.graph = graph
        self.roots = roots
        self.variables: list[frozenset[Shape] | None] = [None] * len(variable_names)
        self._variable_indices = {
            name: index for index, name in enumerate(variable_names)
        }

    def clear_variables(self) -> None:
        self.variables[:] = [None] * len(self.variables)

    def variable(self, slot: int) -> frozenset[Shape]:
        return self.variables[slot] or frozenset()

    def variable_by_name(self, name: str) -> frozenset[Shape]:
        slot = self._variable_indices.get(name)
        if slot is None:
            return frozenset()
        return self.variable(slot)

    def collect(
        self,
        expression: _Expression,
        shapes: Iterable[Shape],
        *,
        reset_variables: bool = False,
    ) -> frozenset[Shape]:
        """Collect every result produced by an expression."""
        matches: set[Shape] = set()

        def capture(result: Shape) -> bool:
            matches.add(result)
            return False

        for shape in shapes:
            if reset_variables:
                self.clear_variables()
            expression.push(self, shape, capture)
        return frozenset(matches)

    def receives(self, expression: _Expression, shape: Shape) -> bool:
        received = False

        def stop(_: Shape) -> bool:
            nonlocal received
            received = True
            return True

        expression.push(self, shape, stop)
        return received


@dataclass(frozen=True, slots=True)
class _Value:
    kind: str
    value: _ValueData = None
    context: _Context | None = None

    @classmethod
    def literal(cls, value: bool | int | float | str) -> _Value:
        return cls("literal", value)

    @property
    def present(self) -> bool:
        if self.kind == "empty":
            return False
        if self.kind == "projection":
            return bool(self.value)
        return True

    def path(self, path: Sequence[str]) -> _Value:
        current = self
        for segment in path:
            if not current.present:
                break
            current = current.get_property(segment)
        return current

    def get_property(self, key: str) -> _Value:
        if self.kind == "literal":
            return (
                _Value.literal(len(self.string)) if key == "(length)" else _EMPTY_VALUE
            )
        if self.kind == "node":
            if isinstance(self.value, Mapping):
                mapping = self.value
                if key == "(keys)":
                    return _Value("projection", tuple(map(_Value.literal, mapping)))
                if key == "(values)":
                    return _Value(
                        "projection",
                        tuple(_Value("node", value) for value in mapping.values()),
                    )
                if key == "(length)":
                    return _Value.literal(len(mapping))
                return _Value("node", mapping[key]) if key in mapping else _EMPTY_VALUE
            if isinstance(self.value, tuple):
                values = cast(tuple[Node, ...], self.value)
                if key == "(values)":
                    return _Value(
                        "projection",
                        tuple(_Value("node", value) for value in values),
                    )
                if key == "(length)":
                    return _Value.literal(len(values))
                return _EMPTY_VALUE
            if isinstance(self.value, str) and key == "(length)":
                return _Value.literal(len(self.value))
            return _EMPTY_VALUE
        if self.kind == "projection":
            values = self.flatten()
            if key == "(first)":
                return values[0] if values else _EMPTY_VALUE
            projected = tuple(
                result
                for value in cast(tuple[_Value, ...], self.value)
                if (result := value.get_property(key)).present
            )
            return _Value("projection", projected)
        if self.kind == "id":
            shape_id = self.value
            assert isinstance(shape_id, ShapeId)  # noqa: S101 - internal invariant
            if key == "name":
                return _Value.literal(shape_id.name)
            if key == "namespace":
                return _Value.literal(shape_id.namespace)
            if key == "member":
                return (
                    _Value.literal(shape_id.member)
                    if shape_id.member is not None
                    else _EMPTY_VALUE
                )
            if key == "(length)":
                return _Value.literal(len(str(shape_id)))
            return _EMPTY_VALUE
        if self.kind == "service":
            service = self.value
            assert isinstance(service, ServiceShape)  # noqa: S101
            if key == "version":
                return (
                    _Value.literal(service.version)
                    if service.version is not None
                    else _EMPTY_VALUE
                )
            if key == "id":
                return _Value("id", service.id)
            return _EMPTY_VALUE
        if self.kind == "traits":
            shape = self.value
            assert isinstance(shape, Shape)  # noqa: S101
            traits = _traits(shape)
            if key == "(keys)":
                return _Value(
                    "projection", tuple(_Value("id", trait) for trait in traits)
                )
            if key == "(values)":
                return _Value(
                    "projection",
                    tuple(_Value("node", value) for value in traits.values()),
                )
            if key == "(length)":
                return _Value.literal(len(traits))
            trait_id = _absolute_trait(key)
            return (
                _Value("node", traits[trait_id]) if trait_id in traits else _EMPTY_VALUE
            )
        if self.kind == "shape":
            shape = self.value
            assert isinstance(shape, Shape)  # noqa: S101
            if key == "trait":
                return _Value("traits", shape, self.context)
            if key == "id":
                return _Value("id", shape.id, self.context)
            if key == "service" and isinstance(shape, ServiceShape):
                return _Value("service", shape, self.context)
            if key == "var":
                return _Value("variables", context=self.context)
            return _EMPTY_VALUE
        if self.kind == "variables":
            assert self.context is not None  # noqa: S101
            return _Value(
                "projection",
                tuple(
                    _Value("shape", shape, self.context)
                    for shape in self.context.variable_by_name(key)
                ),
            )
        return _EMPTY_VALUE

    @property
    def string(self) -> str:
        if self.kind == "empty" or self.kind == "projection":
            return ""
        if self.kind in {"id", "shape", "service"}:
            return str(self.value.id if isinstance(self.value, Shape) else self.value)
        if self.kind == "node":
            if isinstance(self.value, bool):
                return str(self.value).lower()
            if isinstance(self.value, str | int | float):
                return str(self.value)
            return ""
        return str(self.value)

    def flatten(self) -> tuple[_Value, ...]:
        if self.kind != "projection":
            return (self,)
        result: list[_Value] = []
        for value in cast(tuple[_Value, ...], self.value):
            result.extend(value.flatten())
        return tuple(result)


_EMPTY_VALUE: Final = _Value("empty")


def _absolute_trait(value: str) -> ShapeId:
    return ShapeId.from_string(
        value, default_namespace=None if "#" in value else "smithy.api"
    )


def _trait_ids(shape: Shape) -> tuple[ShapeId, ...]:
    traits = list(shape.traits)
    if isinstance(shape, EnumShape) and _ENUM_TRAIT not in shape.traits:
        traits.append(_ENUM_TRAIT)
    return tuple(traits)


def _virtual_trait_shapes(
    model: Model, shapes: Sequence[Shape]
) -> dict[ShapeId, Shape]:
    missing = {
        trait_id
        for shape in shapes
        for trait_id in _trait_ids(shape)
        if model.find_shape(trait_id) is None
    }
    if not missing:
        return {}
    if model.find_shape(_TRAIT_TRAIT) is None:
        missing.add(_TRAIT_TRAIT)
    if (
        missing & _PRELUDE_AUTH_TRAITS
        and model.find_shape(_AUTH_DEFINITION_TRAIT) is None
    ):
        missing.add(_AUTH_DEFINITION_TRAIT)
    empty: Mapping[str, Node] = MappingProxyType({})
    result: dict[ShapeId, Shape] = {}
    for shape_id in missing:
        traits: dict[ShapeId, Node] = {_TRAIT_TRAIT: empty}
        if shape_id in _PRELUDE_AUTH_TRAITS:
            traits[_AUTH_DEFINITION_TRAIT] = empty
        result[shape_id] = Shape(
            id=shape_id,
            type=_PRELUDE_TRAIT_TYPES.get(shape_id, ShapeType.STRUCTURE),
            traits=MappingProxyType(traits),
        )
    return result


def _traits(shape: Shape) -> Mapping[ShapeId, Node]:
    if not isinstance(shape, EnumShape) or _ENUM_TRAIT in shape.traits:
        return shape.traits
    enum_values: list[Mapping[str, Node]] = []
    for member in shape.members.values():
        value = member.get_trait("enumValue")
        entry: dict[str, Node] = {"name": member.name}
        if value is not None:
            entry["value"] = value
        for trait_id, trait_value in member.traits.items():
            if trait_id != ShapeId("smithy.api", "enumValue"):
                entry[trait_id.name] = trait_value
        enum_values.append(entry)
    return {**shape.traits, _ENUM_TRAIT: tuple(enum_values)}


def _compare(comparator: str, lhs: _Value, rhs: _Value, insensitive: bool) -> bool:
    if comparator in {"{<}", "{<<}", "{=}", "{!=}"}:
        if lhs.kind != "projection" or rhs.kind != "projection":
            return comparator == "{!=}"
        left = lhs.flatten()
        right = rhs.flatten()
        subset = _is_subset(left, right, insensitive)
        reverse = _is_subset(right, left, insensitive)
        return {
            "{<}": subset,
            "{<<}": subset and not reverse,
            "{=}": subset and reverse,
            "{!=}": not (subset and reverse),
        }[comparator]
    if comparator == "?=":
        return (lhs.present and rhs.string == "true") or (
            not lhs.present and rhs.string == "false"
        )
    for left in lhs.flatten():
        for right in rhs.flatten():
            if not left.present or not right.present:
                continue
            a = left.string.casefold() if insensitive else left.string
            b = right.string.casefold() if insensitive else right.string
            if comparator == "=" and a == b:
                return True
            if comparator == "!=" and a != b:
                return True
            if comparator == "^=" and a.startswith(b):
                return True
            if comparator == "$=" and a.endswith(b):
                return True
            if comparator == "*=" and b in a:
                return True
            if comparator in {">", ">=", "<", "<="}:
                try:
                    left_number = Decimal(a)
                    right_number = Decimal(b)
                except InvalidOperation:
                    continue
                if not left_number.is_finite() or not right_number.is_finite():
                    continue
                if comparator == ">" and left_number > right_number:
                    return True
                if comparator == ">=" and left_number >= right_number:
                    return True
                if comparator == "<" and left_number < right_number:
                    return True
                if comparator == "<=" and left_number <= right_number:
                    return True
    return False


def _is_subset(lhs: Sequence[_Value], rhs: Sequence[_Value], insensitive: bool) -> bool:
    return all(
        any(_compare("=", left, right, insensitive) for right in rhs) for left in lhs
    )


class _Parser:
    __slots__ = ("_depth", "_position", "_roots", "_source", "_variables")

    def __init__(self, source: str) -> None:
        self._source = source
        self._position = 0
        self._depth = 0
        self._roots: list[_Expression] = []
        self._variables: dict[str, int] = {}

    def parse(self, selector_type: type[Selector]) -> Selector:
        expression = self._parse_sequence()
        self._ws()
        if not self._eof:
            self._error(f"Unexpected selector character: {self._peek()!r}")
        names = tuple(self._variables)
        return selector_type(self._source, expression, tuple(self._roots), names)

    def _parse_sequence(self) -> _Expression:
        self._depth += 1
        if self._depth > 100:
            self._error("Selector exceeds the maximum nesting depth of 100")
        try:
            expressions = [self._parse_expression()]
            self._ws()
            while not self._eof and self._peek() not in ",])":
                expressions.append(self._parse_expression())
                self._ws()
            compact = tuple(
                expression for expression in expressions if expression is not _IDENTITY
            )
            if not compact:
                return _IDENTITY
            if len(compact) == 1:
                return compact[0]
            return _SequenceExpression(compact)
        finally:
            self._depth -= 1

    def _parse_expression(self) -> _Expression:
        self._ws()
        if self._eof:
            self._error("Unexpected selector EOF")
        char = self._peek()
        if char == "*":
            self._position += 1
            return _IDENTITY
        if char == ":":
            self._position += 1
            return self._parse_function()
        if char == "[":
            self._position += 1
            if self._take("@"):
                return self._parse_scoped_attribute()
            return self._parse_attribute()
        if char == ">":
            self._position += 1
            return _NeighborExpression(True)
        if char == "<":
            self._position += 1
            if self._take("-"):
                self._expect("[")
                labels = self._parse_relationships()
                self._expect("-")
                return _NeighborExpression(False, frozenset(labels))
            return _NeighborExpression(False)
        if char == "~":
            self._position += 1
            self._expect(">")
            return _RECURSIVE_NEIGHBOR
        if char == "-":
            self._position += 1
            self._expect("[")
            labels = self._parse_relationships()
            self._expect("-")
            self._expect(">")
            return _NeighborExpression(True, frozenset(labels))
        if char == "$":
            self._position += 1
            return self._parse_variable()
        token = self._identifier()
        type_expression = _TYPE_EXPRESSIONS.get(token)
        if type_expression is None:
            self._error(f"Unknown shape type: {token}")
        return type_expression

    def _parse_function(self) -> _Expression:
        name = self._identifier()
        arguments = self._parse_arguments()
        if name == "not":
            self._arity(name, arguments, 1)
            return _NotExpression(arguments[0])
        if name == "test":
            return _TestExpression(arguments)
        if name in {"is", "each"}:
            return _AnyExpression(arguments)
        if name == "in":
            self._arity(name, arguments, 1)
            return _InExpression(arguments[0])
        if name == "root":
            self._arity(name, arguments, 1)
            result = _RootExpression(len(self._roots))
            self._roots.append(arguments[0])
            return result
        if name == "recursive":
            self._arity(name, arguments, 1)
            return _RecursiveExpression(arguments[0])
        if name == "topdown":
            if len(arguments) not in {1, 2}:
                self._error(
                    f"The :topdown function accepts 1 or 2 arguments, found {len(arguments)}"
                )
            return _TopDownExpression(
                arguments[0], arguments[1] if len(arguments) == 2 else None
            )
        return _AnyExpression(())

    def _parse_arguments(self) -> tuple[_Expression, ...]:
        self._ws()
        self._expect("(")
        arguments: list[_Expression] = []
        while True:
            arguments.append(self._parse_sequence())
            self._ws()
            if self._take(")"):
                return tuple(arguments)
            self._expect(",")

    def _parse_variable(self) -> _Expression:
        self._ws()
        if self._take("{"):
            self._ws()
            name = self._identifier()
            self._ws()
            self._expect("}")
            return _VariableGetExpression(self._variable_slot(name))
        name = self._identifier()
        self._ws()
        self._expect("(")
        expression = self._parse_sequence()
        self._ws()
        self._expect(")")
        return _VariableStoreExpression(self._variable_slot(name), expression)

    def _parse_relationships(self) -> tuple[str, ...]:
        labels: list[str] = []
        while True:
            self._ws()
            labels.append(self._identifier())
            self._ws()
            if self._take("]"):
                return tuple(labels)
            self._expect(",")

    def _parse_attribute(self) -> _Expression:
        path = self._parse_path(allow_empty=False)
        self._ws()
        if self._take("]"):
            return _AttributeExpression(path, None)
        comparator = self._parse_comparator()
        values = [self._attribute_value()]
        self._ws()
        while self._take(","):
            values.append(self._attribute_value())
            self._ws()
        insensitive = self._take("i")
        self._ws()
        self._expect("]")
        return _AttributeExpression(path, comparator, tuple(values), insensitive)

    def _parse_scoped_attribute(self) -> _Expression:
        path = self._parse_path(allow_empty=True)
        self._ws()
        self._expect(":")
        assertions: list[_ScopedAssertion] = []
        while True:
            lhs = self._scoped_operand()
            comparator = self._parse_comparator()
            rhs = [self._scoped_operand()]
            self._ws()
            while self._take(","):
                rhs.append(self._scoped_operand())
                self._ws()
            insensitive = self._take("i")
            self._ws()
            assertions.append(
                _ScopedAssertion(lhs, comparator, tuple(rhs), insensitive)
            )
            if not self._take("&"):
                break
            self._expect("&")
        self._expect("]")
        return _ScopedAttributeExpression(path, tuple(assertions))

    def _scoped_operand(self) -> _ScopedOperand:
        self._ws()
        if self._take("@"):
            self._expect("{")
            self._ws()
            path = () if self._peek() == "}" else self._parse_path(allow_empty=False)
            self._expect("}")
            self._ws()
            return _ScopedOperand(path=path)
        return _ScopedOperand(literal=self._attribute_value())

    def _parse_path(
        self, *, allow_empty: bool, separator: str = "|"
    ) -> tuple[str, ...]:
        self._ws()
        if allow_empty and self._peek() == ":":
            return ()
        path = [self._path_segment()]
        self._ws()
        while self._take(separator):
            path.append(self._path_segment())
            self._ws()
        return tuple(path)

    def _path_segment(self) -> str:
        self._ws()
        if self._take("("):
            name = self._identifier()
            self._expect(")")
            return f"({name})"
        if self._peek() in {"'", '"'}:
            return self._attribute_value()
        start = self._position
        while (
            not self._eof
            and not self._peek().isspace()
            and self._peek() not in "|,]}:=!^$*?><{"
        ):
            self._position += 1
        if start == self._position:
            self._error("Expected an attribute path segment")
        return self._source[start : self._position]

    def _parse_comparator(self) -> str:
        self._ws()
        for token in (
            "{!=}",
            "{<<}",
            "{<}",
            "{=}",
            "!=",
            "^=",
            "$=",
            "*=",
            "?=",
            ">=",
            "<=",
        ):
            if self._take(token):
                self._ws()
                return token
        for token in ("=", ">", "<"):
            if self._take(token):
                self._ws()
                return token
        self._error("Expected an attribute comparator")

    def _attribute_value(self) -> str:
        self._ws()
        if self._peek() in {"'", '"'}:
            quote = self._peek()
            self._position += 1
            start = self._position
            while not self._eof and self._peek() != quote:
                self._position += 1
            if self._eof:
                self._error(f"Expected {quote!r} to close attribute value")
            value = self._source[start : self._position]
            self._position += 1
            self._ws()
            return value
        match = _NUMBER.match(self._source, self._position)
        if match is not None:
            self._position = match.end()
            self._ws()
            return match.group()
        start = self._position
        while (
            not self._eof
            and not self._peek().isspace()
            and self._peek() not in ",]|}"
            and not self._source.startswith("&&", self._position)
        ):
            self._position += 1
        if start == self._position:
            self._error("Expected an attribute value")
        value = self._source[start : self._position]
        self._ws()
        return value

    def _identifier(self) -> str:
        self._ws()
        match = _IDENTIFIER.match(self._source, self._position)
        if match is None:
            self._error("Expected an identifier")
        self._position = match.end()
        return match.group()

    def _variable_slot(self, name: str) -> int:
        slot = self._variables.get(name)
        if slot is None:
            slot = len(self._variables)
            self._variables[name] = slot
        return slot

    def _arity(
        self, name: str, arguments: tuple[_Expression, ...], expected: int
    ) -> None:
        if len(arguments) != expected:
            self._error(f"The :{name} function requires {expected} argument")

    def _ws(self) -> None:
        while not self._eof and self._peek().isspace():
            self._position += 1

    def _take(self, token: str) -> bool:
        if self._source.startswith(token, self._position):
            self._position += len(token)
            return True
        return False

    def _expect(self, token: str) -> None:
        if not self._take(token):
            self._error(f"Expected {token!r}")

    def _peek(self) -> str:
        return self._source[self._position] if not self._eof else ""

    @property
    def _eof(self) -> bool:
        return self._position >= len(self._source)

    def _error(self, message: str) -> NoReturn:
        line = self._source.count("\n", 0, self._position) + 1
        line_start = self._source.rfind("\n", 0, self._position) + 1
        column = self._position - line_start + 1
        raise SelectorSyntaxError(f"{message} at line {line}, column {column}")
