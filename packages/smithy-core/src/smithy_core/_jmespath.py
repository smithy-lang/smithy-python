#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Compile the JMESPath subset that operation context parameters and waiters use.

Compiled paths read structures by attribute and maps by key. Functions given the
wrong type return None instead of raising.
"""

import json
import re
from collections.abc import Callable, Iterable
from dataclasses import fields, is_dataclass
from typing import Any, NamedTuple

from ._model_naming import member_field_name

type _Closure = Callable[[Any], Any]


def compile(expression: str) -> _Closure:
    """Compile a path into a function. Raises ``ValueError`` for unsupported syntax."""
    return _Parser(expression).parse()


class _Token(NamedTuple):
    kind: str
    """``identifier``, ``quoted``, ``literal``, ``number``, ``end``, or the symbol
    itself."""

    text: Any
    position: int


_TOKEN = re.compile(
    r"""
    (?P<identifier>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<quoted>"(?:[^"\\]|\\.)*")
    | (?P<raw>'(?:[^'\\]|\\.)*')
    | (?P<literal>`(?:[^`\\]|\\.)*`)
    | (?P<number>-?[0-9]+)
    | (?P<symbol>\[\]|\[\?|==|!=|<=|>=|&&|\|\||[.*\[\],()@<>!|])
    | (?P<space>[ \t\n\r]+)
    | (?P<invalid>.)
    """,
    re.VERBOSE,
)

# Binding powers from the JMESPath reference parser. Other tokens end an expression.
_BINDING_POWER = {
    "|": 1,
    "||": 2,
    "&&": 3,
    "==": 5,
    "!=": 5,
    "<": 5,
    "<=": 5,
    ">": 5,
    ">=": 5,
    "[]": 9,
    "[?": 21,
    ".": 40,
    "[": 55,
}
_STAR_BINDING_POWER = 20
_NOT_BINDING_POWER = 45
# Projections stop at tokens that bind more loosely, such as comparisons.
_PROJECTION_STOP = 10
_COMPARATORS = frozenset({"==", "!=", "<", "<=", ">", ">="})


def _tokenize(expression: str) -> list[_Token]:
    tokens: list[_Token] = []
    for found in _TOKEN.finditer(expression):
        text, position = found.group(), found.start()
        match found.lastgroup:
            case "identifier":
                tokens.append(_Token("identifier", text, position))
            case "quoted":
                tokens.append(_Token("quoted", json.loads(text), position))
            case "raw":
                tokens.append(
                    _Token("literal", text[1:-1].replace("\\'", "'"), position)
                )
            case "literal":
                try:
                    value = json.loads(text[1:-1].replace("\\`", "`"))
                except ValueError:
                    raise _error(expression, position) from None
                tokens.append(_Token("literal", value, position))
            case "number":
                tokens.append(_Token("number", int(text), position))
            case "symbol":
                tokens.append(_Token(text, text, position))
            case "space":
                continue
            case _:
                raise _error(expression, position)
    tokens.append(_Token("end", "", len(expression)))
    return tokens


def _error(expression: str, position: int) -> ValueError:
    return ValueError(
        f"Unsupported JMESPath expression {expression!r} at position {position}"
    )


class _Parser:
    """A Pratt parser that builds the closure for each expression it parses."""

    def __init__(self, expression: str) -> None:
        self._expression = expression
        self._tokens = _tokenize(expression)
        self._index = 0

    def parse(self) -> _Closure:
        closure = self._parse_expression(0)
        token = self._token()
        if token.kind != "end":
            raise _error(self._expression, token.position)
        return closure

    def _token(self, offset: int = 0) -> _Token:
        return self._tokens[min(self._index + offset, len(self._tokens) - 1)]

    def _advance(self) -> _Token:
        token = self._token()
        self._index += 1
        return token

    def _expect(self, kind: str) -> _Token:
        token = self._advance()
        if token.kind != kind:
            raise _error(self._expression, token.position)
        return token

    def _parse_expression(self, binding_power: int) -> _Closure:
        left = self._parse_prefix(self._advance())
        while binding_power < _BINDING_POWER.get(self._token().kind, 0):
            left = self._parse_infix(self._advance(), left)
        return left

    def _parse_prefix(self, token: _Token) -> _Closure:
        match token.kind:
            case "identifier" if self._token().kind == "(":
                return self._parse_function(token)
            case "identifier" | "quoted":
                return _field(token.text)
            case "literal":
                return _literal(token.text)
            case "@":
                return _identity
            case "*":
                right = self._parse_projection_right(_STAR_BINDING_POWER)
                return _projection(_identity, right, _object_values)
            case "[" if self._token().kind == "number":
                return self._parse_index(_identity)
            case "[" if self._token().kind == "*" and self._token(1).kind == "]":
                self._expect("*")
                self._expect("]")
                right = self._parse_projection_right(_STAR_BINDING_POWER)
                return _projection(_identity, right, _list_items)
            case "[":
                return self._parse_multi_select_list()
            case "[]":
                right = self._parse_projection_right(_BINDING_POWER["[]"])
                return _projection(_flatten(_identity), right, _list_items)
            case "[?":
                return self._parse_filter(_identity)
            case "!":
                return _not(self._parse_expression(_NOT_BINDING_POWER))
            case "(":
                inner = self._parse_expression(0)
                self._expect(")")
                return inner
            case _:
                raise _error(self._expression, token.position)

    def _parse_infix(self, token: _Token, left: _Closure) -> _Closure:
        match token.kind:
            case "." if self._token().kind == "*":
                self._advance()
                right = self._parse_projection_right(_BINDING_POWER["."])
                return _projection(left, right, _object_values)
            case ".":
                right = self._parse_dot_right(_BINDING_POWER["."])
                return _subexpression(left, right)
            case "[]":
                right = self._parse_projection_right(_BINDING_POWER["[]"])
                return _projection(_flatten(left), right, _list_items)
            case "[?":
                return self._parse_filter(left)
            case "[" if self._token().kind == "number":
                return self._parse_index(left)
            case "[":
                self._expect("*")
                self._expect("]")
                right = self._parse_projection_right(_STAR_BINDING_POWER)
                return _projection(left, right, _list_items)
            case "|":
                return _subexpression(left, self._parse_expression(_BINDING_POWER["|"]))
            case "||":
                return _or(left, self._parse_expression(_BINDING_POWER["||"]))
            case "&&":
                return _and(left, self._parse_expression(_BINDING_POWER["&&"]))
            case kind if kind in _COMPARATORS:
                return _comparison(
                    kind, left, self._parse_expression(_BINDING_POWER[kind])
                )
            case _:
                raise _error(self._expression, token.position)

    def _parse_projection_right(self, binding_power: int) -> _Closure:
        token = self._token()
        if _BINDING_POWER.get(token.kind, 0) < _PROJECTION_STOP:
            return _identity
        match token.kind:
            case ".":
                self._advance()
                return self._parse_dot_right(binding_power)
            case "[" | "[?":
                return self._parse_expression(binding_power)
            case _:
                raise _error(self._expression, token.position)

    def _parse_dot_right(self, binding_power: int) -> _Closure:
        token = self._token()
        match token.kind:
            case "identifier" | "quoted" | "*":
                return self._parse_expression(binding_power)
            case "[":
                self._advance()
                return self._parse_multi_select_list()
            case _:
                raise _error(self._expression, token.position)

    def _parse_multi_select_list(self) -> _Closure:
        items = [self._parse_expression(0)]
        while self._token().kind == ",":
            self._advance()
            items.append(self._parse_expression(0))
        self._expect("]")
        return _multi_select_list(tuple(items))

    def _parse_index(self, left: _Closure) -> _Closure:
        index = self._expect("number").text
        self._expect("]")
        return _subexpression(left, _index(index))

    def _parse_filter(self, left: _Closure) -> _Closure:
        condition = self._parse_expression(0)
        self._expect("]")
        if self._token().kind == "[]":
            right = _identity
        else:
            right = self._parse_projection_right(_BINDING_POWER["[?"])
        return _filter_projection(left, right, condition)

    def _parse_function(self, name: _Token) -> _Closure:
        function = _FUNCTIONS.get(name.text)
        if function is None:
            raise _error(self._expression, name.position)
        build, arity = function
        self._expect("(")
        arguments: list[_Closure] = []
        if self._token().kind != ")":
            arguments.append(self._parse_expression(0))
            while self._token().kind == ",":
                self._advance()
                arguments.append(self._parse_expression(0))
        self._expect(")")
        if len(arguments) != arity:
            raise _error(self._expression, name.position)
        return build(*arguments)


def _identity(value: Any) -> Any:
    return value


def _field(name: str) -> _Closure:
    attribute = member_field_name(
        name, is_error=False, carries_response_metadata=False, is_enum=False
    )

    def field(value: Any) -> Any:
        if isinstance(value, dict):
            return value.get(name)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if value is None or isinstance(value, str | int | float | list | tuple):
            return None
        return getattr(value, attribute, None)

    return field


def _literal(value: Any) -> _Closure:
    def literal(_: Any) -> Any:
        return value

    return literal


def _subexpression(left: _Closure, right: _Closure) -> _Closure:
    def subexpression(value: Any) -> Any:
        return right(left(value))

    return subexpression


def _index(index: int) -> _Closure:
    def index_expression(value: Any) -> Any:
        items = _list_items(value)
        if items is None:
            return None
        try:
            return items[index]  # pyright: ignore[reportIndexIssue]
        except IndexError:
            return None

    return index_expression


def _list_items(value: Any) -> Any:
    if isinstance(value, list | tuple):
        return value  # pyright: ignore[reportUnknownVariableType]
    return None


def _object_values(value: Any) -> Iterable[Any] | None:
    if isinstance(value, dict):
        return value.values()  # pyright: ignore[reportUnknownVariableType]
    if is_dataclass(value) and not isinstance(value, type):
        return [getattr(value, field.name) for field in fields(value)]
    return None


def _projection(
    left: _Closure, right: _Closure, items_of: Callable[[Any], Iterable[Any] | None]
) -> _Closure:
    def projection(value: Any) -> Any:
        items = items_of(left(value))
        if items is None:
            return None
        return [result for item in items if (result := right(item)) is not None]

    return projection


def _filter_projection(
    left: _Closure, right: _Closure, condition: _Closure
) -> _Closure:
    def filter_projection(value: Any) -> Any:
        items = _list_items(left(value))
        if items is None:
            return None
        return [
            result
            for item in items  # pyright: ignore[reportUnknownVariableType]
            if _truthy(condition(item)) and (result := right(item)) is not None
        ]

    return filter_projection


def _flatten(left: _Closure) -> _Closure:
    def flatten(value: Any) -> Any:
        items = _list_items(left(value))
        if items is None:
            return None
        flat: list[Any] = []
        for item in items:  # pyright: ignore[reportUnknownVariableType]
            if isinstance(item, list | tuple):
                flat.extend(item)  # pyright: ignore[reportUnknownArgumentType]
            else:
                flat.append(item)
        return flat

    return flatten


def _multi_select_list(items: tuple[_Closure, ...]) -> _Closure:
    def multi_select_list(value: Any) -> Any:
        if value is None:
            return None
        return [item(value) for item in items]

    return multi_select_list


def _truthy(value: Any) -> bool:
    """JMESPath truthiness, under which zero is true."""
    if value is None or value is False:
        return False
    if isinstance(value, str | list | tuple | dict):
        return len(value) > 0  # pyright: ignore[reportUnknownArgumentType]
    return True


def _not(operand: _Closure) -> _Closure:
    def not_expression(value: Any) -> Any:
        return not _truthy(operand(value))

    return not_expression


def _and(left: _Closure, right: _Closure) -> _Closure:
    def and_expression(value: Any) -> Any:
        result = left(value)
        return right(value) if _truthy(result) else result

    return and_expression


def _or(left: _Closure, right: _Closure) -> _Closure:
    def or_expression(value: Any) -> Any:
        result = left(value)
        return result if _truthy(result) else right(value)

    return or_expression


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _equals(left: Any, right: Any) -> bool:
    """JMESPath equality, under which booleans are never numbers."""
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if isinstance(left, list | tuple) and isinstance(right, list | tuple):
        return len(left) == len(right) and all(  # pyright: ignore[reportUnknownArgumentType]
            _equals(a, b)
            for a, b in zip(left, right, strict=True)  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(  # pyright: ignore[reportUnknownMemberType]
            _equals(value, right[key])  # pyright: ignore[reportUnknownArgumentType]
            for key, value in left.items()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        )
    return left == right


def _comparison(operator: str, left: _Closure, right: _Closure) -> _Closure:
    def comparison(value: Any) -> Any:
        a, b = left(value), right(value)
        match operator:
            case "==":
                return _equals(a, b)
            case "!=":
                return not _equals(a, b)
            case _:
                pass
        # Ordering is only defined for numbers.
        if not (_is_number(a) and _is_number(b)):
            return None
        match operator:
            case "<":
                return a < b
            case "<=":
                return a <= b
            case ">":
                return a > b
            case _:
                return a >= b

    return comparison


def _keys(argument: _Closure) -> _Closure:
    """``keys()``, which is None rather than an error for anything but a map, so an
    unset map leaves its parameter unset."""

    def keys(value: Any) -> Any:
        target = argument(value)
        if isinstance(target, dict):
            return list(target)  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
        return None

    return keys


def _length(argument: _Closure) -> _Closure:
    """``length()`` of a string, list, or map, or None for anything else."""

    def length(value: Any) -> Any:
        target = argument(value)
        if isinstance(target, str | list | tuple | dict):
            return len(target)  # pyright: ignore[reportUnknownArgumentType]
        return None

    return length


def _contains(subject: _Closure, search: _Closure) -> _Closure:
    """``contains()`` of a list or string, or None for anything else."""

    def contains(value: Any) -> Any:
        target, wanted = subject(value), search(value)
        if isinstance(target, str):
            return isinstance(wanted, str) and wanted in target
        if isinstance(target, list | tuple):
            return any(_equals(item, wanted) for item in target)  # pyright: ignore[reportUnknownVariableType]
        return None

    return contains


# Each function's closure builder and arity.
_FUNCTIONS: dict[str, tuple[Callable[..., _Closure], int]] = {
    "keys": (_keys, 1),
    "length": (_length, 1),
    "contains": (_contains, 2),
}
