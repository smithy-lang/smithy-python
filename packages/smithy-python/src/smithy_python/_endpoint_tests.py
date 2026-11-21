# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Emission of ``tests/test_endpoints.py`` from ``smithy.rules#endpointTests``.

Every case becomes a rules test, which resolves the case's parameter values with the
client's own endpoint resolver. Every operation input of a case also becomes a client
test, which calls the operation through the async client with config from the
input's built-in and client parameters and checks the endpoint the client resolves.
The input's operation parameters become the call's keyword arguments, with nested
values in their dictionary forms. A client test the client can't express is
generated as skipped, with the reason. Cases keep the trait's ``params`` and
``expect`` objects as they are.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Final

from . import _endpoints
from . import dependencies as _dependencies
from . import exceptions as _exceptions
from . import model as _model
from .symbols import TypeReference

if TYPE_CHECKING:
    from .clients import ClientPlan, OperationPlan
    from .generation import ClientSettings, GenerationContext
    from .writer import PythonWriter


def write_endpoint_tests(
    context: GenerationContext[ClientSettings],
    plan: ClientPlan,
    endpoints: _endpoints.EndpointPlan,
    client: TypeReference,
    config: TypeReference,
    new_config: tuple[str | TypeReference, ...] | None = None,
    test_config: Mapping[str, tuple[Part, ...]] | None = None,
    builtin_entry: BuiltinEntry | None = None,
) -> None:
    """Register ``tests/test_endpoints.py`` when the service has endpoint tests.

    :param client: The async client class.
    :param config: The async config class.
    :param new_config: The callable that creates an async config from keyword
        fields. Defaults to the config class.
    :param test_config: Config fields every test sets, as expressions by field
        name. A case's own fields replace them.
    :param builtin_entry: The config field and expression that set a built-in to
        a case's value, or None when no config field sets it.
    :raises CodegenError: If a case names an operation the service doesn't
        contain, expects neither an endpoint nor an error, or gives an operation
        an input member it doesn't have.
    """
    service = plan.selection.service
    assert service is not None  # noqa: S101 - ClientPlan requires a service
    if endpoints.trait is _endpoints.MANUAL_ENDPOINT_BDD:
        return
    trait = service.get_trait(_ENDPOINT_TESTS)
    cases = (
        _array(trait.get("testCases", ()), "testCases")
        if isinstance(trait, Mapping)
        else ()
    )
    if not cases:
        return
    # pytestmark names pytest-asyncio's marker, which nothing imports.
    context.dependencies.add(_dependencies.PYTEST_ASYNCIO)
    _Writer(
        context.files.python_module("tests/test_endpoints.py", "tests.test_endpoints"),
        plan,
        endpoints,
        client,
        config,
        new_config or (config,),
        test_config or {},
        builtin_entry or (lambda builtin, value: None),
    ).write(service, tuple(_object(case, "test case") for case in cases))


type Part = str | TypeReference
"""A piece of a generated line."""

type BuiltinEntry = Callable[[str, _model.Node], tuple[str, tuple[Part, ...]] | None]
"""Finds the config field and expression that set a built-in in a test."""


def literal(node: _model.Node) -> str:
    """Render a JSON node as a one-line Python literal of lists and dicts."""
    if node is None:
        return "None"
    if isinstance(node, bool):
        return "True" if node else "False"
    if isinstance(node, int | float):
        return str(node)
    if isinstance(node, str):
        return _endpoints.literal(node)
    if isinstance(node, tuple):
        return "[" + ", ".join(map(literal, node)) + "]"
    return (
        "{"
        + ", ".join(f"{_endpoints.literal(k)}: {literal(v)}" for k, v in node.items())
        + "}"
    )


