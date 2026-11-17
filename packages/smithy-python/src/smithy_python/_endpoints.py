# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Lowering of a service's endpoint rules into the BDD its client resolves with.

The lowered BDD is a ``smithy_core.endpoints.EndpointBdd`` of Python literals that
re-encodes the ``smithy.rules#endpointBdd`` trait. Lowering keeps no engine
decisions: names stay names, tags are small ints, and the trait's nodes are copied
verbatim. A service with no endpoint rules gets a BDD that requires a configured
endpoint.
"""

from __future__ import annotations

import base64
import binascii
import re
import struct
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from . import dependencies as _dependencies
from . import exceptions as _exceptions
from . import model as _model
from . import symbols as _symbols
from .symbols import TypeReference

if TYPE_CHECKING:
    from .writer import PythonWriter

type Value = None | bool | int | str | tuple[Value, ...]
"""A lowered value: a Python literal, with tuples for every sequence."""


@dataclass(frozen=True, slots=True)
class EndpointBdd:
    """A lowered endpoint BDD: the fields of a Python ``EndpointBdd``."""

    parameters: tuple[Value, ...]
    functions: tuple[str, ...]
    conditions: tuple[Value, ...]
    results: tuple[Value, ...]
    root: int
    nodes: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ClientContextField:
    """The config field a ``clientContextParams`` entry reads."""

    parameter: str
    """The endpoint parameter name."""

    attribute: str
    """The config attribute name."""

    type: str
    """The Python type of the value: ``bool`` or ``str``."""

    documentation: str


@dataclass(frozen=True, slots=True)
class EndpointPlan:
    """A service's lowered endpoint rules and the config fields they read."""

    trait: Mapping[str, _model.Node]
    """The endpointBdd trait the BDD was lowered from."""

    bdd: EndpointBdd
    client_context_fields: tuple[ClientContextField, ...]


def plan_endpoints(
    service: _model.ServiceShape, *, reserved: Collection[str] = ()
) -> EndpointPlan:
    """Lower a service's endpoint rules.

    A service with no endpoint rules gets a BDD that requires the ``SDK::Endpoint``
    built-in, the config's ``endpoint_uri``.

    :param service: The service.
    :param reserved: Config attribute names a client context field must not take.
    :raises CodegenError: If the service has only an endpointRuleSet trait, its
        endpointBdd trait is invalid, its rules call functions outside the rules
        standard library, or a client context field is unsupported or collides.
    """
    if service.has_trait(_ENDPOINT_BDD):
        trait = _object(service.get_trait(_ENDPOINT_BDD), "the trait")
    elif service.has_trait(_ENDPOINT_RULE_SET):
        raise _exceptions.CodegenError(
            f"Service {service.id} uses {_ENDPOINT_RULE_SET} without "
            f"{_ENDPOINT_BDD}. Client generation reads {_ENDPOINT_BDD} only, so "
            "compile the ruleset with Smithy's CompileBdd transform first."
        )
    else:
        trait = MANUAL_ENDPOINT_BDD
    fields = client_context_fields(service, reserved=reserved)
    bdd = lower(trait, {field.parameter: field.attribute for field in fields})
    unsupported = [name for name in bdd.functions if name not in STANDARD_FUNCTIONS]
    if unsupported:
        raise _exceptions.CodegenError(
            f"Service {service.id} endpoint rules call {', '.join(unsupported)}, "
            "which client generation does not support yet"
        )
    return EndpointPlan(trait=trait, bdd=bdd, client_context_fields=fields)


def client_context_fields(
    service: _model.ServiceShape, *, reserved: Collection[str] = ()
) -> tuple[ClientContextField, ...]:
    """The config field for each ``clientContextParams`` entry, in trait order.

    :raises CodegenError: If an entry's type is not boolean or string, or two
        fields, or a field and a reserved name, share an attribute.
    """
    if not service.has_trait(_CLIENT_CONTEXT_PARAMS):
        return ()
    entries = _object(service.get_trait(_CLIENT_CONTEXT_PARAMS), "clientContextParams")
    fields: list[ClientContextField] = []
    taken = dict.fromkeys(reserved, "")
    for name, value in entries.items():
        definition = _object(value, f"client context parameter {name}")
        type_ = _FIELD_TYPES.get(_string(definition.get("type"), f"{name} type"))
        if type_ is None:
            raise _exceptions.CodegenError(
                f"Unsupported type {definition.get('type')} for client context "
                f"parameter {name} of {service.id}"
            )
        attribute = _symbols._name(name)  # pyright: ignore[reportPrivateUsage]
        if attribute in taken:
            other = taken[attribute]
            raise _exceptions.CodegenError(
                f"Client context parameter {name} of {service.id} maps to the "
                f"config field {attribute}, which "
                + (f"{other} also maps to" if other else "the config already has")
            )
        taken[attribute] = name
        documentation = definition.get("documentation")
        fields.append(
            ClientContextField(
                parameter=name,
                attribute=attribute,
                type=type_,
                documentation=documentation
                if isinstance(documentation, str)
                else f"The {name} endpoint parameter.",
            )
        )
    return tuple(fields)


