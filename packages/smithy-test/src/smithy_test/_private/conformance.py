#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0
"""Conformance checks for generated model modules and clients.

:py:func:`verify_models` introspects a generated client's ``models`` module and
asserts the runtime classes it builds on demand match the model (the compact
schemas they are built from) and, optionally, the ``models.pyi`` stub that carries
their static types and the ``_params.pyi`` stub that carries their dictionary
forms. :py:func:`verify_client` asserts the client's operation methods take the
parameters the runtime accepts, and match the ``client.pyi`` stub. Type-correctness
of the stubs is NOT checked here -- that requires a type checker (pyright over a
generated usage fixture).
"""

from __future__ import annotations

import ast
import dataclasses
import datetime
import inspect
from collections.abc import Iterator, Mapping
from decimal import Decimal
from types import ModuleType
from typing import TYPE_CHECKING, Any, cast

from smithy_core._schema_compact import hydrate
from smithy_core.shapes import ShapeType
from smithy_core.traits import DefaultTrait, RequiredTrait, StreamingTrait

if TYPE_CHECKING:
    from smithy_core.schemas import APIOperation

_SHAPE_CONSTS = ("STRUCTURE", "UNION", "ENUM", "INT_ENUM")

_INPUT = "smithy.api#input"


class ConformanceError(AssertionError):
    """A generated model class does not match its schema or stub."""


def verify_models(
    models: ModuleType,
    schemas: ModuleType,
    *,
    codec: Any | None = None,
    pyi_path: str | None = None,
    params_pyi_path: str | None = None,
) -> int:
    """Verify every model shape in ``schemas`` builds and matches its surface.

    :param models: The generated ``models`` module (lazy ``__getattr__`` build).
    :param schemas: The generated ``_private.schemas`` module.
    :param codec: Optional codec with ``serialize``/``deserialize``; when given, every
        shape is round-tripped through it. Omit for request-only protocols.
    :param pyi_path: If given, the ``models.pyi`` file is AST-parsed and its class
        field surface asserted to match the runtime classes.
    :param params_pyi_path: If given, the ``_params.pyi`` file is AST-parsed and its
        TypedDicts asserted to be exactly the dictionary forms of the shapes
        reachable from operation inputs, with the keys and required keys the runtime
        accepts, and importable from ``models``.
    :returns: The number of shapes verified.
    :raises ConformanceError: On the first mismatch.
    """
    structs = _structures(schemas, models)
    for name, schema in structs.items():
        cls = getattr(models, name)
        _assert_fields_match_schema(name, cls, schema)
        if codec is not None:
            _assert_round_trips(name, cls, schema, models, codec)

    if pyi_path is not None:
        _assert_stub_matches(pyi_path, models, structs)

    if params_pyi_path is not None:
        _assert_params_stub_matches(params_pyi_path, models)

    return len(structs)


def verify_client(
    client_class: type,
    operations: Mapping[str, APIOperation[Any, Any]],
    *,
    pyi_path: str | None = None,
) -> int:
    """Verify a generated client's operation methods match their input schemas.

    Each operation method must take ``self``, then keyword-only parameters named
    and ordered like the members the runtime builds the input from, required
    exactly when the runtime requires the member, and finally ``plugins``.

    :param client_class: The generated client class.
    :param operations: Operation method name -> the operation it invokes. Must
        cover every public operation method of the class.
    :param pyi_path: If given, the ``client.pyi`` file is AST-parsed and each
        method's parameters asserted to match the runtime method's.
    :returns: The number of operations verified.
    :raises ConformanceError: On the first mismatch.
    """
    name = client_class.__name__
    methods = {
        attr
        for attr, value in vars(client_class).items()
        if not attr.startswith("_") and inspect.iscoroutinefunction(value)
    }
    if methods != set(operations):
        raise ConformanceError(
            f"{name}: operation methods {sorted(methods)} != operations given "
            f"{sorted(operations)}"
        )
    for method_name, operation in operations.items():
        _assert_method_matches_input(
            f"{name}.{method_name}", getattr(client_class, method_name), operation
        )
    if pyi_path is not None:
        _assert_client_stub_matches(pyi_path, client_class, sorted(operations))
    return len(operations)