_ENDPOINT_TESTS: Final = _model.ShapeId("smithy.rules", "endpointTests")
_PYTEST_MARK: Final = TypeReference(
    "mark", "pytest", dependencies=(_dependencies.PYTEST,)
)
_PYTEST_PARAM: Final = TypeReference(
    "param", "pytest", dependencies=(_dependencies.PYTEST,)
)
_ANY: Final = TypeReference("Any", "typing")
_MAPPING: Final = TypeReference("Mapping", "collections.abc")
_AWAITABLE: Final = TypeReference("Awaitable", "collections.abc")
_CALLABLE: Final = TypeReference("Callable", "collections.abc")
_CONCATENATE: Final = TypeReference("Concatenate", "typing")
_CORE: Final = (_dependencies.SMITHY_CORE,)
_CLOSE_ASYNC: Final = TypeReference(
    "close_async", "smithy_core.aio.utils", dependencies=_CORE
)
_BDD_RESOLVER: Final = TypeReference(
    "BddEndpointResolver", "smithy_core.endpoints", dependencies=_CORE
)
_INTERCEPTOR: Final = TypeReference(
    "Interceptor", "smithy_core.interceptors", dependencies=_CORE
)
_RETRY: Final = TypeReference(
    "SimpleRetryStrategy", "smithy_core.retries", dependencies=_CORE
)
_TEST: Final = (_dependencies.SMITHY_TEST,)
_CHECK_RULES: Final = TypeReference(
    "check_rules_case", "smithy_test", dependencies=_TEST
)
_CHECK_CLIENT: Final = TypeReference(
    "check_client_case_async", "smithy_test.aio", dependencies=_TEST
)
# Member types whose values a test can't write as JSON literals.
_UNWRITABLE: Final = frozenset(
    {
        _model.ShapeType.BLOB,
        _model.ShapeType.TIMESTAMP,
        _model.ShapeType.BIG_DECIMAL,
        _model.ShapeType.DOCUMENT,
    }
)