def lower(
    trait: Mapping[str, _model.Node], client_context_attributes: Mapping[str, str]
) -> EndpointBdd:
    """Lower an endpointBdd trait value into an endpoint BDD.

    :param trait: The trait's JSON value.
    :param client_context_attributes: The config attribute each of the service's
        clientContextParams reads, by parameter name.
    :raises CodegenError: If the trait is invalid or uses an unsupported version.
    """
    return _Lowering(trait, client_context_attributes).bdd()


def write_endpoints(writer: PythonWriter, plan: EndpointPlan) -> None:
    """Write the ``BDD`` constant of a generated endpoints module."""
    bdd = plan.bdd
    writer.line("# fmt: off")
    writer.line("# Tags: ref=0, attr=1, call=2, list=3, map=4, error=5, endpoint=6.")
    writer.line("BDD = ", _ENDPOINT_BDD_TYPE, "(")
    with writer.indent():
        if bdd.parameters:
            writer.line(
                "# (name, type, required, default, builtin, client_context_attribute)"
            )
        _write_items(writer, "parameters", bdd.parameters, None)
        writer.line("functions=", literal(bdd.functions), ",")
        comments = [
            _condition_text(_object(condition, "condition"))
            for condition in _array(plan.trait.get("conditions"), "conditions")
        ]
        _write_items(writer, "conditions", bdd.conditions, comments)
        # Nodes point at results by index, so each result carries its index.
        results = ["no match", *("" for _ in bdd.results[1:])]
        _write_items(writer, "results", bdd.results, results)
        writer.line("root=", _reference(bdd.root), ",")
        _write_nodes(writer, bdd.nodes)
    writer.line(")")
    writer.line("# fmt: on")


def literal(value: Value) -> str:
    """Render a lowered value as a one-line Python literal."""
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return _string_literal(value)
    items = ", ".join(map(literal, value))
    return f"({items},)" if len(value) == 1 else f"({items})"


# Verbatim from smithy-typescript AddDefaultEndpointRuleSet.DEFAULT_RULESET,
# compiled by Smithy's CompileBdd.
MANUAL_ENDPOINT_BDD: Final[Mapping[str, _model.Node]] = {
    "version": "1.1",
    "parameters": {
        "endpoint": {
            "type": "string",
            "builtIn": "SDK::Endpoint",
            "documentation": "Endpoint used for making requests. Should be "
            "formatted as a URI.",
        }
    },
    "conditions": ({"fn": "isSet", "argv": ({"ref": "endpoint"},)},),
    "results": (
        {
            "conditions": (),
            "endpoint": {"url": {"ref": "endpoint"}},
            "type": "endpoint",
        },
        {
            "conditions": (),
            "error": "(default endpointRuleSet) endpoint is not set - you must "
            "configure an endpoint.",
            "type": "error",
        },
    ),
    "root": 2,
    "nodeCount": 2,
    "nodes": base64.b64encode(
        struct.pack(">6i", -1, 1, -1, 0, 100_000_001, 100_000_002)
    ).decode(),
}
"""The endpointBdd of a service with no endpoint rules: it requires an endpoint."""

# The functions smithy_core.endpoints evaluates without an extension.
STANDARD_FUNCTIONS: Final = frozenset(
    {
        "booleanEquals",
        "coalesce",
        "isSet",
        "isValidHostLabel",
        "ite",
        "not",
        "parseURL",
        "split",
        "stringEquals",
        "substring",
        "uriEncode",
    }
)

RESULT_OFFSET: Final = 100_000_000
"""BDD references at or above this value point at results."""

# Tags lead expression and result tuples; smithy_core.endpoints._types.Tag has the
# same values.
_REF: Final = 0
_ATTR: Final = 1
_CALL: Final = 2
_LIST: Final = 3
_MAP: Final = 4
_ERROR: Final = 5
_ENDPOINT: Final = 6

