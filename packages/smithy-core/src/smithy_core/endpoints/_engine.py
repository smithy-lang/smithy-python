#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""The rules engine that evaluates an endpoint BDD.

The engine compiles each condition and result of an :py:class:`EndpointBdd` into a
closure the first time a resolution reaches it, and keeps it for the life of the
engine.
"""

import re
from collections.abc import Callable, Mapping, Sequence
from functools import lru_cache, partial
from operator import itemgetter
from types import MappingProxyType
from typing import Any, TypeGuard

from .. import URI
from ..exceptions import EndpointResolutionError, ExpectationNotMetError
from ..types import TypedProperties
from ..utils import parse_uri
from ._standard_library import STANDARD_FUNCTIONS
from ._types import (
    ENDPOINT_HEADERS,
    Endpoint,
    EndpointAuthScheme,
    EndpointAuthSchemeFactory,
    EndpointBdd,
    RulesExtension,
    Tag,
)

type _Values = list[Any]
type _Closure = Callable[[_Values], Any]
"""A compiled condition, expression or result, called with the values."""

type _Steps = tuple[str | int, ...]
"""A parsed getAttr path: its keys and indexes, in order."""

_RESULT_OFFSET = 100_000_000
"""BDD references at or above this value point at results."""

_CACHE_SIZE = 128
"""The number of resolved endpoints each engine keeps."""

_COMPILED_FUNCTIONS = frozenset(
    {"isSet", "not", "booleanEquals", "stringEquals", "coalesce", "ite"}
)
"""Standard functions the compiler builds into closures instead of calling."""

_NEVER_EMPTY = frozenset(
    {
        "isSet",
        "not",
        "booleanEquals",
        "stringEquals",
        "isValidHostLabel",
        "substring",
        "parseURL",
        "split",
    }
)
"""Standard functions whose values Python's truth test reads as the rules do.

Each returns a bool, None, or a value that is never empty, so a condition that calls
one holds exactly when its value is truthy.
"""


class RulesEngine:
    """Evaluates one endpoint BDD.

    It caches compiled closures and resolved endpoints.
    """

    def __init__(
        self, bdd: EndpointBdd, extensions: Sequence[RulesExtension] = ()
    ) -> None:
        """Create an engine.

        :param bdd: The endpoint BDD to evaluate.
        :param extensions: Extensions whose functions the rules may call, beyond the
            standard library, which is always included.
        """
        redefined = [
            name
            for extension in extensions
            for name in extension.functions
            if name in _COMPILED_FUNCTIONS or name in STANDARD_FUNCTIONS
        ]
        if redefined:
            raise EndpointResolutionError(
                f"Endpoint rules extensions redefine standard functions: {', '.join(redefined)}"
            )
        functions = dict(STANDARD_FUNCTIONS)
        auth_schemes: dict[str, EndpointAuthSchemeFactory] = {}
        for extension in extensions:
            functions.update(extension.functions)
            auth_schemes.update(extension.auth_schemes)
        called = [name for name in bdd.functions if name not in _COMPILED_FUNCTIONS]
        missing = [name for name in called if name not in functions]
        if missing:
            raise EndpointResolutionError(
                f"Endpoint rules use functions no extension provides: {', '.join(missing)}"
            )

        self._conditions = bdd.conditions
        self._results = bdd.results
        self._compiler = _ClosureCompiler(
            bdd, {name: functions[name] for name in called}, auth_schemes
        )
        self._root, self._condition_indexes, self._high_refs, self._low_refs = (
            _node_table(bdd.nodes, bdd.root)
        )

        # One closure per condition and result, at the same index as its entry. Each
        # starts as a stub that compiles its entry on first use and replaces itself.
        condition_stub = self._condition_stub
        result_stub = self._result_stub
        self._condition_closures: list[_Closure] = [
            partial(condition_stub, index) for index in range(len(bdd.conditions))
        ]
        self._result_closures: list[_Closure] = [_no_match]
        self._result_closures += [
            partial(result_stub, index) for index in range(1, len(bdd.results))
        ]

        self.evaluate: Callable[[tuple[Any, ...]], Endpoint] = lru_cache(
            maxsize=_CACHE_SIZE
        )(self._evaluate)
        """The endpoint for parameter values, through the engine's cache."""

    def _evaluate(self, param_values: tuple[Any, ...]) -> Endpoint:
        """Evaluate the decision diagram and build the endpoint, uncached.

        :param param_values: The parameter values, in BDD order.
        """
        # The parameter values, then one unset slot per assign target.
        values = [*param_values, *(None,) * self._compiler.target_count]
        condition_closures = self._condition_closures
        condition_indexes = self._condition_indexes
        high_refs, low_refs = self._high_refs, self._low_refs
        ref = self._root
        try:
            while ref < _RESULT_OFFSET:
                ref = (
                    high_refs[ref]
                    if condition_closures[condition_indexes[ref]](values)
                    else low_refs[ref]
                )
            return self._result_closures[ref - _RESULT_OFFSET](values)
        except EndpointResolutionError:
            raise
        except Exception as e:
            raise EndpointResolutionError(
                f"Endpoint rules failed with {type(e).__name__}: {e}"
            ) from e

    def _condition_stub(self, index: int, values: _Values) -> Any:
        """The stub for condition ``index``: compile it, replace the stub, and run it."""
        closure = self._compiler.compile_condition(self._conditions[index])
        self._condition_closures[index] = closure
        return closure(values)

    def _result_stub(self, index: int, values: _Values) -> Any:
        """The stub for result ``index``: compile it, replace the stub, and run it.

        Result 0, no match, has no stub.
        """
        result = self._results[index]
        if result is None:
            raise EndpointResolutionError(f"Invalid endpoint BDD result {index}: None")
        closure = self._compiler.compile_result(result)
        self._result_closures[index] = closure
        return closure(values)


