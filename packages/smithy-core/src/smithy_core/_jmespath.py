#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Compile the JMESPath subset that operation context parameter paths use.

The subset is identifiers, sub-expressions, list and object wildcards, flatten,
multi-select lists and the ``keys`` function. A compiled path reads structures by
attribute and maps by key, so its input isn't converted first. Smithy checks each
path against the input shape, so values are trusted to have their modeled types.
"""

import json
import re
from collections.abc import Callable, Iterable
from dataclasses import fields, is_dataclass
from typing import Any, NamedTuple

from ._model_naming import member_field_name

type _Closure = Callable[[Any], Any]


def compile(expression: str) -> _Closure:
    """Compile a path into a function of an operation input.

    :param expression: The JMESPath expression.
    :raises ValueError: If the expression is outside the supported subset.
    """
    return _Parser(expression).parse()


class _Token(NamedTuple):
    kind: str
    """``identifier``, ``quoted``, ``end``, or the symbol itself."""

    text: str
    position: int


_TOKEN = re.compile(
    r"""
    (?P<identifier>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<quoted>"(?:[^"\\]|\\.)*")
    | (?P<symbol>\[\]|[.*\[\],()])
    | (?P<space>[ \t\n\r]+)
    | (?P<invalid>.)
    """,
    re.VERBOSE,
)

# Binding powers from the JMESPath reference parser. Other tokens end an expression.
_BINDING_POWER = {"[]": 9, ".": 40, "[": 55}
_STAR_BINDING_POWER = 20


def _tokenize(expression: str) -> list[_Token]:
    tokens: list[_Token] = []
    for found in _TOKEN.finditer(expression):
        text, position = found.group(), found.start()
        match found.lastgroup:
            case "identifier":
                tokens.append(_Token("identifier", text, position))
            case "quoted":
                tokens.append(_Token("quoted", json.loads(text), position))
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
        return self._tokens[self._index + offset]

    def _advance(self) -> _Token:
        token = self._tokens[self._index]
        self._index += 1
        return token

    def _expect(self, kind: str) -> None:
        token = self._advance()
        if token.kind != kind:
            raise _error(self._expression, token.position)

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
            case "*":
                right = self._parse_projection_right(_STAR_BINDING_POWER)
                return _projection(_identity, right, _object_values)
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
            case _:  # "["
                self._expect("*")
                self._expect("]")
                right = self._parse_projection_right(_STAR_BINDING_POWER)
                return _projection(left, right, _list_items)

    def _parse_projection_right(self, binding_power: int) -> _Closure:
        match self._token().kind:
            case ".":
                self._advance()
                return self._parse_dot_right(binding_power)
            case "[":
                return self._parse_expression(binding_power)
            case _:
                return _identity

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

    def _parse_function(self, name: _Token) -> _Closure:
        if name.text != "keys":
            raise _error(self._expression, name.position)
        self._expect("(")
        argument = self._parse_expression(0)
        self._expect(")")
        return _keys(argument)


def _identity(value: Any) -> Any:
    return value


def _field(name: str) -> _Closure:
    attribute = member_field_name(
        name, is_error=False, carries_response_metadata=False, is_enum=False
    )

    def field(value: Any) -> Any:
        if isinstance(value, dict):
            return value.get(name)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        return getattr(value, attribute, None)

    return field


def _subexpression(left: _Closure, right: _Closure) -> _Closure:
    def subexpression(value: Any) -> Any:
        return right(left(value))

    return subexpression


def _list_items(value: Any) -> Iterable[Any] | None:
    if isinstance(value, list | tuple):
        return value  # pyright: ignore[reportUnknownVariableType]
    return None


def _object_values(value: Any) -> Iterable[Any] | None:
    if is_dataclass(value):
        return [getattr(value, field.name) for field in fields(value)]
    if isinstance(value, dict):
        return value.values()  # pyright: ignore[reportUnknownVariableType]
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


def _flatten(left: _Closure) -> _Closure:
    def flatten(value: Any) -> Any:
        items = _list_items(left(value))
        if items is None:
            return None
        flat: list[Any] = []
        for item in items:
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


def _keys(argument: _Closure) -> _Closure:
    """``keys()``, which is None rather than an error for anything but a map, so an
    unset map leaves its parameter unset."""

    def keys(value: Any) -> Any:
        target = argument(value)
        if isinstance(target, dict):
            return list(target)  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
        return None

    return keys