def _assert_method_matches_input(
    name: str, method: Any, operation: APIOperation[Any, Any]
) -> None:
    params = list(inspect.signature(method).parameters.values())
    if not params or params[0].name != "self":
        raise ConformanceError(f"{name}: first parameter is not self")
    if params[-1].name != "plugins" or params[-1].default is not None:
        raise ConformanceError(f"{name}: last parameter is not plugins=None")
    members = params[1:-1]
    for param in params[1:]:
        if param.kind is not inspect.Parameter.KEYWORD_ONLY:
            raise ConformanceError(f"{name}: {param.name} is not keyword-only")
    registry = operation.model_registry
    plan = registry._struct_forms(operation.input_schema)
    expected = list(plan.converters)
    actual = [p.name for p in members]
    if actual != expected:
        raise ConformanceError(
            f"{name}: parameters {actual} != input members {expected}"
        )
    required = {p.name for p in members if p.default is inspect.Parameter.empty}
    if required != set(plan.required):
        raise ConformanceError(
            f"{name}: required parameters {sorted(required)} != required members "
            f"{sorted(plan.required)}"
        )
    for param in members:
        if param.default is not inspect.Parameter.empty and param.default is not None:
            raise ConformanceError(f"{name}: {param.name} defaults to non-None")


def _assert_client_stub_matches(
    pyi_path: str, client_class: type, operations: list[str]
) -> None:
    name = client_class.__name__
    tree = ast.parse(open(pyi_path).read())
    stub = next(
        (n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name), None
    )
    if stub is None:
        raise ConformanceError(f"{name}: class absent from client.pyi")
    defs = {
        n.name: n
        for n in stub.body
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    expected = {"__init__", *operations}
    if set(defs) != expected:
        raise ConformanceError(
            f"{name}: client.pyi methods {sorted(defs)} != {sorted(expected)}"
        )
    for method_name, node in defs.items():
        runtime = _runtime_params(getattr(client_class, method_name))
        if _stub_params(node) != runtime:
            raise ConformanceError(
                f"{name}.{method_name}: client.pyi parameters {_stub_params(node)} "
                f"!= runtime {runtime}"
            )
        is_async = isinstance(node, ast.AsyncFunctionDef)
        if is_async != inspect.iscoroutinefunction(getattr(client_class, method_name)):
            raise ConformanceError(f"{name}.{method_name}: async mismatch")


# (name, kind, has default) per parameter.
type _ParamShape = list[tuple[str, str, bool]]


def _runtime_params(method: Any) -> _ParamShape:
    return [
        (p.name, p.kind.name, p.default is not inspect.Parameter.empty)
        for p in inspect.signature(method).parameters.values()
    ]


def _stub_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> _ParamShape:
    args = node.args
    positional = [*args.posonlyargs, *args.args]
    first_default = len(positional) - len(args.defaults)
    kinds = ["POSITIONAL_ONLY"] * len(args.posonlyargs) + [
        "POSITIONAL_OR_KEYWORD"
    ] * len(args.args)
    shape = [
        (arg.arg, kind, i >= first_default)
        for i, (arg, kind) in enumerate(zip(positional, kinds, strict=True))
    ]
    shape += [
        (arg.arg, "KEYWORD_ONLY", default is not None)
        for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True)
    ]
    return shape