class _ClosureCompiler:
    """Compiles one BDD's conditions and results into closures.

    Closures read and write a list of values by slot: the parameter values in BDD
    order, then one value per distinct assign target.
    """

    def __init__(
        self,
        bdd: EndpointBdd,
        functions: Mapping[str, Callable[..., Any]],
        auth_schemes: Mapping[str, EndpointAuthSchemeFactory],
    ) -> None:
        slots = {name: slot for slot, (name, *_) in enumerate(bdd.parameters)}
        for _, target in bdd.conditions:
            if target is not None:
                slots.setdefault(target, len(slots))
        self._slots = slots
        self._functions = functions
        self._auth_schemes = auth_schemes
        self.target_count = len(slots) - len(bdd.parameters)
        """The number of distinct assign targets; their slots follow the parameters'."""

    def compile_condition(self, condition: tuple[Any, ...]) -> _Closure:
        """A closure that tests a condition and stores its assigned value.

        A condition holds unless its value is None or False.
        """
        expr, target = condition
        # Most conditions call a compiled function, so they skip _compile_expr's
        # dispatch, and the one match also names the function for _NEVER_EMPTY.
        match expr:
            case (Tag.CALL, function_name, *_) if function_name in _COMPILED_FUNCTIONS:
                expr_closure = self._compile_function(expr)
            case (Tag.CALL, function_name, *_):
                expr_closure = self._compile_expr(expr)
            case _:
                function_name = None
                expr_closure = self._compile_expr(expr)
        if target is None:
            if function_name in _NEVER_EMPTY:
                return expr_closure
            return lambda values: (
                (v := expr_closure(values)) is not None and v is not False
            )
        slot = self._slots[target]

        def assign(values: _Values) -> bool:
            v = expr_closure(values)
            if v is None:
                return False
            values[slot] = v
            return v is not False

        return assign

    def compile_result(self, result: tuple[Any, ...]) -> _Closure:
        """A closure that builds a result's endpoint or raises its error."""
        match result:
            case (Tag.ERROR, message):
                message_closure = self._compile_expr(message)

                def error(values: _Values) -> Any:
                    raise EndpointResolutionError(message_closure(values))

                return error
            case (Tag.ENDPOINT, url, properties, headers):
                return self._compile_endpoint(url, properties, headers)
            case _:
                raise EndpointResolutionError(
                    f"Invalid endpoint BDD result: {result!r}"
                )

    def _compile_endpoint(
        self, url: Any, properties: Any, headers: tuple[Any, ...]
    ) -> _Closure:
        """A closure that builds an endpoint result's endpoint."""
        url_closure = self._compile_expr(url)
        properties_closure = (
            None if properties is None else self._compile_expr(properties)
        )
        header_closures = tuple(
            (name, tuple(self._compile_expr(expr) for expr in exprs))
            for name, exprs in headers
        )

        factories = self._auth_schemes

        def build(values: _Values) -> Endpoint:
            data: dict[str, Any] = {}
            auth_schemes: tuple[EndpointAuthScheme, ...] = ()
            if properties_closure is not None:
                for key, value in properties_closure(values).items():
                    if key == "authSchemes":
                        auth_schemes = _auth_schemes(value, factories)
                    else:
                        data[key] = value
            if header_closures:
                data[ENDPOINT_HEADERS.key] = MappingProxyType(
                    {
                        name: tuple([closure(values) for closure in value_closures])
                        for name, value_closures in header_closures
                    }
                )
            endpoint_properties = TypedProperties()
            # Hand the dict over: the constructor copies it item by item.
            endpoint_properties.data = data
            return Endpoint(
                uri=_to_uri(url_closure(values)),
                properties=endpoint_properties,
                auth_schemes=auth_schemes,
            )

        return build

    def _compile_expr(self, expr: Any) -> _Closure:
        """A closure that computes an expression's value.

        Lists become tuples and maps read-only mappings, so endpoints stay immutable.
        """
        match expr:
            case (Tag.REF, name):
                return itemgetter(self._slots[name])
            case (Tag.ATTR, base, path):
                return _attr(self._compile_expr(base), _parse_path(path))
            case (Tag.CALL, function_name, *_) if function_name in _COMPILED_FUNCTIONS:
                return self._compile_function(expr)
            case (Tag.CALL, function_name, (Tag.REF, name), *literals) if all(
                map(_is_literal, literals)
            ):
                # A function of one reference and literals reads the reference
                # directly and passes the literals as they are.
                function, slot = self._functions[function_name], self._slots[name]
                if not literals:
                    return lambda values: function(values[slot])
                return lambda values: function(values[slot], *literals)
            case (Tag.CALL, function_name, *args):
                function = self._functions[function_name]
                arg_closures = tuple(self._compile_expr(arg) for arg in args)
                return lambda values: function(
                    *[closure(values) for closure in arg_closures]
                )
            case (Tag.LIST, *elements):
                element_closures = tuple(
                    self._compile_expr(element) for element in elements
                )
                return lambda values: tuple(
                    [closure(values) for closure in element_closures]
                )
            case (Tag.MAP, keys, *elements):
                item_closures = tuple(
                    zip(keys, map(self._compile_expr, elements), strict=True)
                )
                return lambda values: MappingProxyType(
                    {key: closure(values) for key, closure in item_closures}
                )
            case str():
                if not _is_plain(expr):
                    return self._compile_template(expr)
                return _literal(expr)
            case bool() | int():
                return _literal(expr)
            case _:
                raise EndpointResolutionError(
                    f"Invalid endpoint BDD expression: {expr!r}"
                )

    def _compile_function(self, call: Any) -> _Closure:
        """A closure for a call of a function the compiler builds itself.

        Tests of a reference or against a literal, the most common conditions in
        endpoint rules, read the slot or compare with the literal directly.
        """
        match call:
            case (Tag.CALL, "isSet", (Tag.REF, name)):
                slot = self._slots[name]
                return lambda values: values[slot] is not None
            case (Tag.CALL, "isSet", arg):
                arg_closure = self._compile_expr(arg)
                return lambda values: arg_closure(values) is not None
            case (Tag.CALL, "not", arg):
                arg_closure = self._compile_expr(arg)
                return lambda values: not arg_closure(values)
            case (Tag.CALL, "booleanEquals", (Tag.REF, name), bool(literal)):
                slot = self._slots[name]
                return lambda values: values[slot] is literal
            case (Tag.CALL, "booleanEquals", left, bool(literal)):
                left_closure = self._compile_expr(left)
                return lambda values: left_closure(values) is literal
            case (Tag.CALL, "booleanEquals", left, right):
                left_closure = self._compile_expr(left)
                right_closure = self._compile_expr(right)
                return lambda values: left_closure(values) is right_closure(values)
            case (Tag.CALL, "stringEquals", (Tag.REF, name), str(literal)) if _is_plain(
                literal
            ):
                slot = self._slots[name]
                return lambda values: values[slot] == literal
            case (Tag.CALL, "stringEquals", left, str(literal)) if _is_plain(literal):
                left_closure = self._compile_expr(left)
                return lambda values: left_closure(values) == literal
            case (Tag.CALL, "stringEquals", left, right):
                left_closure = self._compile_expr(left)
                right_closure = self._compile_expr(right)

                def string_equals(values: _Values) -> bool:
                    left_value = left_closure(values)
                    right_value = right_closure(values)
                    return left_value is not None and left_value == right_value

                return string_equals
            case (Tag.CALL, "coalesce", *args):
                arg_closures = tuple(self._compile_expr(arg) for arg in args)

                def coalesce(values: _Values) -> Any:
                    for closure in arg_closures:
                        if (v := closure(values)) is not None:
                            return v
                    return None

                return coalesce
            case (Tag.CALL, "ite", test, then, otherwise):
                test_closure, then_closure, otherwise_closure = (
                    self._compile_expr(test),
                    self._compile_expr(then),
                    self._compile_expr(otherwise),
                )
                return lambda values: (
                    then_closure(values)
                    if test_closure(values)
                    else otherwise_closure(values)
                )
            case _:
                raise EndpointResolutionError(f"Invalid endpoint BDD call: {call!r}")

    def _compile_template(self, template: str) -> _Closure:
        """A closure that renders a template with at least one brace.

        The template is parsed here, once, into the closures of its parts.
        """
        parts = _parse_template(template)
        if len(parts) == 1 and isinstance(parts[0], str):
            return _literal(parts[0])
        part_closures: list[_Closure] = []
        for part in parts:
            if isinstance(part, str):
                part_closures.append(_literal(part))
                continue
            name, steps = part
            value_closure = itemgetter(self._slots[name])
            part_closures.append(
                value_closure if steps is None else _attr(value_closure, steps)
            )
        return lambda values: "".join([closure(values) for closure in part_closures])