_ENDPOINT_BDD: Final = _model.ShapeId("smithy.rules", "endpointBdd")
_ENDPOINT_RULE_SET: Final = _model.ShapeId("smithy.rules", "endpointRuleSet")
_CLIENT_CONTEXT_PARAMS: Final = _model.ShapeId("smithy.rules", "clientContextParams")
_FIELD_TYPES: Final = {"boolean": "bool", "string": "str"}
_ENDPOINT_BDD_TYPE: Final = TypeReference(
    "EndpointBdd",
    "smithy_core.endpoints",
    dependencies=(_dependencies.SMITHY_CORE,),
)
_INDEX: Final = re.compile(r"[+-]?[0-9]+")
_ESCAPES: Final = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}


class _Lowering:
    def __init__(
        self,
        trait: Mapping[str, _model.Node],
        client_context_attributes: Mapping[str, str],
    ) -> None:
        self._trait = trait
        self._client_context_attributes = client_context_attributes
        self._references: set[str] = set()
        self._functions: set[str] = set()

    def bdd(self) -> EndpointBdd:
        trait = self._trait
        version = trait.get("version")
        if version != "1.1":
            raise _invalid(
                f"endpointBdd version {version} is not supported; expected 1.1"
            )
        parameters = _object(trait.get("parameters"), "parameters")
        conditions = tuple(
            self._condition(_object(condition, "condition"))
            for condition in _array(trait.get("conditions"), "conditions")
        )
        rules = _array(trait.get("results"), "results")
        results: tuple[Value, ...] = (
            None,
            *(
                self._result(index, _object(rule, f"result {index}"))
                for index, rule in enumerate(rules, start=1)
            ),
        )
        nodes = self._nodes()
        return EndpointBdd(
            parameters=self._parameters(parameters),
            functions=tuple(sorted(self._functions)),
            conditions=conditions,
            results=results,
            root=_int(trait.get("root"), "root"),
            nodes=nodes,
        )

    # Normalized parameter fields; unread optional parameters are dropped.
    def _parameters(self, parameters: Mapping[str, _model.Node]) -> tuple[Value, ...]:
        lowered: list[Value] = []
        for name, value in parameters.items():
            definition = _object(value, f"parameter {name}")
            required = definition.get("required", False)
            if not isinstance(required, bool):
                raise _invalid(f"parameter {name} required must be a boolean")
            if not required and name not in self._references:
                continue
            builtin = definition.get("builtIn")
            if builtin is not None:
                builtin = _string(builtin, f"parameter {name} builtIn")
            default = definition.get("default")
            lowered.append(
                (
                    name,
                    _parameter_type(definition.get("type"), name),
                    required,
                    None if default is None else _default(default, name),
                    builtin,
                    self._client_context_attributes.get(name),
                )
            )
        return tuple(lowered)

    def _condition(self, condition: Mapping[str, _model.Node]) -> Value:
        assign = condition.get("assign")
        return (
            self._function(condition),
            None if assign is None else _string(assign, "condition assign"),
        )

    # Results after the no-match result at index 0.
    def _result(self, index: int, rule: Mapping[str, _model.Node]) -> Value:
        if _array(rule.get("conditions", ()), f"result {index} conditions"):
            raise _invalid(f"result {index} has conditions")
        kind = rule.get("type")
        if kind == "error":
            return (_ERROR, self._expression(rule.get("error")))
        if kind == "endpoint":
            endpoint = _object(rule.get("endpoint"), f"result {index} endpoint")
            properties = _object(endpoint.get("properties", {}), "endpoint properties")
            headers = _object(endpoint.get("headers", {}), "endpoint headers")
            return (
                _ENDPOINT,
                self._expression(endpoint.get("url")),
                self._map(properties) if properties else None,
                tuple(
                    (
                        name,
                        tuple(
                            self._expression(item)
                            for item in _array(values, f"header {name}")
                        ),
                    )
                    for name, values in headers.items()
                ),
            )
        raise _invalid(f"result {index} is not an endpoint or error result")

    def _expression(self, node: _model.Node) -> Value:
        if isinstance(node, Mapping):
            has_ref = "ref" in node
            if has_ref == ("fn" in node):
                raise _invalid("an expression object needs exactly one of ref or fn")
            if has_ref:
                return (_REF, self._name(_string(node["ref"], "ref")))
            return self._function(node)
        return self._literal(node)

    def _function(self, node: Mapping[str, _model.Node]) -> Value:
        name = _string(node.get("fn"), "fn")
        arguments = _array(node.get("argv"), f"{name} argv")
        if name == "getAttr":
            if len(arguments) != 2:
                raise _invalid("getAttr takes two arguments")
            target = self._expression(arguments[0])
            return (_ATTR, target, _path(_string(arguments[1], "getAttr path")))
        self._functions.add(name)
        return (_CALL, name, *map(self._expression, arguments))

    def _literal(self, node: _model.Node) -> Value:
        if isinstance(node, bool):
            return node
        if isinstance(node, int):
            return node
        if isinstance(node, str):
            return self._template(node)
        if isinstance(node, tuple):
            return (_LIST, *map(self._literal, node))
        if isinstance(node, Mapping):
            return self._map(node)
        raise _invalid(f"unsupported literal {node!r}")

    def _map(self, members: Mapping[str, _model.Node]) -> Value:
        return (_MAP, tuple(members), *map(self._literal, members.values()))

    # Every string in an expression position is a template, kept as a template
    # string. It is rendered back from its parsed parts.
    def _template(self, template: str) -> str:
        parts: list[str] = []
        for is_placeholder, part in _template_parts(template):
            if is_placeholder:
                parts.append("{" + self._placeholder(part) + "}")
            else:
                parts.append(part.replace("{", "{{").replace("}", "}}"))
        return "".join(parts)

    def _placeholder(self, raw: str) -> str:
        if "#" in raw:
            name, path = raw.split("#", 1)
            return self._name(name) + "#" + _path(path)
        return self._name(raw)

    def _name(self, name: str) -> str:
        self._references.add(name)
        return name

    # Nodes copied verbatim. Smithy's validator checks the indexes and references,
    # but not that node 0 is the terminal the runtime relies on, nor that no edge
    # complements a result reference.
    def _nodes(self) -> tuple[int, ...]:
        trait = self._trait
        count = _int(trait.get("nodeCount"), "nodeCount")
        try:
            data = base64.b64decode(_string(trait.get("nodes"), "nodes"), validate=True)
        except binascii.Error as error:
            raise _invalid("nodes are not base64") from error
        if count < 1 or len(data) != count * 12:
            raise _invalid(f"nodes do not hold {count} nodes")
        nodes = struct.unpack(f">{count * 3}i", data)
        if nodes[:3] != (-1, 1, -1):
            raise _invalid("node 0 must be the terminal (-1, 1, -1)")
        for index in range(count):
            if min(nodes[index * 3 + 1 : index * 3 + 3]) <= -RESULT_OFFSET:
                raise _invalid(f"node {index} complements a result reference")
        return nodes