def _assert_params_stub_matches(pyi_path: str, models: ModuleType) -> None:
    """AST-parse _params.pyi and assert it matches the runtime dictionary forms."""
    tree = ast.parse(open(pyi_path).read())
    # TypedDict name -> (keys, required keys). Totality only matters through the
    # required keys, so an empty TypedDict matches whether or not it is total.
    typed_dicts: dict[str, tuple[list[str], set[str]]] = {}
    aliases: dict[str, list[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and any(
            isinstance(b, ast.Name) and b.id == "TypedDict" for b in node.bases
        ):
            total = not any(
                k.arg == "total"
                and isinstance(k.value, ast.Constant)
                and k.value.value is False
                for k in node.keywords
            )
            keys: list[str] = []
            required: set[str] = set()
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(
                    stmt.target, ast.Name
                ):
                    keys.append(stmt.target.id)
                    if total or _is_required_annotation(stmt.annotation):
                        required.add(stmt.target.id)
            typed_dicts[node.name] = (keys, required)
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            aliases[node.targets[0].id] = list(_union_names(node.value))

    registry = models._registry
    expected_dicts, expected_aliases = _expected_params(models, registry)
    if set(typed_dicts) != set(expected_dicts):
        raise ConformanceError(
            "_params.pyi TypedDicts differ from the shapes reachable from operation "
            f"inputs: missing {sorted(set(expected_dicts) - set(typed_dicts))}, "
            f"unexpected {sorted(set(typed_dicts) - set(expected_dicts))}"
        )
    for name, expected in expected_dicts.items():
        if typed_dicts[name] != expected:
            raise ConformanceError(
                f"{name}: _params.pyi (keys, required keys) {typed_dicts[name]} "
                f"!= runtime {expected}"
            )
    if aliases != expected_aliases:
        raise ConformanceError(
            f"_params.pyi union aliases {aliases} != runtime {expected_aliases}"
        )
    for name in [*typed_dicts, *aliases]:
        if getattr(models, name, None) is not dict:
            raise ConformanceError(f"{name}: not importable from models as dict")


def _expected_params(
    models: ModuleType, registry: Any
) -> tuple[dict[str, tuple[list[str], set[str]]], dict[str, list[str]]]:
    """Walk every operation input and build the dictionary forms it can reach."""
    from smithy_core.schemas import APIOperation

    typed_dicts: dict[str, tuple[list[str], set[str]]] = {}
    aliases: dict[str, list[str]] = {}
    seen: set[Any] = set()
    pending = [
        op.input_schema for op in vars(models).values() if isinstance(op, APIOperation)
    ]
    while pending:
        schema = pending.pop()
        if schema.id in seen:
            continue
        seen.add(schema.id)
        if schema.shape_type == ShapeType.STRUCTURE:
            plan = registry._struct_forms(schema)
            name = registry.params_name(plan.name)
            typed_dicts[name] = (list(plan.converters), set(plan.required))
            members = [
                m for m in schema.members_by_index if not _is_event_stream_member(m)
            ]
        else:
            variants = registry._union_forms(schema)
            names: list[str] = []
            for key, (variant, _) in variants.items():
                variant_name = registry.params_name(variant.__name__)
                typed_dicts[variant_name] = ([key], {key})
                names.append(variant_name)
            aliases[registry.params_name(registry._target_name(schema))] = names
            members = list(schema.members_by_index)
        for member in members:
            pending.extend(_reachable_targets(member))
    return typed_dicts, aliases


def _reachable_targets(member: Any) -> Iterator[Any]:
    if member.shape_type in (ShapeType.STRUCTURE, ShapeType.UNION):
        yield member.expect_member_target()
    elif member.shape_type == ShapeType.LIST:
        yield from _reachable_targets(member.expect_member_target().members_by_index[0])
    elif member.shape_type == ShapeType.MAP:
        yield from _reachable_targets(member.expect_member_target().members["value"])


def _is_required_annotation(annotation: ast.expr) -> bool:
    return (
        isinstance(annotation, ast.Subscript)
        and isinstance(annotation.value, ast.Name)
        and annotation.value.id == "Required"
    )


def _union_names(node: ast.expr) -> Iterator[str]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        yield from _union_names(node.left)
        yield from _union_names(node.right)
    elif isinstance(node, ast.Name):
        yield node.id


def _structures(schemas: ModuleType, models: ModuleType) -> dict[str, Any]:
    # A shape's generated symbol name usually equals its schema id name, but a
    # rename (two shapes sharing an id name in different namespaces) makes them
    # differ. The registry's rename map (symbol -> schema constant) is the
    # authoritative symbol<->schema pairing, so key each schema by the symbol
    # the client actually exposes rather than the ambiguous id name.
    const_to_symbol: dict[str, str] = {}
    registry = getattr(models, "_registry", None)
    if registry is not None:
        for symbol, const in getattr(registry, "_renames", {}).items():
            const_to_symbol[const] = symbol
    out: dict[str, Any] = {}
    for const in dir(schemas):
        if not (const.replace("_", "").isupper() and const[:1].isalpha()):
            continue
        tup = getattr(schemas, const)
        if not isinstance(tup, tuple):
            continue
        schema = hydrate(cast("tuple[Any, ...]", tup))
        if schema.shape_type == ShapeType.STRUCTURE:
            out[const_to_symbol.get(const, schema.id.name)] = schema
    return out


def _assert_fields_match_schema(name: str, cls: type, schema: Any) -> None:
    if not dataclasses.is_dataclass(cls):
        raise ConformanceError(f"{name}: built class is not a dataclass")
    field_names = {f.name for f in dataclasses.fields(cls)}
    for member in schema.members_by_index:
        if _is_event_stream_member(member):
            continue
        # a runtime field must exist for every modeled member (name derived by the
        # same ported namer the registry uses)
        from smithy_core._model_naming import member_field_name

        is_error = _is_error(schema)
        fname = member_field_name(
            member.expect_member_name(),
            is_error=is_error,
            carries_response_metadata=is_error or _is_output(schema),
            is_enum=False,
            is_operation_input=_is_input(schema),
        )
        if fname not in field_names:
            raise ConformanceError(
                f"{name}: schema member {member.expect_member_name()!r} -> field "
                f"{fname!r} missing from built class {sorted(field_names)}"
            )


def _assert_round_trips(
    name: str, cls: type, schema: Any, models: ModuleType, codec: Any
) -> None:
    instance = _build_instance(cls, schema, models)
    body = codec.serialize(instance)
    rebuilt = codec.deserialize(body, cls)
    reserialized = codec.serialize(rebuilt)
    if body != reserialized:
        raise ConformanceError(
            f"{name}: round-trip mismatch\n  first: {body!r}\n  again: {reserialized!r}"
        )


def _build_instance(cls: type, schema: Any, models: ModuleType) -> Any:
    """Construct an instance filling required members with trivial values."""
    from smithy_core._model_naming import member_field_name

    kwargs: dict[str, Any] = {}
    is_error = _is_error(schema)
    for member in schema.members_by_index:
        if _is_event_stream_member(member):
            continue
        required = member.get_trait(RequiredTrait) is not None
        has_default = member.get_trait(DefaultTrait) is not None
        if not required or has_default or _is_input(schema):
            continue
        fname = member_field_name(
            member.expect_member_name(),
            is_error=is_error,
            carries_response_metadata=is_error or _is_output(schema),
            is_enum=False,
            is_operation_input=False,
        )
        kwargs[fname] = _trivial_value(member, models)
    return cls(**kwargs)


def _trivial_value(member: Any, models: ModuleType) -> Any:
    st = member.shape_type
    simple: dict[ShapeType, Any] = {
        ShapeType.STRING: "x",
        ShapeType.BOOLEAN: False,
        ShapeType.TIMESTAMP: datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
        ShapeType.BLOB: b"x",
        ShapeType.BYTE: 1,
        ShapeType.SHORT: 1,
        ShapeType.INTEGER: 1,
        ShapeType.LONG: 1,
        ShapeType.FLOAT: 1.0,
        ShapeType.DOUBLE: 1.0,
        ShapeType.BIG_INTEGER: 1,
        ShapeType.BIG_DECIMAL: Decimal(1),
        ShapeType.LIST: [],
        ShapeType.MAP: {},
    }
    if st in simple:
        return simple[st]
    if st == ShapeType.ENUM:
        return next(iter(member.expect_member_target().members))
    if st == ShapeType.INT_ENUM:
        return 1
    if st == ShapeType.STRUCTURE:
        target = member.expect_member_target()
        nested = getattr(models, target.id.name)
        return _build_instance(nested, target, models)
    if st == ShapeType.UNION:
        target = member.expect_member_target()
        first = target.members_by_index[0]
        variant = getattr(models, target.id.name + first.expect_member_name())
        return variant(value=_trivial_value(first, models))
    return None


def _assert_stub_matches(
    pyi_path: str, models: ModuleType, structs: dict[str, Any]
) -> None:
    """AST-parse models.pyi and assert its class field surface matches runtime."""
    tree = ast.parse(open(pyi_path).read())
    stub_fields: dict[str, set[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            stub_fields[node.name] = {
                stmt.target.id
                for stmt in node.body
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
            }
    for name in structs:
        if name not in stub_fields:
            raise ConformanceError(
                f"{name}: declared in schema but absent from models.pyi"
            )
        cls = getattr(models, name)
        runtime = {f.name for f in dataclasses.fields(cls)}
        inherited: set[str] = set()
        for base in cls.__mro__[1:]:
            if dataclasses.is_dataclass(base):
                inherited |= {f.name for f in dataclasses.fields(base)}
        # The stub declares locally-defined fields plus response_metadata (which the
        # runtime inherits on errors but declares on outputs). Normalize both sides to
        # "local fields, with response_metadata counted if present at runtime".
        local_runtime = (runtime - inherited) | (runtime & {"response_metadata"})
        if stub_fields[name] != local_runtime:
            raise ConformanceError(
                f"{name}: models.pyi fields {sorted(stub_fields[name])} != "
                f"runtime local fields {sorted(local_runtime)}"
            )


def _is_error(schema: Any) -> bool:
    from smithy_core.traits import ErrorTrait

    return schema.get_trait(ErrorTrait) is not None


def _is_output(schema: Any) -> bool:
    from smithy_core.shapes import ShapeID

    return schema.get_trait(ShapeID("smithy.api#output")) is not None


def _is_input(schema: Any) -> bool:
    from smithy_core.shapes import ShapeID

    return schema.get_trait(ShapeID("smithy.api#input")) is not None


def _is_event_stream_member(member: Any) -> bool:
    target = member.expect_member_target()
    return (
        target.shape_type is ShapeType.UNION
        and target.get_trait(StreamingTrait) is not None
    )