def _is_plain(template: str) -> bool:
    """Whether a template has no braces, so it is the string literal it reads as."""
    return "{" not in template and "}" not in template


def _is_literal(expr: Any) -> bool:
    """Whether an expression is a literal: a boolean, an integer, or a plain string."""
    return isinstance(expr, bool | int) or (isinstance(expr, str) and _is_plain(expr))


def _to_uri(url: str) -> URI:
    """The URI of a rendered URL."""
    try:
        return parse_uri(url)
    except ExpectationNotMetError as e:
        raise EndpointResolutionError(f"Invalid endpoint URI: {url}") from e


def _literal(value: Any) -> _Closure:
    return lambda values: value


def _attr(base_closure: _Closure, steps: _Steps) -> _Closure:
    match steps:
        case (str(key),):

            def key_closure(values: _Values) -> Any:
                value = base_closure(values)
                if _is_dict(value):
                    return value.get(key)
                return _get_attr(value, steps)

            return key_closure
        case _:
            return lambda values: _get_attr(base_closure(values), steps)


def _is_dict(value: Any) -> TypeGuard[dict[str, Any]]:
    return isinstance(value, dict)


_ESCAPED_TEMPLATE_TOKEN = re.compile(r"\{\{|\}\}|\{([^{}]*)\}|[{}]")