class _Writer:
    def __init__(
        self,
        writer: PythonWriter,
        plan: ClientPlan,
        endpoints: _endpoints.EndpointPlan,
        client: TypeReference,
        config: TypeReference,
        new_config: tuple[str | TypeReference, ...],
        test_config: Mapping[str, tuple[Part, ...]],
        builtin_entry: BuiltinEntry,
    ) -> None:
        self._writer = writer
        self._new_config = new_config
        self._test_config = test_config
        self._builtin_entry = builtin_entry
        self._extensions = tuple(
            extension.reference for extension in endpoints.extensions
        )
        self._plan = plan
        self._client = client
        self._config = config
        self._fields = {
            field.parameter: field.attribute
            for field in endpoints.client_context_fields
        }
        parameters = _object(endpoints.trait.get("parameters", {}), "parameters")
        self._builtins: dict[str, Mapping[str, _model.Node]] = {}
        for name, value in parameters.items():
            definition = _object(value, f"parameter {name}")
            builtin = definition.get("builtIn")
            if isinstance(builtin, str):
                self._builtins[builtin] = {**definition, "name": name}

    def write(
        self, service: _model.ServiceShape, cases: tuple[Mapping[str, _model.Node], ...]
    ) -> None:
        writer = self._writer
        writer.line(f"# Endpoint tests from the endpointTests trait of {service.id}.")
        writer.line()
        writer.line("pytestmark = ", _PYTEST_MARK, ".asyncio")
        self._write_factories()
        self._write_rules_tests(cases)
        self._write_client_tests(cases)

    def _write_factories(self) -> None:
        w = self._writer
        any_ = _ANY
        w.line()
        w.line()
        w.line("_TEST_CONFIG: dict[str, ", any_, "] = {")
        with w.indent():
            for name, value in self._test_config.items():
                w.line(_endpoints.literal(name), ": ", *value, ",")
        w.line("}")
        w.line(
            _endpoints.literal(
                "Config fields every test sets. A case's own fields replace them."
            )
        )
        w.line()
        w.line()
        w.line("async def _config(**fields: ", any_, ") -> ", self._config, ":")
        with w.indent():
            w.line(
                "return ",
                *self._new_config,
                "(**(_TEST_CONFIG | fields), retry_strategy=",
                _RETRY,
                "(max_attempts=1))",
            )
        if self._extensions:
            w.line()
            w.line()
            w.line("_RULES_EXTENSIONS = [", *_join(self._extensions, ", "), "]")
            w.line(
                _endpoints.literal(
                    "The extensions of the default resolver, which build the auth"
                    " schemes a case expects."
                )
            )
        w.line()
        w.line()
        w.line(
            "# Every rules test shares one resolver, so its caches see changing"
            " parameters."
        )
        w.line("_resolver: ", _BDD_RESOLVER, " | None = None")
        w.line()
        w.line()
        w.line("async def _endpoint_resolver() -> ", _BDD_RESOLVER, ":")
        with w.indent():
            w.line("global _resolver")
            w.line("if _resolver is None:")
            with w.indent():
                w.line("config = await _config()")
                w.line(
                    "# Only the resolver is used, so the transport is closed right"
                    " away."
                )
                w.line("await ", _CLOSE_ASYNC, "(config.transport)")
                w.line(
                    "# The rules checks are sync, so they need the default sync"
                    " resolver."
                )
                w.line("resolver = config.endpoint_resolver")
                w.line("if not isinstance(resolver, ", _BDD_RESOLVER, "):")
                with w.indent():
                    w.line(
                        'raise TypeError("The default endpoint resolver is not a '
                        'BddEndpointResolver")'
                    )
                w.line("_resolver = resolver")
            w.line("return _resolver")
        w.line()
        w.line()
        w.line("async def _client(")
        with w.indent():
            w.line(
                "config: ",
                _MAPPING,
                "[str, ",
                any_,
                "], capture: ",
                _INTERCEPTOR,
                "[",
                any_,
                ", ",
                any_,
                ", ",
                any_,
                ", ",
                any_,
                "]",
            )
        w.line(") -> ", self._client, ":")
        with w.indent():
            w.line(
                "return ",
                self._client,
                "(config=await _config(**config, interceptors=[capture]))",
            )

    def _write_rules_tests(self, cases: tuple[Mapping[str, _model.Node], ...]) -> None:
        w = self._writer
        ids = _CaseIds()
        w.line()
        w.line()
        w.line("RULES_CASES = [")
        with w.indent():
            for case in cases:
                w.line(_PYTEST_PARAM, "(")
                with w.indent():
                    w.line(literal(_object(case.get("params", {}), "params")), ",")
                    w.line(_expectation(case), ",")
                    w.line("id=", _endpoints.literal(ids.next(case)), ",")
                w.line("),")
        w.line("]")
        w.line()
        w.line()
        w.line("@", _PYTEST_MARK, '.parametrize(("params", "expect"), RULES_CASES)')
        w.line("async def test_endpoint_rules(")
        with w.indent():
            w.line("params: dict[str, ", _ANY, "], expect: dict[str, ", _ANY, "]")
        w.line(") -> None:")
        with w.indent():
            w.line(
                _CHECK_RULES,
                "(await _endpoint_resolver(), params, expect",
                self._extensions_argument(),
                ")",
            )

    def _write_client_tests(self, cases: tuple[Mapping[str, _model.Node], ...]) -> None:
        inputs = [
            (case, _object(item, "operation input"))
            for case in cases
            for item in _array(case.get("operationInputs", ()), "operationInputs")
        ]
        if not inputs:
            return
        w = self._writer
        ids = _CaseIds()
        w.line()
        w.line()
        w.line("CLIENT_CASES = [")
        with w.indent():
            for case, operation_input in inputs:
                self._write_client_case(case, operation_input, ids.next(case))
        w.line("]")
        w.line()
        w.line()
        w.line(
            "@",
            _PYTEST_MARK,
            '.parametrize(("config", "operation", "input", "expect"), CLIENT_CASES)',
        )
        w.line("async def test_endpoint_client(")
        with w.indent():
            w.line("config: dict[str, ", _ANY, "],")
            w.line(
                "operation: ",
                _CALLABLE,
                "[",
                _CONCATENATE,
                "[",
                self._client,
                ", ...], ",
                _AWAITABLE,
                "[",
                _ANY,
                "]],",
            )
            w.line("input: dict[str, ", _ANY, "],")
            w.line("expect: dict[str, ", _ANY, "],")
        w.line(") -> None:")
        with w.indent():
            w.line("await ", _CHECK_CLIENT, "(")
            with w.indent():
                w.line(
                    "lambda capture: _client(config, capture), operation, input, expect",
                    self._extensions_argument(),
                )
            w.line(")")

    def _write_client_case(
        self,
        case: Mapping[str, _model.Node],
        operation_input: Mapping[str, _model.Node],
        case_id: str,
    ) -> None:
        w = self._writer
        name = _string(operation_input.get("operationName"), "operationName")
        operation = self._operation(name)
        skips: list[str] = []
        entries = self._config_entries(operation_input, skips)
        params = _object(operation_input.get("operationParams", {}), "operationParams")
        arguments = self._arguments(
            self._plan.model.get_shape(operation.operation.input), params, skips
        )
        w.line(_PYTEST_PARAM, "(")
        with w.indent():
            w.line("{", *_join(entries, ", "), "},")
            w.line(self._client, ".", operation.method_name, ",")
            w.line("{", ", ".join(arguments), "},")
            w.line(_expectation(case), ",")
            w.line("id=", _endpoints.literal(case_id), ",")
            if skips:
                reason = _endpoints.literal("; ".join(dict.fromkeys(skips)))
                w.line("marks=", _PYTEST_MARK, ".skip(reason=", reason, "),")
        w.line("),")

    # The config entries an operation input's built-in and client parameters set. A
    # parameter the client has no config field for adds the reason the case is
    # skipped.
    def _extensions_argument(self) -> str:
        return ", extensions=_RULES_EXTENSIONS" if self._extensions else ""

    def _config_entries(
        self, operation_input: Mapping[str, _model.Node], skips: list[str]
    ) -> list[tuple[Part, ...]]:
        entries: list[tuple[Part, ...]] = []
        builtins = _object(operation_input.get("builtInParams", {}), "builtInParams")
        for builtin, value in builtins.items():
            parameter = self._builtins.get(builtin)
            # A built-in that is also a client context parameter reads its field.
            field = (
                None if parameter is None else self._fields.get(str(parameter["name"]))
            )
            if field is None and builtin == "SDK::Endpoint":
                field = "endpoint_uri"
            if field is not None:
                entries.append((f"{_endpoints.literal(field)}: {literal(value)}",))
            elif (entry := self._builtin_entry(builtin, value)) is not None:
                entries.append((_endpoints.literal(entry[0]), ": ", *entry[1]))
            elif parameter is not None and parameter.get("default") != value:
                skips.append(f"No config field sets the built-in {builtin}")
        clients = _object(operation_input.get("clientParams", {}), "clientParams")
        for name, value in clients.items():
            field = self._fields.get(name)
            if field is None:
                skips.append(f"{name} is not a client context parameter")
            else:
                entries.append((f"{_endpoints.literal(field)}: {literal(value)}",))
        return entries

    def _arguments(
        self,
        shape: _model.Shape,
        params: Mapping[str, _model.Node],
        skips: list[str],
    ) -> list[str]:
        return [
            f"{_endpoints.literal(field)}: {value}"
            for field, value in self._members(shape, params, skips)
        ]

    # A structure or union value in its dictionary form: (field name, literal).
    def _members(
        self,
        shape: _model.Shape,
        values: Mapping[str, _model.Node],
        skips: list[str],
    ) -> list[tuple[str, str]]:
        members: list[tuple[str, str]] = []
        for name, value in values.items():
            member = shape.members.get(name)
            if member is None:
                raise _exceptions.CodegenError(
                    f"Endpoint test input for {shape.id} sets {name}, which it "
                    "doesn't have"
                )
            members.append(
                (
                    self._plan.symbols.member_name(member.id),
                    self._value(self._plan.model.get_target(member), value, skips),
                )
            )
        return members

    def _value(self, shape: _model.Shape, value: _model.Node, skips: list[str]) -> str:
        if value is None:
            return "None"
        if shape.type in _UNWRITABLE:
            skips.append(f"Endpoint tests can't set {shape.type} values")
            return literal(value)
        if isinstance(shape, _model.ListShape):
            target = self._plan.model.get_target(shape.member)
            items = _array(value, f"{shape.id} value")
            return "[" + ", ".join(self._value(target, v, skips) for v in items) + "]"
        if isinstance(shape, _model.MapShape):
            target = self._plan.model.get_target(shape.value)
            entries = _object(value, f"{shape.id} value")
            return (
                "{"
                + ", ".join(
                    f"{_endpoints.literal(k)}: {self._value(target, v, skips)}"
                    for k, v in entries.items()
                )
                + "}"
            )
        if shape.type in (_model.ShapeType.STRUCTURE, _model.ShapeType.UNION):
            members = self._members(shape, _object(value, f"{shape.id} value"), skips)
            return (
                "{"
                + ", ".join(f"{_endpoints.literal(k)}: {v}" for k, v in members)
                + "}"
            )
        return literal(value)

    def _operation(self, name: str) -> OperationPlan:
        for operation in self._plan.operations:
            if operation.operation.id.name == name:
                return operation
        service = self._plan.selection.service
        assert service is not None  # noqa: S101 - ClientPlan requires a service
        raise _exceptions.CodegenError(
            f"Endpoint test operation {name} is not in service {service.id}"
        )