def _template_parts(template: str) -> list[tuple[bool, str]]:
    """Split a template into (is_placeholder, text) parts, as Smithy parses it.

    Literal text is unescaped and a placeholder's text is the raw text between its
    braces.
    """
    parts: list[tuple[bool, str]] = []
    start: int | None = None
    depth = 0
    end = 0
    i = 0
    while i < len(template):
        if template.startswith(("{{", "}}"), i):
            i += 2
            continue
        if template[i] == "{":
            if depth == 0:
                if end != i:
                    parts.append((False, _unescape(template[end:i])))
                start = i + 1
            depth += 1
        if template[i] == "}":
            depth -= 1
            if depth < 0:
                raise _invalid(f"unmatched }} in template {template!r}")
            if depth == 0:
                assert start is not None  # noqa: S101 - set when depth became 1
                parts.append((True, template[start:i]))
                start = None
            end = i + 1
        i += 1
    if depth != 0:
        raise _invalid(f"unmatched {{ in template {template!r}")
    if end < len(template):
        parts.append((False, _unescape(template[end:])))
    return parts


def _unescape(text: str) -> str:
    return text.replace("{{", "{").replace("}}", "}")


# A getAttr path, parsed as Smithy parses it and written back: keys joined by '.',
# each index as [i].
def _path(path: str) -> str:
    components = path.split(".")
    # Java's String.split drops trailing empty components.
    while components and not components[-1]:
        components.pop()
    text = ""
    for component in components or [""]:
        bracket = component.find("[")
        if bracket < 0:
            text += ("." if text else "") + component
            continue
        index = component[bracket + 1 : -1]
        if not component.endswith("]") or not _INDEX.fullmatch(index):
            raise _invalid(f"invalid getAttr path component {component!r}")
        if bracket > 0:
            text += ("." if text else "") + component[:bracket]
        text += f"[{int(index)}]"
    if not text:
        raise _invalid(f"empty getAttr path {path!r}")
    return text