def _parse_template(template: str) -> list[str | tuple[str, _Steps | None]]:
    """Split a template into literal runs and ``(name, steps)`` placeholders.

    As in Smithy, ``{{`` and ``}}`` are literal braces and any other brace outside a
    placeholder is an error. Adjacent literal text is merged into one run.
    """
    if "{{" in template or "}}" in template:
        return _parse_escaped_template(template)
    # Without escapes, each { opens a placeholder that the next } closes.
    head, *chunks = template.split("{")
    if "}" in head:
        raise _template_error(template)
    parts: list[str | tuple[str, _Steps | None]] = [head] if head else []
    for chunk in chunks:
        placeholder, closed, literal = chunk.partition("}")
        if not closed or "}" in literal:
            raise _template_error(template)
        parts.append(_parse_placeholder(placeholder))
        if literal:
            parts.append(literal)
    return parts


def _parse_escaped_template(template: str) -> list[str | tuple[str, _Steps | None]]:
    parts: list[str | tuple[str, _Steps | None]] = []
    literal = ""
    end = 0
    for match in _ESCAPED_TEMPLATE_TOKEN.finditer(template):
        literal += template[end : match.start()]
        end = match.end()
        placeholder = match.group(1)
        if placeholder is not None:
            if literal:
                parts.append(literal)
                literal = ""
            parts.append(_parse_placeholder(placeholder))
        elif len(match.group()) == 2:
            literal += match.group()[0]
        else:
            raise _template_error(template)
    literal += template[end:]
    if literal:
        parts.append(literal)
    return parts