def _join(
    items: tuple[TypeReference, ...] | list[tuple[Part, ...]], separator: str
) -> tuple[Part, ...]:
    parts: list[Part] = []
    for index, item in enumerate(items):
        if index:
            parts.append(separator)
        if isinstance(item, tuple):
            parts.extend(item)
        else:
            parts.append(item)
    return tuple(parts)


# The case's expect object as the trait models it.
def _expectation(case: Mapping[str, _model.Node]) -> str:
    expect = _object(case.get("expect"), "expect")
    if "error" in expect:
        return literal({"error": expect["error"]})
    endpoint = expect.get("endpoint")
    if not isinstance(endpoint, Mapping):
        raise _exceptions.CodegenError(
            "An endpoint test case expects neither an endpoint nor an error"
        )
    expected: dict[str, _model.Node] = {"url": endpoint.get("url")}
    for key in ("headers", "properties"):
        if endpoint.get(key):
            expected[key] = endpoint[key]
    return literal({"endpoint": expected})


# Test ids from case documentation, numbered when a description repeats.
class _CaseIds:
    def __init__(self) -> None:
        self._used: set[str] = set()

    def next(self, case: Mapping[str, _model.Node]) -> str:
        documentation = case.get("documentation")
        base = documentation if isinstance(documentation, str) else "undocumented"
        case_id = base
        n = 2
        while case_id in self._used:
            case_id = f"{base} ({n})"
            n += 1
        self._used.add(case_id)
        return case_id


def _object(node: _model.Node, what: str) -> Mapping[str, _model.Node]:
    if not isinstance(node, Mapping):
        raise _exceptions.CodegenError(f"Invalid endpointTests trait: {what}")
    return node


def _array(node: _model.Node, what: str) -> tuple[_model.Node, ...]:
    if not isinstance(node, tuple):
        raise _exceptions.CodegenError(f"Invalid endpointTests trait: {what}")
    return node


def _string(node: _model.Node, what: str) -> str:
    if not isinstance(node, str):
        raise _exceptions.CodegenError(f"Invalid endpointTests trait: {what}")
    return node