def _parameter_type(node: _model.Node, name: str) -> str:
    value = _string(node, f"parameter {name} type")
    if value.lower() in ("string", "boolean"):
        return value.lower()
    if value == "stringArray":
        return value
    raise _invalid(f"parameter {name} has unsupported type {value}")


def _default(node: _model.Node, name: str) -> Value:
    if isinstance(node, str | bool):
        return node
    if isinstance(node, tuple) and all(isinstance(item, str) for item in node):
        return tuple(item for item in node if isinstance(item, str))
    raise _invalid(f"parameter {name} has unsupported default {node!r}")


def _condition_text(condition: Mapping[str, _model.Node]) -> str:
    """A condition as Smithy's ``Condition.toString`` writes it."""
    text = _expression_text(condition)
    assign = condition.get("assign")
    return f"{assign} = {text}" if isinstance(assign, str) else text


def _expression_text(node: _model.Node) -> str:
    if isinstance(node, Mapping):
        if "ref" in node:
            return str(node["ref"])
        arguments = _array(node.get("argv"), "argv")
        if node.get("fn") == "getAttr":
            return f"{_expression_text(arguments[0])}#{arguments[1]}"
        return f"{node.get('fn')}({', '.join(map(_expression_text, arguments))})"
    return _literal_text(node)


def _literal_text(node: _model.Node) -> str:
    if isinstance(node, bool):
        return "true" if node else "false"
    if isinstance(node, str):
        return f'"{node}"'
    if isinstance(node, tuple):
        return "[" + ", ".join(map(_literal_text, node)) + "]"
    if isinstance(node, Mapping):
        members = ", ".join(f"{k}={_literal_text(v)}" for k, v in node.items())
        return "{" + members + "}"
    return str(node)


def _write_items(
    writer: PythonWriter,
    field: str,
    items: tuple[Value, ...],
    comments: list[str] | None,
) -> None:
    if not items:
        writer.line(field, "=(),")
        return
    writer.line(field, "=(")
    with writer.indent():
        for index, item in enumerate(items):
            comment = ""
            if comments is not None:
                text = comments[index]
                printable = text and all(" " <= c <= "~" for c in text)
                comment = f"  # {index}" + (f": {text}" if printable else "")
            writer.line(literal(item), ",", comment)
    writer.line("),")


def _write_nodes(writer: PythonWriter, nodes: tuple[int, ...]) -> None:
    if not nodes:
        writer.line("nodes=(),")
        return
    writer.line(
        "# (condition, high, low); 1 and -1 are terminals, a negative reference is a"
    )
    writer.line("# complement edge, and 100_000_000 + k is result k.")
    writer.line("nodes=(")
    with writer.indent():
        for index in range(0, len(nodes), 3):
            variable, high, low = nodes[index : index + 3]
            writer.line(f"{variable}, {_reference(high)}, {_reference(low)},")
    writer.line("),")


# A node or result reference; result references are written 100_000_000 + k, so k is
# easy to read.
def _reference(ref: int) -> str:
    return str(ref) if ref < RESULT_OFFSET else f"{ref:_}"


# An ASCII-only, double-quoted Python str literal.
def _string_literal(value: str) -> str:
    out: list[str] = []
    for char in value:
        code = ord(char)
        if char in _ESCAPES:
            out.append(_ESCAPES[char])
        elif code < 0x20 or code == 0x7F:
            out.append(f"\\x{code:02x}")
        elif code < 0x7F:
            out.append(char)
        elif code <= 0xFFFF:
            out.append(f"\\u{code:04x}")
        else:
            out.append(f"\\U{code:08x}")
    return '"' + "".join(out) + '"'


def _object(node: _model.Node, what: str) -> Mapping[str, _model.Node]:
    if not isinstance(node, Mapping):
        raise _invalid(f"{what} must be an object")
    return node


def _array(node: _model.Node, what: str) -> tuple[_model.Node, ...]:
    if not isinstance(node, tuple):
        raise _invalid(f"{what} must be an array")
    return node


def _string(node: _model.Node, what: str) -> str:
    if not isinstance(node, str):
        raise _invalid(f"{what} must be a string")
    return node


def _int(node: _model.Node, what: str) -> int:
    if isinstance(node, bool) or not isinstance(node, int):
        raise _invalid(f"{what} must be an integer")
    return node


def _invalid(message: str) -> _exceptions.CodegenError:
    return _exceptions.CodegenError(f"Invalid endpointBdd trait: {message}")