def _parse_placeholder(placeholder: str) -> tuple[str, _Steps | None]:
    name, _, path = placeholder.partition("#")
    return name, _parse_path(path) if path else None


def _parse_path(path: str) -> _Steps:
    steps: list[str | int] = []
    for segment in path.split("."):
        key, bracket, index = segment.partition("[")
        if key:
            steps.append(key)
        if bracket:
            if not index.endswith("]"):
                raise EndpointResolutionError(f"Invalid getAttr path: {path!r}")
            steps.append(int(index[:-1]))
    return tuple(steps)


def _template_error(template: str) -> EndpointResolutionError:
    return EndpointResolutionError(
        f"Unmatched brace in endpoint template: {template!r}"
    )


def _get_attr(value: Any, steps: _Steps) -> Any:
    for step in steps:
        if value is None:
            return None
        if isinstance(step, str):
            # dict first: library functions return dicts, and the ABC check is slow.
            if isinstance(value, dict | Mapping):
                value = value.get(step)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            else:
                return None
        elif isinstance(value, tuple | list):
            try:
                value = value[step]  # pyright: ignore[reportUnknownVariableType]
            except IndexError:
                return None
        else:
            return None
    return value  # pyright: ignore[reportUnknownVariableType]


def _no_match(values: _Values) -> Any:
    raise EndpointResolutionError("No endpoint rule matched")


def _auth_schemes(
    entries: Any, factories: Mapping[str, EndpointAuthSchemeFactory]
) -> tuple[EndpointAuthScheme, ...]:
    """The auth schemes built from the ``authSchemes`` entries whose names an
    extension maps.

    They keep the rules' order. Rules that list only unmapped names give an endpoint no
    auth scheme can sign for, so that raises.
    """
    schemes: list[EndpointAuthScheme] = []
    for entry in entries:
        factory = factories.get(entry["name"])
        if factory is not None:
            schemes.append(factory(entry))
    if entries and not schemes:
        names = ", ".join(entry["name"] for entry in entries)
        raise EndpointResolutionError(
            f"Endpoint rules use auth schemes no extension provides: {names}"
        )
    return tuple(schemes)


def _node_table(
    nodes: tuple[int, ...], root: int
) -> tuple[int, tuple[Any, ...], tuple[Any, ...], tuple[Any, ...]]:
    """The root, and the condition indexes, high refs and low refs by reference.

    Index ``ref`` of each array describes trait node ``ref - 1``. When a terminal or
    complement edge appears, terminals become the no-match result and each
    complemented node gets a twin with its edges swapped.
    """
    condition_indexes: Sequence[Any] = (None, *nodes[0::3])
    high_refs: Sequence[Any] = (None, *nodes[1::3])
    low_refs: Sequence[Any] = (None, *nodes[2::3])
    if root > 1 and min(nodes[4::3], default=2) > 1 and min(nodes[5::3], default=2) > 1:
        return root, condition_indexes, high_refs, low_refs
    if root < -1:
        raise EndpointResolutionError(f"Invalid endpoint BDD root: {root}")

    # Twins are appended, so edit list copies.
    condition_indexes = list(condition_indexes)
    high_refs = list(high_refs)
    low_refs = list(low_refs)
    twins: dict[int, int] = {}

    def normalize(ref: int) -> int:
        if ref == 1 or ref == -1:
            return _RESULT_OFFSET
        if ref > 0:
            return ref
        twin = twins.get(-ref)
        if twin is None:
            twin = twins[-ref] = len(condition_indexes)
            condition_indexes.append(None)
            high_refs.append(None)
            low_refs.append(None)
        return twin

    for ref in range(2, len(condition_indexes)):
        high_refs[ref] = normalize(high_refs[ref])
        low_refs[ref] = normalize(low_refs[ref])
    for ref, twin in twins.items():
        condition_indexes[twin], high_refs[twin], low_refs[twin] = (
            condition_indexes[ref],
            low_refs[ref],
            high_refs[ref],
        )
    return normalize(root), tuple(condition_indexes), tuple(high_refs), tuple(low_refs)
